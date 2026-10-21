import uuid

from httpx import AsyncClient


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
            "requires_funds": True,
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert "id" in body
    assert body["name"] == "test_account"
    assert body["currency"] == "INR"
    assert body["kind"] == "CUSTOMER"
    assert body["requires_funds"] is True


async def test_get_valid_account(client: AsyncClient) -> None:

    response_created = await client.post(
        "/accounts",
        json={
            "name": "test_account",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": True,
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
            "requires_funds": True,
        },
    )

    assert response.status_code == 422


async def test_new_account_has_zero_balance(client: AsyncClient) -> None:
    created = await client.post(
        "/accounts",
        json={
            "name": "test_account",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": True,
        },
    )

    response = await client.get(f"/accounts/{created.json()['id']}/balance")

    assert response.status_code == 200
    assert response.json() == {"amount_minor": 0, "currency": "INR"}


async def test_new_account_bool_passed_as_string(client: AsyncClient) -> None:

    response = await client.post(
        "/accounts",
        json={
            "name": "test_account",
            "currency": "INR",
            "kind": "CUSTOMER",
            "requires_funds": "true",
        },
    )

    assert response.status_code == 422
