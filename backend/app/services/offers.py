import time

from app.keitaro.client import KeitaroClient
from app.schemas import OfferInfo

_TTL = 60.0
_cache: dict[str, tuple[float, list[dict]]] = {}


def clear_cache() -> None:
    _cache.clear()


def _all_offers(k: KeitaroClient) -> list[dict]:
    """Список офферов Keitaro целиком (поиска в API нет), кэшируется на минуту."""
    key = f"{id(k)}"
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < _TTL:
        return hit[1]
    offers = k.offers()
    _cache[key] = (time.monotonic(), offers)
    return offers


def search_offers(k: KeitaroClient, q: str = "", limit: int = 20) -> list[OfferInfo]:
    q = q.strip().lower()
    result: list[OfferInfo] = []
    for o in _all_offers(k):
        if (o.get("state") or "active") != "active":
            continue
        if q and q != str(o["id"]) and q not in (o.get("name") or "").lower():
            continue
        result.append(OfferInfo(id=o["id"], name=o.get("name") or "", state=o.get("state") or ""))
        if len(result) >= limit:
            break
    return result
