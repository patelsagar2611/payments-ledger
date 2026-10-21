from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from payments.api.app import create_app
from payments.ledger.in_memory_repository import InMemoryLedgerRepository


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = create_app(InMemoryLedgerRepository())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        yield http_client
