import uuid
from pydantic import BaseModel, Field


class CreateCampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo_code: str = Field(min_length=2, max_length=2)
    offer_id: int
    offer_name: str | None = None
    domain: str | None = None
    group_id: int | None = None
    source_id: int | None = None


class CampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    geo_code: str
    domain: str
    group_id: int
    source_id: int
    keitaro_campaign_id: int | None
    current_version_number: int | None


class AddOfferIn(BaseModel):
    keitaro_offer_id: int
    name: str | None = None


class SetFixedIn(BaseModel):
    fixed: bool
    weight: float | None = None
