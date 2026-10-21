import uuid

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from payments.api.dependencies import RepositoryDep
from payments.api.schemas import MoneyModel
from payments.domain.money import Money
from payments.domain.transfer import Transfer, TransferStatus

router = APIRouter(prefix="/transfers", tags=["transfers"])


class CreateTransferRequest(BaseModel):
    amount: MoneyModel
    source_id: uuid.UUID
    destination_id: uuid.UUID


class TransferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    destination_id: uuid.UUID
    amount: MoneyModel
    status: TransferStatus


@router.post("", status_code=201)
async def create_transfer(
    body: CreateTransferRequest, repository: RepositoryDep
) -> TransferResponse:
    source_acc = await repository.get_account(body.source_id)
    destination_acc = await repository.get_account(body.destination_id)
    amount_money = Money(body.amount.amount_minor, body.amount.currency)

    transfer = Transfer.create(
        amount=amount_money, source=source_acc, destination=destination_acc
    )
    await repository.save_transfer(transfer)

    return TransferResponse.model_validate(transfer)

