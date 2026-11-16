import pytest
from unittest.mock import AsyncMock
from app.keitaro.offer_catalog import OfferCatalog


@pytest.mark.asyncio
async def test_search_by_prefix():
    client = AsyncMock()
    client.list_offers.return_value = [
        {"id": 101, "name": "Lead Gen DE"},
        {"id": 102, "name": "Crypto Trial US"},
    ]
    cat = OfferCatalog(client, ttl_seconds=300)

    res = await cat.search("102")
    assert [o["id"] for o in res] == [102]

    res = await cat.search("lead")
    assert [o["id"] for o in res] == [101]


@pytest.mark.asyncio
async def test_cache_hit():
    client = AsyncMock()
    client.list_offers.return_value = [{"id": 1, "name": "X"}]
    cat = OfferCatalog(client, ttl_seconds=300)

    await cat.search("")
    await cat.search("x")
    await cat.search("1")
    # закешировано — клиент дёрнут ровно один раз
    assert client.list_offers.await_count == 1
