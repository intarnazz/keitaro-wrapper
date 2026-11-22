from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import EditorError
from app.keitaro.client import KeitaroClient
from app.models import Stream, StreamOffer
from app.schemas import OfferView, StreamView
from app.services.distribute import DistributionError, distribute

# ---------- представление ----------


def stream_view(stream: Stream) -> StreamView:
    # активные сверху, удалённые (архив) снизу; внутри групп порядок добавления
    ordered = sorted(stream.offers, key=lambda o: (o.status != "active", o.id or 0))
    return StreamView(
        id=stream.id,
        keitaro_stream_id=stream.keitaro_stream_id,
        campaign_id=stream.campaign_id,
        name=stream.name,
        position=stream.position,
        is_editable=bool(stream.offers),
        dirty=stream.dirty,
        total_share=sum(o.share for o in stream.offers if o.status == "active"),
        offers=[
            OfferView(offer_id=o.offer_id, name=o.offer_name, status=o.status, share=o.share,  # type: ignore[arg-type]
                      pinned=o.pinned, is_new=o.is_new, changed=o.changed)
            for o in ordered
        ],
    )


# ---------- чтение ----------


def list_streams(db: Session, campaign_id: int) -> list[Stream]:
    q = select(Stream).where(Stream.campaign_id == campaign_id).order_by(Stream.position, Stream.id)
    return list(db.scalars(q))


def get_stream(db: Session, stream_id: int) -> Stream:
    stream = db.get(Stream, stream_id)
    if stream is None:
        raise EditorError(404, "Поток не найден. Сначала выполните Fetch streams")
    return stream


def _get_row(stream: Stream, offer_id: int) -> StreamOffer:
    for o in stream.offers:
        if o.offer_id == offer_id:
            return o
    raise EditorError(404, f"Оффер {offer_id} не найден в потоке")


def _require_editable(stream: Stream) -> None:
    if not stream.offers:
        raise EditorError(409, "В этом потоке нет офферов, редактировать его нельзя")


def _recalc(db: Session, stream: Stream) -> None:
    """Пересчёт долей. Если не получилось, все изменения запроса откатываются."""
    try:
        distribute(stream.offers)
    except DistributionError as e:
        db.rollback()
        raise EditorError(422, str(e)) from e


# ---------- Fetch streams ----------


def fetch_campaign(db: Session, k: KeitaroClient, campaign_id: int) -> list[Stream]:
    """Подтягивает потоки кампании из Keitaro и сводит их с локальным состоянием."""
    keitaro_streams = [s for s in k.campaign_streams(campaign_id) if s.get("state") != "deleted"]
    names = {o["id"]: o.get("name") or "" for o in k.offers()}

    local = {s.keitaro_stream_id: s for s in list_streams(db, campaign_id)}
    seen: set[int] = set()

    for ks in keitaro_streams:
        seen.add(ks["id"])
        stream = local.get(ks["id"])
        if stream is None:
            stream = Stream(campaign_id=campaign_id, keitaro_stream_id=ks["id"], name="")
            db.add(stream)
        stream.name = ks.get("name") or f"Stream {ks['id']}"
        stream.position = ks.get("position") or 0
        _merge_offers(stream, ks.get("offers") or [], names)

    for keitaro_id, stream in local.items():  # поток удалили в Keitaro
        if keitaro_id not in seen:
            db.delete(stream)

    db.commit()
    return list_streams(db, campaign_id)


def _merge_offers(stream: Stream, keitaro_offers: list[dict], names: dict[int, str]) -> None:
    present = {
        int(o["offer_id"]): int(o.get("share") or 0)
        for o in keitaro_offers
        if (o.get("state") or "active") == "active"
    }
    rows = {o.offer_id: o for o in stream.offers}

    for offer_id, share in present.items():
        row = rows.get(offer_id)
        if row is None:
            stream.offers.append(
                StreamOffer(offer_id=offer_id, offer_name=names.get(offer_id, ""), status="active",
                            share=share, base_status="active", base_share=share)
            )
            continue
        was_clean = not row.changed
        row.base_status, row.base_share = "active", share
        if was_clean:  # чужих черновых правок нет, берём данные Keitaro
            row.status, row.share = "active", share

    for offer_id, row in rows.items():
        if offer_id in present:
            row.offer_name = names.get(offer_id) or row.offer_name
            continue
        if row.base_status != "active":
            # добавлен в черновике или уже был удалён: черновик не трогаем
            continue
        # Оффер был в Keitaro, а теперь его нет: как будто удалён вручную
        row.status, row.share, row.pinned = "removed", 0, False
        row.base_status, row.base_share = "removed", 0

    for row in stream.offers:
        row.offer_name = names.get(row.offer_id) or row.offer_name or f"Offer {row.offer_id}"

    # Черновик пережил Fetch, но состав изменился: пробуем вернуть сумму 100%.
    # Если нельзя (например, всё закреплено), оставляем как есть: интерфейс покажет сумму красным.
    active = [o for o in stream.offers if o.status == "active"]
    if stream.dirty and active and sum(o.share for o in active) != 100:
        try:
            distribute(stream.offers)
        except DistributionError:
            pass


# ---------- правки черновика ----------


def add_offer(db: Session, k: KeitaroClient, stream_id: int, offer_id: int) -> Stream:
    stream = get_stream(db, stream_id)
    _require_editable(stream)

    row = next((o for o in stream.offers if o.offer_id == offer_id), None)
    if row is not None:
        if row.status == "active":
            raise EditorError(409, f"Оффер {offer_id} уже в потоке")
        row.status = "active"  # был в архиве: то же, что Bring back
    else:
        info = k.offer(offer_id)  # ошибку «нет такого оффера» отдаёт Keitaro
        stream.offers.append(
            StreamOffer(offer_id=offer_id, offer_name=info.get("name") or f"Offer {offer_id}",
                        status="active", share=0)
        )
        db.flush()
    _recalc(db, stream)
    db.commit()
    return stream


def remove_offer(db: Session, stream_id: int, offer_id: int) -> Stream:
    stream = get_stream(db, stream_id)
    row = _get_row(stream, offer_id)
    if row.status == "removed":
        raise EditorError(409, f"Оффер {offer_id} уже удалён")
    if row.is_new:  # в Keitaro его не было, архивировать нечего
        stream.offers.remove(row)
    else:
        row.status, row.share, row.pinned = "removed", 0, False
    _recalc(db, stream)
    db.commit()
    return stream


def restore_offer(db: Session, stream_id: int, offer_id: int) -> Stream:
    stream = get_stream(db, stream_id)
    row = _get_row(stream, offer_id)
    if row.status == "active":
        raise EditorError(409, f"Оффер {offer_id} уже активен")
    row.status = "active"
    _recalc(db, stream)
    db.commit()
    return stream


def set_pin(db: Session, stream_id: int, offer_id: int, pinned: bool, share: int | None) -> Stream:
    stream = get_stream(db, stream_id)
    row = _get_row(stream, offer_id)
    if row.status != "active":
        raise EditorError(409, "Закрепить можно только активный оффер")
    row.pinned = pinned
    if pinned and share is not None:
        row.share = share
    _recalc(db, stream)
    db.commit()
    return stream


# ---------- Push / Cancel ----------


def push(db: Session, k: KeitaroClient, stream_id: int) -> Stream:
    stream = get_stream(db, stream_id)
    if not stream.dirty:
        return stream

    active = [o for o in stream.offers if o.status == "active"]
    if not active:
        raise EditorError(422, "Нельзя опубликовать поток без активных офферов")
    total = sum(o.share for o in active)
    if total != 100:
        raise EditorError(422, f"Сумма долей {total}%, а должна быть 100%")

    k.update_stream(
        stream.keitaro_stream_id,
        {"offers": [{"offer_id": o.offer_id, "share": o.share, "state": "active"} for o in active]},
    )
    for o in stream.offers:
        o.base_status, o.base_share = o.status, o.share
    db.commit()
    return stream


def cancel(db: Session, stream_id: int) -> Stream:
    stream = get_stream(db, stream_id)
    for o in list(stream.offers):
        if o.is_new:
            stream.offers.remove(o)
        else:
            o.status = o.base_status or "removed"
            o.share = o.base_share or 0
    db.commit()
    return stream
