import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.services.editor_service import EditorService
from app.models import Campaign, Stream, StreamOffer


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.campaigns = MagicMock()
    uow.streams = MagicMock()
    uow.session = MagicMock()

    uow.session.flush = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.mark.asyncio
async def test_add_offer_success(mock_uow):
    service = EditorService(mock_uow)

    campaign = Campaign(id="c1")
    stream = Stream(id="s1", type="flow", campaign_id="c1")
    existing_offer = StreamOffer(keitaro_offer_id=100, weight=Decimal("100.00"))
    stream.offers = [existing_offer]

    mock_uow.campaigns.get = AsyncMock(return_value=campaign)
    mock_uow.campaigns.get_with_streams = AsyncMock(return_value=campaign)  # <-- Добавлено
    mock_uow.streams.get = AsyncMock(return_value=stream)
    mock_uow.streams.by_campaign = AsyncMock(return_value=[stream])  # <-- Добавлено для get_state
    mock_uow.campaigns.active_draft_session = AsyncMock(return_value=None)

    mock_uow.streams.add_offer.side_effect = lambda offer: stream.offers.append(offer)

    await service.add_offer("c1", "s1", keitaro_offer_id=200, name="Test")

    mock_uow.streams.add_offer.assert_called_once()
    mock_uow.commit.assert_called_once()

    assert len(stream.offers) == 2
    assert stream.offers[0].weight == Decimal("50.00")
    assert stream.offers[1].weight == Decimal("50.00")


@pytest.mark.asyncio
async def test_add_offer_to_redirect_stream_fails(mock_uow):
    service = EditorService(mock_uow)
    campaign = Campaign(id="c1")
    stream = Stream(id="s1", type="redirect", campaign_id="c1")

    mock_uow.campaigns.get = AsyncMock(return_value=campaign)
    mock_uow.streams.get = AsyncMock(return_value=stream)

    from app.exceptions import ValidationError
    with pytest.raises(ValidationError, match="flow"):
        await service.add_offer("c1", "s1", keitaro_offer_id=200, name="Test")