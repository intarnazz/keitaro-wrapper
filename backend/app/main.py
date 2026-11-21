from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.keitaro.client import KeitaroClient, KeitaroError

app = FastAPI(title="Keitaro wrapper")


def get_keitaro() -> KeitaroClient:
    return KeitaroClient(settings.keitaro_url, settings.keitaro_api_key)


@app.exception_handler(KeitaroError)
def keitaro_error_handler(_: Request, exc: KeitaroError):
    status = exc.status if exc.status in (400, 404, 422) else 502
    return JSONResponse(status_code=status, content={"detail": exc.detail})


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/domains")
def domains(k: KeitaroClient = Depends(get_keitaro)):
    return k.domains()


@app.get("/api/groups")
def groups(k: KeitaroClient = Depends(get_keitaro)):
    return k.groups()


@app.get("/api/traffic-sources")
def traffic_sources(k: KeitaroClient = Depends(get_keitaro)):
    return k.traffic_sources()