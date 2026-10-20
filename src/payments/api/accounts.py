import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from payments.api.dependencies import RepositoryDep
from payments.domain.account import Account, AccountKind
from payments.domain.money import Currency

router = APIRouter(prefix="/accounts", tags=["accounts"])


class CreateAccountRequest(BaseModel):
    name: str
    currency: Currency
    kind: AccountKind
    requires_funds: bool


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency: Currency
    kind: AccountKind
    requires_funds: bool
    created_at: datetime


@router.post("", status_code=201)
async def create_account(
    body: CreateAccountRequest, repository: RepositoryDep
) -> AccountResponse:
    account = Account(
        name=body.name,
        currency=body.currency,
        kind=body.kind,
        requires_funds=body.requires_funds,
    )
    await repository.save_account(account)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}")
async def get_account(
    account_id: uuid.UUID, repository: RepositoryDep
) -> AccountResponse:
    account = await repository.get_account(account_id)
    return AccountResponse.model_validate(account)
