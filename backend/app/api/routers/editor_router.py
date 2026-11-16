import uuid
from fastapi import APIRouter, Depends
from ..deps import get_editor_service, get_push_service, get_kt_client
from ..schemas import AddOfferIn, SetFixedIn
from app.keitaro.client import KeitaroClient
from app.services.editor_service import EditorService
from app.services.push_service import PushService

router = APIRouter(prefix="/campaigns/{campaign_id}/editor", tags=["editor"])


@router.get("")
async def get_state(
    campaign_id: uuid.UUID,
    svc: EditorService = Depends(get_editor_service),
):
    return await svc.get_state(campaign_id)


@router.post("/streams/{stream_id}/offers")
async def add_offer(
    campaign_id: uuid.UUID,
    stream_id: uuid.UUID,
    body: AddOfferIn,
    svc: EditorService = Depends(get_editor_service),
):
    return await svc.add_offer(campaign_id, stream_id, body.keitaro_offer_id, body.name)


@router.delete("/streams/{stream_id}/offers/{offer_row_id}")
async def remove_offer(
    campaign_id: uuid.UUID,
    stream_id: uuid.UUID,
    offer_row_id: uuid.UUID,
    svc: EditorService = Depends(get_editor_service),
):
    return await svc.remove_offer(campaign_id, stream_id, offer_row_id)


@router.post("/streams/{stream_id}/offers/{offer_row_id}/rollback")
async def rollback_offer(
    campaign_id: uuid.UUID,
    stream_id: uuid.UUID,
    offer_row_id: uuid.UUID,
    svc: EditorService = Depends(get_editor_service),
):
    return await svc.rollback_offer(campaign_id, stream_id, offer_row_id)


@router.patch("/streams/{stream_id}/offers/{offer_row_id}")
async def set_fixed(
    campaign_id: uuid.UUID,
    stream_id: uuid.UUID,
    offer_row_id: uuid.UUID,
    body: SetFixedIn,
    svc: EditorService = Depends(get_editor_service),
):
    return await svc.set_fixed(
        campaign_id, stream_id, offer_row_id, body.fixed, body.weight
    )


@router.post("/fetch")
async def fetch_from_kt(
    campaign_id: uuid.UUID,
    svc: EditorService = Depends(get_editor_service),
    client: KeitaroClient = Depends(get_kt_client),
):
    return await svc.fetch_from_kt(campaign_id, client)


@router.post("/discard")
async def discard(
    campaign_id: uuid.UUID,
    svc: EditorService = Depends(get_editor_service),
    client: KeitaroClient = Depends(get_kt_client),
):
    return await svc.discard(campaign_id, client)


@router.post("/push")
async def push(
    campaign_id: uuid.UUID,
    svc: PushService = Depends(get_push_service),
):
    return await svc.push(campaign_id)
