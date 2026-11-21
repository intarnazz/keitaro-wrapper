import re
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Единый формат всех ответов API."""

    success: bool = True
    message: str = "success"
    data: T | None = None


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: str = Field(description="Код страны, 2 буквы: AU, US, ...")
    offer_id: int = Field(gt=0, description="ID оффера в Keitaro")
    domain_id: int | None = Field(
        default=None, description="Если не задан, берётся первый активный домен Keitaro"
    )
    group_id: int | None = Field(
        default=None, description="Если не задан, берётся первая группа кампаний Keitaro"
    )
    traffic_source_id: int | None = Field(
        default=None, description="Если не задан, берётся первый источник трафика Keitaro"
    )
    alias: str | None = Field(
        default=None, description="Если не задан, будет сгенерирован из названия"
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name не может быть пустым")
        return v

    @field_validator("geo")
    @classmethod
    def normalize_geo(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", v):
            raise ValueError("geo должен состоять из двух латинских букв")
        return v


class CampaignCreated(BaseModel):
    campaign_id: int
    alias: str
    domain_id: int
    group_id: int
    traffic_source_id: int
    streams: list[int]
