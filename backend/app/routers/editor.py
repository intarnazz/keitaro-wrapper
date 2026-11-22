from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_keitaro
from app.keitaro.client import KeitaroClient
from app.schemas import AddOfferBody, ApiResponse, CampaignInfo, OfferInfo, PinBody, StreamView
from app.services import editor
from app.services.offers import search_offers

router = APIRouter(prefix="/api", tags=["editor"])


def _streams(items) -> list[StreamView]:
    return [editor.stream_view(s) for s in items]


# ---------- кампании (чтение из Keitaro) ----------

@router.get("/campaigns", response_model=ApiResponse[list[CampaignInfo]])
def list_campaigns(k: KeitaroClient = Depends(get_keitaro)):
    result: list[CampaignInfo] = []
    page = 100
    for i in range(50):  # защита от бесконечного цикла: не больше 5000 кампаний
        chunk: list[dict[str, Any]] = k.campaigns(limit=page, offset=i * page)
        result += [CampaignInfo.from_keitaro(c) for c in chunk]
        if len(chunk) < page:
            break
    return ApiResponse(data=result)


@router.get("/campaigns/{campaign_id}", response_model=ApiResponse[CampaignInfo])
def get_campaign(campaign_id: int, k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=CampaignInfo.from_keitaro(k.campaign(campaign_id)))


# ---------- потоки ----------

@router.get("/campaigns/{campaign_id}/streams", response_model=ApiResponse[list[StreamView]])
def campaign_streams(campaign_id: int, db: Session = Depends(get_db)):
    """Локальное состояние (с черновиками). В Keitaro не ходит."""
    return ApiResponse(data=_streams(editor.list_streams(db, campaign_id)))


@router.post("/campaigns/{campaign_id}/fetch", response_model=ApiResponse[list[StreamView]])
def fetch_streams(campaign_id: int, db: Session = Depends(get_db), k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=_streams(editor.fetch_campaign(db, k, campaign_id)))


# ---------- офферы ----------

@router.get("/offers", response_model=ApiResponse[list[OfferInfo]])
def offers(q: str = "", limit: int = Query(20, ge=1, le=100), k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=search_offers(k, q, limit))


@router.post("/streams/{stream_id}/offers", response_model=ApiResponse[StreamView])
def add_offer(stream_id: int, body: AddOfferBody, db: Session = Depends(get_db),
              k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=editor.stream_view(editor.add_offer(db, k, stream_id, body.offer_id)))


@router.post("/streams/{stream_id}/offers/{offer_id}/remove", response_model=ApiResponse[StreamView])
def remove_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=editor.stream_view(editor.remove_offer(db, stream_id, offer_id)))


@router.post("/streams/{stream_id}/offers/{offer_id}/restore", response_model=ApiResponse[StreamView])
def restore_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=editor.stream_view(editor.restore_offer(db, stream_id, offer_id)))


@router.put("/streams/{stream_id}/offers/{offer_id}/pin", response_model=ApiResponse[StreamView])
def pin_offer(stream_id: int, offer_id: int, body: PinBody, db: Session = Depends(get_db)):
    return ApiResponse(data=editor.stream_view(editor.set_pin(db, stream_id, offer_id, body.pinned, body.share)))


@router.post("/streams/{stream_id}/push", response_model=ApiResponse[StreamView])
def push_stream(stream_id: int, db: Session = Depends(get_db), k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=editor.stream_view(editor.push(db, k, stream_id)))


@router.post("/streams/{stream_id}/cancel", response_model=ApiResponse[StreamView])
def cancel_stream(stream_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=editor.stream_view(editor.cancel(db, stream_id)))
