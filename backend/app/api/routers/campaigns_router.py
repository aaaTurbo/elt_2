import uuid
from fastapi import APIRouter, Depends
from ..deps import get_campaign_service
from ..schemas import CampaignOut, CreateCampaignIn
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignOut)
async def create(
    body: CreateCampaignIn,
    svc: CampaignService = Depends(get_campaign_service),
):
    c = await svc.create(
        name=body.name,
        geo_code=body.geo_code,
        offer_id=body.offer_id,
        offer_name=body.offer_name,
        domain=body.domain,
        group_id=body.group_id,
        source_id=body.source_id,
    )
    return CampaignOut.model_validate(c, from_attributes=True)


@router.get("", response_model=list[CampaignOut])
async def list_all(svc: CampaignService = Depends(get_campaign_service)):
    items = await svc.list()
    return [CampaignOut.model_validate(c, from_attributes=True) for c in items]


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_one(
    campaign_id: uuid.UUID,
    svc: CampaignService = Depends(get_campaign_service),
):
    c = await svc.get(campaign_id)
    return CampaignOut.model_validate(c, from_attributes=True)