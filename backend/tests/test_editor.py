"""Сценарии из видео, на уровне сервиса."""

import pytest

from app.errors import EditorError
from app.services import editor
from tests.conftest import DEMO_CAMPAIGN


def fetch(db, keitaro):
    return editor.fetch_campaign(db, keitaro, DEMO_CAMPAIGN)


def offers_stream(db, keitaro):
    return next(s for s in fetch(db, keitaro) if s.offers)


def view(stream):
    return {o.offer_id: (o.status, o.share, o.pinned) for o in stream.offers}


def test_fetch_creates_all_streams_and_ignores_content_of_offerless(db, keitaro):
    streams = fetch(db, keitaro)
    assert [s.name for s in streams] == ["Australia -> Google", "Offers", "Fallback"]
    assert [bool(s.offers) for s in streams] == [False, True, False]
    assert not any(s.dirty for s in streams)
    assert {o.offer_id: o.share for o in streams[1].offers} == {1: 34, 2: 33, 3: 33}
    assert streams[1].offers[0].offer_name == "Casino Alpha"


def test_fetch_is_idempotent(db, keitaro):
    fetch(db, keitaro)
    streams = fetch(db, keitaro)
    assert len(streams) == 3 and not any(s.dirty for s in streams)


def test_add_offer_recalculates_and_marks_dirty(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)
    assert view(stream) == {1: ("active", 25, False), 2: ("active", 25, False),
                            3: ("active", 25, False), 4: ("active", 25, False)}
    assert stream.dirty
    # в Keitaro пока без изменений
    assert len(keitaro.streams_data[5002]["offers"]) == 3


def test_push_publishes_to_keitaro_and_cleans_dirty(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)
    editor.push(db, keitaro, stream.id)
    assert not stream.dirty
    assert {o["offer_id"]: o["share"] for o in keitaro.streams_data[5002]["offers"]} == {1: 25, 2: 25, 3: 25, 4: 25}


def test_cancel_drops_added_offers_and_restores_shares(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)
    editor.cancel(db, stream.id)
    assert view(stream) == {1: ("active", 34, False), 2: ("active", 33, False), 3: ("active", 33, False)}
    assert not stream.dirty


def test_remove_greys_offer_sets_zero_and_publishes(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.remove_offer(db, stream.id, 3)
    assert view(stream)[3] == ("removed", 0, False)
    assert stream.dirty
    editor.push(db, keitaro, stream.id)
    assert [o["offer_id"] for o in keitaro.streams_data[5002]["offers"]] == [1, 2]
    # остался в архиве у нас
    assert view(stream)[3] == ("removed", 0, False) and not stream.dirty


def test_bring_back_after_remove(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.remove_offer(db, stream.id, 3)
    editor.push(db, keitaro, stream.id)
    editor.restore_offer(db, stream.id, 3)
    assert stream.dirty
    editor.push(db, keitaro, stream.id)
    assert {o["offer_id"] for o in keitaro.streams_data[5002]["offers"]} == {1, 2, 3}


def test_cancel_undoes_remove(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.remove_offer(db, stream.id, 3)
    editor.cancel(db, stream.id)
    assert view(stream)[3] == ("active", 33, False) and not stream.dirty


def test_removing_draft_added_offer_forgets_it(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)
    editor.remove_offer(db, stream.id, 4)
    assert 4 not in view(stream)
    assert not stream.dirty


def test_offer_deleted_in_keitaro_becomes_removed_on_next_fetch(db, keitaro):
    stream = offers_stream(db, keitaro)
    keitaro.streams_data[5002]["offers"] = [o for o in keitaro.streams_data[5002]["offers"]
                                           if o["offer_id"] != 2]
    stream = offers_stream(db, keitaro)
    assert view(stream)[2] == ("removed", 0, False)
    assert not stream.dirty
    editor.restore_offer(db, stream.id, 2)  # Bring back работает
    assert stream.dirty


def test_pin_survives_later_operations(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)            # 25/25/25/25
    editor.set_pin(db, stream.id, 1, True, None)           # закрепили 25
    editor.remove_offer(db, stream.id, 2)
    assert view(stream)[1] == ("active", 25, True)
    assert sorted(o.share for o in stream.offers if o.status == "active") == [25, 37, 38]
    editor.restore_offer(db, stream.id, 2)
    assert view(stream)[1] == ("active", 25, True)
    assert sum(o.share for o in stream.offers if o.status == "active") == 100


def test_pin_with_explicit_share(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.set_pin(db, stream.id, 1, True, 50)
    assert view(stream) == {1: ("active", 50, True), 2: ("active", 25, False), 3: ("active", 25, False)}


def test_fetch_keeps_draft_but_updates_base(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)
    stream = offers_stream(db, keitaro)  # повторный Fetch не теряет черновик
    assert 4 in view(stream) and stream.dirty


def test_errors(db, keitaro):
    stream = offers_stream(db, keitaro)
    with pytest.raises(EditorError) as e:
        editor.add_offer(db, keitaro, stream.id, 1)         # уже в потоке
    assert e.value.status == 409
    with pytest.raises(EditorError) as e:
        editor.set_pin(db, stream.id, 1, True, 100)         # 100% закреплено, остальным ничего
    assert e.value.status == 422
    assert view(stream)[1] == ("active", 34, False)         # откат
    streams = fetch(db, keitaro)
    with pytest.raises(EditorError) as e:
        editor.add_offer(db, keitaro, streams[0].id, 5)     # поток без офферов
    assert e.value.status == 409


def test_push_requires_active_offers(db, keitaro):
    stream = offers_stream(db, keitaro)
    for oid in (1, 2, 3):
        editor.remove_offer(db, stream.id, oid)
    with pytest.raises(EditorError) as e:
        editor.push(db, keitaro, stream.id)
    assert e.value.status == 422


def test_fetch_keeps_restored_offer_that_keitaro_does_not_have(db, keitaro):
    """Регрессия: оффер, удалённый и опубликованный, затем возвращённый в черновике, переживает Fetch."""
    stream = offers_stream(db, keitaro)
    editor.remove_offer(db, stream.id, 2)
    editor.push(db, keitaro, stream.id)
    editor.restore_offer(db, stream.id, 2)
    stream = offers_stream(db, keitaro)  # Fetch
    assert view(stream)[2][0] == "active"
    assert sum(o.share for o in stream.offers if o.status == "active") == 100
    assert stream.dirty


def test_fetch_rebalances_draft_when_keitaro_lost_an_offer(db, keitaro):
    stream = offers_stream(db, keitaro)
    editor.add_offer(db, keitaro, stream.id, 4)  # черновик 25/25/25/25
    keitaro.streams_data[5002]["offers"] = [o for o in keitaro.streams_data[5002]["offers"] if o["offer_id"] != 2]
    stream = offers_stream(db, keitaro)
    assert view(stream)[2][0] == "removed"
    assert sum(o.share for o in stream.offers if o.status == "active") == 100
