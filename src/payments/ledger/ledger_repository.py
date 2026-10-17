import uuid
from typing import Protocol

from payments.domain.account import Account
from payments.domain.errors import ConflictError, DomainError
from payments.domain.money import Money
from payments.domain.transfer import Transfer


class AccountNotFoundError(DomainError, LookupError):
    """No account exists with the given id."""


class TransferNotFoundError(DomainError, LookupError):
    """No transfer exists with the given id."""


class InsufficientFundsError(ConflictError):
    """The source account cannot cover the transfer amount."""


class LedgerRepository(Protocol):
    """Storage contract for the ledger."""

    async def get_account(self, account_id: uuid.UUID) -> Account:
        """Return the account with this id.

        Raises AccountNotFoundError if it does not exist.
        """
        ...

    async def save_account(self, account: Account) -> None:
        """Store a new account."""
        ...

    async def get_transfer(self, transfer_id: uuid.UUID) -> Transfer:
        """Return the transfer with this id.

        Raises TransferNotFoundError if it does not exist.
        """
        ...

    async def get_balance(self, account_id: uuid.UUID) -> Money:
        """Return the current balance of the account.

        Raises AccountNotFoundError if account does not exist.
        """
        ...

    async def save_transfer(self, transfer: Transfer) -> None:
        """Store a transfer and its entries atomically.

        Raises AccountNotFoundError if the source or destination does not exist.
        Raises InsufficientFundsError if the source requires funds and its
        balance would go negative.
        """
        ...
