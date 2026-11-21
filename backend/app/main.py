import json
from typing import Any

from fastapi import Depends, FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.keitaro.client import KeitaroClient, KeitaroError
from app.schemas import ApiResponse, CampaignCreate, CampaignCreated
from app.services.campaigns import DefaultNotFound, create_campaign_with_streams

app = FastAPI(title="Keitaro wrapper")


def get_keitaro() -> KeitaroClient:
    return KeitaroClient(settings.keitaro_url, settings.keitaro_api_key)


# ---------- единый формат ответов: {"success", "message", "data"} ----------

def fail(status_code: int, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "data": data},
    )


def short_text(text: str, limit: int = 200) -> str:
    """Краткий текст ошибки: достаём error/message из JSON Keitaro или режем строку."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            for key in ("error", "message", "detail"):
                if isinstance(parsed.get(key), str):
                    text = parsed[key]
                    break
    except ValueError:
        pass
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


@app.exception_handler(KeitaroError)
def keitaro_error_handler(_: Request, exc: KeitaroError):
    code = exc.status if exc.status in (400, 404, 422) else 502
    return fail(
        code,
        f"Keitaro: {short_text(exc.detail)}",
        {"keitaro_status": exc.status, "detail": exc.detail},
    )


def _body_model(request: Request):
    """Pydantic-модель тела запроса текущего маршрута (если есть)."""
    model = getattr(request.state, "body_model", None)
    if model is not None:
        return model
    route = request.scope.get("route")
    body_field = getattr(route, "body_field", None)
    model = getattr(getattr(body_field, "field_info", None), "annotation", None)
    return model if hasattr(model, "model_fields") else None


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    """422: какие поля обязательны, какие нет и что именно не так."""
    errors = jsonable_encoder(exc.errors())
    data: dict = {"errors": errors}

    model = _body_model(request)
    if model is not None:
        required = [n for n, f in model.model_fields.items() if f.is_required()]
        optional = [n for n, f in model.model_fields.items() if not f.is_required()]
        data["required_fields"] = required
        data["optional_fields"] = optional

        # Тело не передано совсем: вместо одной ошибки "body" показываем каждое поле.
        if any(e["loc"] == ["body"] and e["type"] == "missing" for e in errors):
            data["errors"] = errors = [
                {"type": "missing", "loc": ["body", n], "msg": "Field required", "input": None}
                for n in required
            ]

    missing = [str(e["loc"][-1]) for e in errors if e["type"] == "missing"]
    others = [
        f"{'.'.join(map(str, e['loc'][1:]))}: {e['msg']}" if len(e["loc"]) > 1 else e["msg"]
        for e in errors
        if e["type"] != "missing"
    ]
    parts = ([f"missing required fields: {', '.join(missing)}"] if missing else []) + others
    return fail(422, short_text("Validation error: " + "; ".join(parts)), data)


@app.exception_handler(DefaultNotFound)
def default_not_found_handler(_: Request, exc: DefaultNotFound):
    return fail(400, short_text(str(exc)))


@app.exception_handler(StarletteHTTPException)
def http_error_handler(_: Request, exc: StarletteHTTPException):
    return fail(exc.status_code, short_text(str(exc.detail)))


@app.exception_handler(Exception)
def unexpected_error_handler(_: Request, exc: Exception):
    return fail(500, "Internal server error")


# ---------- тело запроса: JSON, multipart/form-data или x-www-form-urlencoded ----------

def _body_error(error_type: str, msg: str) -> RequestValidationError:
    return RequestValidationError([{"type": error_type, "loc": ("body",), "msg": msg, "input": None}])


async def campaign_payload(request: Request) -> CampaignCreate:
    request.state.body_model = CampaignCreate  # чтобы 422 знал список полей
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()

    if content_type == "application/json":
        raw = await request.body()
        try:
            data = json.loads(raw) if raw.strip() else {}
        except ValueError:
            raise _body_error("json_invalid", "JSON decode error")
    elif content_type in ("multipart/form-data", "application/x-www-form-urlencoded"):
        form = await request.form()
        # пустые значения считаем «не передано»; файлы игнорируем
        data = {k: v for k, v in form.items() if isinstance(v, str) and v.strip() != ""}
    elif await request.body():
        raise _body_error(
            "unsupported_content_type",
            "Use application/json, multipart/form-data or application/x-www-form-urlencoded",
        )
    else:
        data = {}

    if not isinstance(data, dict):
        raise _body_error("dict_type", "Input should be an object")
    try:
        return CampaignCreate.model_validate(data)
    except ValidationError as e:
        raise RequestValidationError(
            [{**err, "loc": ("body", *err["loc"])} for err in e.errors()]
        )


# ---------- маршруты ----------

@app.get("/api/health", response_model=ApiResponse[dict[str, bool]])
def health():
    return ApiResponse(data={"ok": True})


@app.get("/api/domains", response_model=ApiResponse[list[dict[str, Any]]])
def domains(k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=k.domains())


@app.get("/api/groups", response_model=ApiResponse[list[dict[str, Any]]])
def groups(k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=k.groups())


@app.get("/api/traffic-sources", response_model=ApiResponse[list[dict[str, Any]]])
def traffic_sources(k: KeitaroClient = Depends(get_keitaro)):
    return ApiResponse(data=k.traffic_sources())


_campaign_schema = CampaignCreate.model_json_schema()


@app.post(
    "/api/campaigns",
    response_model=ApiResponse[CampaignCreated],
    status_code=status.HTTP_201_CREATED,
    openapi_extra={  # описание тела для Swagger: принимаем JSON и form-data
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": _campaign_schema},
                "multipart/form-data": {"schema": _campaign_schema},
                "application/x-www-form-urlencoded": {"schema": _campaign_schema},
            },
        }
    },
)
def create_campaign(
    data: CampaignCreate = Depends(campaign_payload),
    k: KeitaroClient = Depends(get_keitaro),
):
    return ApiResponse(data=create_campaign_with_streams(k, data))
