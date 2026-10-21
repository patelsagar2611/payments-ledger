import uuid

import pytest
from httpx import AsyncClient


@pytest.fixture
async def customer_id(client: AsyncClient) -> uuid.UUID:
    response = await client.post(
        "/accounts",
        json={
            "name": "customer",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": True,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body

    return uuid.UUID(body["id"])


@pytest.fixture
async def system_id(client: AsyncClient) -> uuid.UUID:
    response = await client.post(
        "/accounts",
        json={
            "name": "system",
            "currency": "INR",
            "kind": "SYSTEM",
            "requires_funds": False,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body

    return uuid.UUID(body["id"])


@pytest.fixture
async def system_id_usd(client: AsyncClient) -> uuid.UUID:
    response = await client.post(
        "/accounts",
        json={
            "name": "system",
            "currency": "USD",
            "kind": "SYSTEM",
            "requires_funds": False,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body

    return uuid.UUID(body["id"])


async def test_transfer_unknown_destination_account_returns_404(
    client: AsyncClient, system_id: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(system_id),
            "destination_id": str(uuid.uuid4()),
            "amount": {"amount_minor": 5000, "currency": "INR"},
        },
    )

    assert response.status_code == 404


async def test_transfer_unfunded_source_account_returns_409(
    client: AsyncClient, customer_id: uuid.UUID, system_id: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(customer_id),
            "destination_id": str(system_id),
            "amount": {"amount_minor": 1, "currency": "INR"},
        },
    )

    assert response.status_code == 409


async def test_transfer_different_currency_source_account_returns_422(
    client: AsyncClient, customer_id: uuid.UUID, system_id_usd: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(system_id_usd),
            "destination_id": str(customer_id),
            "amount": {"amount_minor": 500, "currency": "INR"},
        },
    )

    assert response.status_code == 422


async def test_transfer_non_int_amount_returns_422(
    client: AsyncClient, customer_id: uuid.UUID, system_id: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(system_id),
            "destination_id": str(customer_id),
            "amount": {"amount_minor": 50.0, "currency": "INR"},
        },
    )

    assert response.status_code == 422


async def test_transfer_same_source_destination_account_returns_422(
    client: AsyncClient, customer_id: uuid.UUID, system_id: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(customer_id),
            "destination_id": str(customer_id),
            "amount": {"amount_minor": 50, "currency": "INR"},
        },
    )

    assert response.status_code == 422


async def test_create_valid_transfer(
    client: AsyncClient, customer_id: uuid.UUID, system_id: uuid.UUID
) -> None:

    response = await client.post(
        "/transfers",
        json={
            "source_id": str(system_id),
            "destination_id": str(customer_id),
            "amount": {"amount_minor": 5000, "currency": "INR"},
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body

    assert body["source_id"] == str(system_id)
    assert body["destination_id"] == str(customer_id)
    assert body["amount"] == {"amount_minor": 5000, "currency": "INR"}
    assert body["status"] == "COMPLETED"

    response_balance = await client.get(f"/accounts/{customer_id}/balance")

    assert response_balance.status_code == 200

    assert response_balance.json() == {"amount_minor": 5000, "currency": "INR"}
