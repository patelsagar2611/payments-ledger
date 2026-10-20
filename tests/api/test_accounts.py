import uuid
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


async def test_get_unknown_account_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/accounts/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_create_valid_account(client: AsyncClient) -> None:

    response = await client.post(
        "/accounts",
        json={
            "name": "test_account",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": "true",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body
    assert body["name"] == "test_account"
    assert body["currency"] == "INR"
    assert body["kind"] == "CUSTOMER"
    assert body["requires_funds"]


async def test_get_valid_account(client: AsyncClient) -> None:

    response_created = await client.post(
        "/accounts",
        json={
            "name": "test_account",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": "true",
        },
    )

    assert response_created.status_code == 201

    body_created = response_created.json()
    assert "id" in body_created

    response_get = await client.get(f"/accounts/{body_created['id']}")

    assert response_get.status_code == 200

    assert response_get.json() == response_created.json()


async def test_get_non_uuid_account_returns_422(client: AsyncClient) -> None:
    response = await client.get("/accounts/not-a-uuid")

    assert response.status_code == 422


async def test_create_invalid_account(client: AsyncClient) -> None:

    response = await client.post(
        "/accounts",
        json={
            "name": " ",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": "true",
        },
    )

    assert response.status_code == 422
