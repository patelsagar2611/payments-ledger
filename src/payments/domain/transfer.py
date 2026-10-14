import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from payments.domain.account import Account
from payments.domain.errors import DomainError
from payments.domain.money import CurrencyMismatchError, Money


class InvalidEntryAccountError(DomainError, ValueError):
    """Raised when account_id in Entry is invalid"""


class InvalidEntryTransferIdError(DomainError, ValueError):
    """Raised when transfer_id in Entry is invalid"""


class InvalidEntryAmountError(DomainError, ValueError):
    """Raised when amount in Entry is invalid"""


@dataclass(frozen=True, kw_only=True)
class Entry:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    account_id: uuid.UUID
    transfer_id: uuid.UUID
    amount: Money
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not isinstance(self.account_id, uuid.UUID):
            raise InvalidEntryAccountError(f"invalid account id {self.account_id!r}")
        if not isinstance(self.transfer_id, uuid.UUID):
            raise InvalidEntryTransferIdError(f"Invalid transfer id {self.transfer_id}")
        if self.amount.amount_minor == 0:
            raise InvalidEntryAmountError("amount cannot be zero from transfer entry")


class TransferStatus(StrEnum):
    COMPLETED = "COMPLETED"
    REVERSED = "REVERSED"


class SameAccountTransferError(DomainError, ValueError):
    """Raised when source and destination accounts are same"""


class InvalidTransferAmountError(DomainError, ValueError):
    """Raised when transfer amount is invalid"""


class InvalidTransferEntriesTotalError(DomainError, ValueError):
    """Raised when transfer entries' total sum is invalid instead of 0"""


@dataclass(frozen=True, kw_only=True)
class Transfer:
    id: uuid.UUID
    amount: Money
    source_id: uuid.UUID
    destination_id: uuid.UUID
    status: TransferStatus
    entries: tuple[Entry, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.amount.amount_minor <= 0:
            raise InvalidTransferAmountError(
                f"transfer amount: {self.amount.amount_minor!r} is invalid"
            )
        if self.source_id == self.destination_id:
            raise SameAccountTransferError(
                "source and destination needs to be different accounts"
            )
        sum_debit = 0
        sum_credit = 0
        for entry in self.entries:
            if entry.transfer_id != self.id:
                raise InvalidEntryTransferIdError(
                    f"incorrect transfer id for entry. "
                    f"got {entry.transfer_id!r} instead of {self.id!r}"
                )
            if entry.amount.currency != self.amount.currency:
                raise CurrencyMismatchError(
                    f"invalid currency in entry. "
                    f"got {entry.amount.currency!r} instead of {self.amount.currency!r}"
                )
            if entry.account_id == self.source_id:
                sum_debit += entry.amount.amount_minor
            elif entry.account_id == self.destination_id:
                sum_credit += entry.amount.amount_minor
            else:
                raise InvalidEntryAccountError(
                    f"invalid account id: {entry.account_id!r}"
                )
        if sum_credit != -sum_debit or sum_credit != self.amount.amount_minor:
            raise InvalidTransferEntriesTotalError(
                f"invalid transfer entries. "
                f"credit is {sum_credit!r} and debit is {sum_debit!r}, "
                f"transfer amount is {self.amount.amount_minor!r}"
            )

    @classmethod
    def create(cls, *, amount: Money, source: Account, destination: Account) -> Self:
        if amount.amount_minor <= 0:
            raise InvalidTransferAmountError(
                f"transfer amount: {amount.amount_minor!r} is invalid"
            )
        if not (amount.currency == source.currency == destination.currency):
            raise CurrencyMismatchError(
                f"currency mismatch, amount: "
                f"{amount.currency!r}, source: {source.currency!r}, "
                f"destination: {destination.currency!r}"
            )
        generated_id = uuid.uuid4()

        credit = Entry(
            account_id=destination.id, transfer_id=generated_id, amount=amount
        )

        debit = Entry(account_id=source.id, transfer_id=generated_id, amount=-amount)

        return cls(
            id=generated_id,
            amount=amount,
            source_id=source.id,
            destination_id=destination.id,
            status=TransferStatus.COMPLETED,
            entries=(debit, credit),
        )
