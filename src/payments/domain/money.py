"""
1. An amount is always a whole number of minor units (paise), never a float.
2. An amount always carries its currency; a bare number is meaningless.
3. Amounts in different currencies can never be combined.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from payments.domain.errors import DomainError


class Currency(StrEnum):
    INR = "INR"
    USD = "USD"


class CurrencyMismatchError(DomainError, ValueError):
    """Raised when combining amounts in different currencies."""


class CurrencyInvalidError(DomainError, TypeError):
    """Raised when a currency is not a member of Currency."""


@dataclass(frozen=True)
class Money:
    amount_minor: int
    currency: Currency

    def __post_init__(self) -> None:
        if type(self.amount_minor) is not int:
            raise TypeError(f"amount needs to be int but got {self.amount_minor!r}")
        if not isinstance(self.currency, Currency):
            raise CurrencyInvalidError(f"{self.currency!r} is not a valid currency")

    def __add__(self, other: Self) -> Self:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"different currencies can not be added: "
                f"{self.currency} and {other.currency}"
            )
        return type(self)(self.amount_minor + other.amount_minor, self.currency)

    def __neg__(self) -> Self:
        return type(self)(-self.amount_minor, self.currency)
