import uuid

from payments.domain.account import Account
from payments.domain.money import Money
from payments.domain.transfer import Transfer
from payments.ledger.ledger_repository import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferNotFoundError,
)


class InMemoryLedgerRepository:
    """LedgerRepository backed by dictionaries, for tests and local runs."""

    def __init__(self) -> None:
        self._accounts: dict[uuid.UUID, Account] = {}
        self._transfers: dict[uuid.UUID, Transfer] = {}

    async def get_account(self, account_id: uuid.UUID) -> Account:
        try:
            return self._accounts[account_id]
        except KeyError:
            raise AccountNotFoundError(f"account {account_id} not found.") from None

    async def save_account(self, account: Account) -> None:
        self._accounts[account.id] = account

    async def get_transfer(self, transfer_id: uuid.UUID) -> Transfer:
        try:
            return self._transfers[transfer_id]
        except KeyError:
            raise TransferNotFoundError(f"transfer {transfer_id} not found.") from None

    async def save_transfer(self, transfer: Transfer) -> None:
        await self.get_account(transfer.destination_id)
        source_acc = await self.get_account(transfer.source_id)
        if source_acc.requires_funds:
            balance = await self.get_balance(source_acc.id)
            if balance.amount_minor < transfer.amount.amount_minor:
                raise InsufficientFundsError(source_acc.id)
        self._transfers[transfer.id] = transfer

    async def get_balance(self, account_id: uuid.UUID) -> Money:
        account = await self.get_account(account_id)
        return sum(
            (
                entry.amount
                for transfer in self._transfers.values()
                for entry in transfer.entries
                if entry.account_id == account_id
            ),
            start=Money(0, account.currency),
        )
