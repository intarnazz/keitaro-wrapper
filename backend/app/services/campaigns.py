import re
import secrets

from app.keitaro.client import KeitaroClient, KeitaroError
from app.schemas import CampaignCreate, CampaignCreated

# Значения Keitaro для потоков. Сверить с GET /stream_filters и GET /streams_actions.
GEO_FILTER_NAME = "country"
REDIRECT_ACTION_TYPE = "http"
REDIRECT_URL = "https://www.google.com"


class DefaultNotFound(Exception):
    """В Keitaro нет значения по умолчанию (домена, группы или источника)."""


def pick_first(items: list[dict], what: str, param: str) -> int:
    """Первый активный элемент справочника (если у элементов есть state), иначе первый."""
    if not items:
        raise DefaultNotFound(f"В Keitaro нет ни одного значения для {what}, передайте {param}")
    active = [i for i in items if i.get("state", "active") == "active"]
    return (active or items)[0]["id"]


def make_alias(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "campaign"
    return f"{slug[:40]}-{secrets.token_hex(3)}"


def geo_stream_payload(campaign_id: int, geo: str) -> dict:
    """Поток 1: все из страны geo уходят на Google."""
    return {
        "campaign_id": campaign_id,
        "name": f"Geo {geo} -> Google",
        "type": "regular",
        "position": 1,
        "schema": "redirect",
        "action_type": REDIRECT_ACTION_TYPE,
        "action_payload": REDIRECT_URL,
        "state": "active",
        "filters": [{"name": GEO_FILTER_NAME, "mode": "accept", "payload": [geo]}],
    }


def offer_stream_payload(campaign_id: int, offer_id: int) -> dict:
    """Поток 2: все остальные (без фильтров) уходят на оффер."""
    return {
        "campaign_id": campaign_id,
        "name": "Offer",
        "type": "regular",
        "position": 2,
        "schema": "landings",
        # action_type обязателен для любого потока, даже когда трафик идёт на офферы
        "action_type": REDIRECT_ACTION_TYPE,
        "state": "active",
        "offers": [{"offer_id": offer_id, "share": 100, "state": "active"}],
    }


def create_campaign_with_streams(k: KeitaroClient, data: CampaignCreate) -> CampaignCreated:
    # Значения по умолчанию берём из Keitaro до создания кампании: если их нет, ничего не создаём.
    domain_id = data.domain_id or pick_first(k.domains(), "домена", "domain_id")
    group_id = data.group_id or pick_first(k.groups(), "группы", "group_id")
    traffic_source_id = data.traffic_source_id or pick_first(
        k.traffic_sources(), "источника трафика", "traffic_source_id"
    )

    campaign = k.create_campaign(
        {
            "name": data.name,
            "alias": data.alias or make_alias(data.name),
            "domain_id": domain_id,
            "group_id": group_id,
            "traffic_source_id": traffic_source_id,
        }
    )
    campaign_id = campaign["id"]

    try:
        s1 = k.create_stream(geo_stream_payload(campaign_id, data.geo))
        s2 = k.create_stream(offer_stream_payload(campaign_id, data.offer_id))
    except KeitaroError:
        # Откат: без потоков кампания бесполезна. Сбой отката не должен скрыть исходную ошибку.
        # Keitaro требует уникальное имя и среди архивных, поэтому перед архивацией освобождаем имя.
        try:
            k.update_campaign(campaign_id, {"name": f"{data.name} (rollback {secrets.token_hex(3)})"})
        except KeitaroError:
            pass
        try:
            k.delete_campaign(campaign_id)
        except KeitaroError:
            pass
        raise

    return CampaignCreated(
        campaign_id=campaign_id,
        alias=campaign["alias"],
        domain_id=domain_id,
        group_id=group_id,
        traffic_source_id=traffic_source_id,
        streams=[s1["id"], s2["id"]],
    )
