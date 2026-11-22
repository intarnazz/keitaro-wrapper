"""Фейковый Keitaro в памяти для разработки и тестов.

Подменяет только транспорт (`_request`), поэтому все методы KeitaroClient
(пути, тела запросов, разбор ответов) работают так же, как с настоящим сервером.
Включается переменной окружения KEITARO_FAKE=true. Данные живут, пока запущен процесс.

Имитирует ошибки Keitaro, которые мы уже видели: уникальность имени кампании
(в том числе среди архивных) и обязательность полей потока.
"""

import copy
import json
import re
from typing import Any

from app.keitaro.client import KeitaroClient, KeitaroError

STREAM_REQUIRED = ("campaign_id", "schema", "type", "name", "action_type")


def _err(status: int, body: Any) -> KeitaroError:
    return KeitaroError(status, body if isinstance(body, str) else json.dumps(body))


class FakeKeitaro(KeitaroClient):
    def __init__(self) -> None:  # без httpx-клиента
        self._seed()

    # ---------- начальные данные ----------

    def _seed(self) -> None:
        self.domains_data = [
            {"id": 1, "name": "track.example.com", "state": "active"},
            {"id": 2, "name": "old.example.com", "state": "deleted"},
        ]
        self.groups_data = [
            {"id": 1, "name": "Default", "type": "campaigns", "position": 1},
            {"id": 2, "name": "Tests", "type": "campaigns", "position": 2},
        ]
        self.sources_data = [
            {"id": 1, "name": "Facebook", "state": "active"},
            {"id": 2, "name": "Google Ads", "state": "active"},
        ]
        names = [
            "Casino Alpha", "Crypto Beta", "Dating Gamma", "Nutra Delta", "Sweeps Epsilon",
            "Loans Zeta", "VPN Eta", "Gaming Theta", "Finance Iota", "Pets Kappa",
            "Travel Lambda", "Education Mu",
        ]
        self.offers_data = [{"id": i + 1, "name": n, "state": "active"} for i, n in enumerate(names)]
        self.campaigns_data: dict[int, dict] = {}
        self.streams_data: dict[int, dict] = {}
        self._next_campaign = 1001
        self._next_stream = 5001
        self._next_offer_stream = 9001

        # Демо-кампания как в видео: поток по стране -> Google, поток с офферами, поток без офферов
        demo = self._new_campaign({"name": "Demo AU", "alias": "demo-au", "domain_id": 1, "group_id": 1,
                                   "traffic_source_id": 1})
        self._new_stream({"campaign_id": demo["id"], "name": "Australia -> Google", "type": "regular",
                          "position": 1, "schema": "redirect", "action_type": "http",
                          "action_payload": "https://www.google.com",
                          "filters": [{"name": "country", "mode": "accept", "payload": ["AU"]}]})
        self._new_stream({"campaign_id": demo["id"], "name": "Offers", "type": "regular", "position": 2,
                          "schema": "landings", "action_type": "http",
                          "offers": [{"offer_id": 1, "share": 34}, {"offer_id": 2, "share": 33},
                                     {"offer_id": 3, "share": 33}]})
        self._new_stream({"campaign_id": demo["id"], "name": "Fallback", "type": "default", "position": 3,
                          "schema": "redirect", "action_type": "http", "action_payload": "https://example.org"})

    # ---------- хелперы ----------

    def _new_campaign(self, p: dict) -> dict:
        c = {
            "id": self._next_campaign, "alias": p["alias"], "name": p["name"], "type": "position",
            "state": "active", "group_id": p.get("group_id") or 0, "domain_id": p.get("domain_id"),
            "traffic_source_id": p.get("traffic_source_id") or 0,
        }
        self._next_campaign += 1
        self.campaigns_data[c["id"]] = c
        return c

    def _new_stream(self, p: dict) -> dict:
        s = {
            "id": self._next_stream, "campaign_id": p["campaign_id"], "name": p["name"],
            "type": p["type"], "position": p.get("position", 1), "schema": p["schema"],
            "action_type": p["action_type"], "action_payload": p.get("action_payload", ""),
            "state": p.get("state", "active"), "filters": p.get("filters", []), "offers": [],
        }
        self._next_stream += 1
        self._set_offers(s, p.get("offers", []))
        self.streams_data[s["id"]] = s
        return s

    def _set_offers(self, stream: dict, offers: list[dict]) -> None:
        known = {o["id"] for o in self.offers_data}
        result = []
        for o in offers:
            if o["offer_id"] not in known:
                raise _err(422, {"offers": [f"Offer {o['offer_id']} not found"]})
            result.append({
                "id": self._next_offer_stream, "stream_id": stream["id"], "offer_id": o["offer_id"],
                "state": o.get("state", "active"), "share": int(o.get("share", 0)),
            })
            self._next_offer_stream += 1
        stream["offers"] = result

    def _campaign(self, cid: int, include_deleted: bool = False) -> dict:
        c = self.campaigns_data.get(cid)
        if c is None or (c["state"] == "deleted" and not include_deleted):
            raise _err(404, {"error": "Not found"})
        return c

    # ---------- транспорт ----------

    def _request(self, method: str, path: str, **kwargs: Any):
        params = kwargs.get("params") or {}
        body = copy.deepcopy(kwargs.get("json"))
        out = self._route(method, path, params, body)
        return copy.deepcopy(out)

    def _route(self, method: str, path: str, params: dict, body: Any):
        m = (method, path)
        if m == ("GET", "/domains"):
            return self.domains_data
        if m == ("GET", "/groups"):
            return [g for g in self.groups_data if g["type"] == params.get("type", "campaigns")]
        if m == ("GET", "/traffic_sources"):
            return self.sources_data
        if m == ("GET", "/offers"):
            return self.offers_data
        if x := re.fullmatch(r"/offers/(\d+)", path):
            if method == "GET":
                for o in self.offers_data:
                    if o["id"] == int(x[1]):
                        return o
                raise _err(404, {"error": "Offer not found"})

        if m == ("GET", "/campaigns"):
            items = [c for c in self.campaigns_data.values() if c["state"] != "deleted"]
            offset, limit = int(params.get("offset", 0)), int(params.get("limit", 100))
            return items[offset: offset + limit]
        if m == ("POST", "/campaigns"):
            errors: dict[str, list[str]] = {}
            for field in ("name", "alias"):
                if not (body or {}).get(field):
                    errors[field] = [f"{field.capitalize()} is required"]
            if errors:
                raise _err(422, errors)
            if any(c["name"] == body["name"] for c in self.campaigns_data.values()):
                where = "in the archive" if any(
                    c["name"] == body["name"] and c["state"] == "deleted" for c in self.campaigns_data.values()
                ) else ""
                raise _err(422, {"name": [f"Name has already been used {where}".strip()]})
            return self._new_campaign(body)
        if x := re.fullmatch(r"/campaigns/(\d+)", path):
            cid = int(x[1])
            if method == "GET":
                return self._campaign(cid)
            if method == "PUT":
                c = self._campaign(cid, include_deleted=True)
                c.update({k: v for k, v in (body or {}).items() if k in ("name", "alias", "group_id", "domain_id",
                                                                        "traffic_source_id")})
                return c
            if method == "DELETE":
                self._campaign(cid)["state"] = "deleted"  # как у Keitaro: в архив
                return None
        if (x := re.fullmatch(r"/campaigns/(\d+)/streams", path)) and method == "GET":
            cid = int(x[1])
            self._campaign(cid)
            items = [s for s in self.streams_data.values() if s["campaign_id"] == cid and s["state"] != "deleted"]
            return sorted(items, key=lambda s: s["position"])

        if m == ("POST", "/streams"):
            missing = {f: [f"{f.replace('_', ' ').capitalize()} is required"]
                       for f in STREAM_REQUIRED if not (body or {}).get(f)}
            if missing:
                raise _err(422, missing)
            self._campaign(body["campaign_id"])
            return self._new_stream(body)
        if x := re.fullmatch(r"/streams/(\d+)", path):
            sid = int(x[1])
            s = self.streams_data.get(sid)
            if s is None:
                raise _err(404, {"error": "Not found"})
            if method == "GET":
                return s
            if method == "PUT":
                payload = body or {}
                if "offers" in payload:
                    self._set_offers(s, payload.pop("offers"))
                s.update({k: v for k, v in payload.items() if k in ("name", "position", "state", "type",
                                                                    "action_type", "action_payload", "filters")})
                return s

        raise _err(404, {"error": f"Fake Keitaro: {method} {path} is not implemented"})
