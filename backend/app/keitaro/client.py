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