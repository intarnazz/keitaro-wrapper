import httpx


class KeitaroError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(f"Keitaro {status}: {detail}")
        self.status = status
        self.detail = detail


class KeitaroClient:
    def __init__(self, base_url: str, api_key: str):
        self._http = httpx.Client(
            base_url=base_url, headers={"Api-Key": api_key}, timeout=15
        )

    def _request(self, method: str, path: str, **kwargs):
        try:
            r = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as e:
            raise KeitaroError(502, f"network error: {e}") from e
        if r.status_code >= 400:
            raise KeitaroError(r.status_code, r.text[:500])
        return r.json() if r.content else None

    def get(self, path: str, **params):
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict):
        return self._request("POST", path, json=json)

    def put(self, path: str, json: dict):
        return self._request("PUT", path, json=json)

    def delete(self, path: str):
        return self._request("DELETE", path)

    # справочники
    def domains(self):
        return self.get("/domains")

    def groups(self):
        return self.get("/groups", type="campaigns")

    def traffic_sources(self):
        return self.get("/traffic_sources")

    # чтение
    def campaigns(self, limit: int = 100, offset: int = 0) -> list[dict]:
        return self.get("/campaigns", limit=limit, offset=offset)

    def campaign(self, campaign_id: int) -> dict:
        return self.get(f"/campaigns/{campaign_id}")

    def campaign_streams(self, campaign_id: int) -> list[dict]:
        return self.get(f"/campaigns/{campaign_id}/streams")

    def stream(self, stream_id: int) -> dict:
        return self.get(f"/streams/{stream_id}")

    def offers(self) -> list[dict]:
        return self.get("/offers")

    def offer(self, offer_id: int) -> dict:
        return self.get(f"/offers/{offer_id}")

    # запись
    def create_campaign(self, payload: dict) -> dict:
        return self.post("/campaigns", payload)

    def update_campaign(self, campaign_id: int, payload: dict) -> dict:
        return self.put(f"/campaigns/{campaign_id}", payload)

    def delete_campaign(self, campaign_id: int):
        return self.delete(f"/campaigns/{campaign_id}")

    def create_stream(self, payload: dict) -> dict:
        return self.post("/streams", payload)

    def update_stream(self, stream_id: int, payload: dict) -> dict:
        return self.put(f"/streams/{stream_id}", payload)
