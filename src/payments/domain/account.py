import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from payments.domain.errors import DomainError
from payments.domain.money import Currency, CurrencyInvalidError


class AccountKind(StrEnum):
    CUSTOMER = "CUSTOMER"
    MERCHANT = "MERCHANT"
    SYSTEM = "SYSTEM"


class MissingAccountNameError(DomainError, ValueError):
    """Raised when account name is empty"""


class AccountKindInvalidError(DomainError, TypeError):
    """Raised when account kind is not a member of AccountKind"""


@dataclass(frozen=True, kw_only=True)
class Account:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str
    currency: Currency
    kind: AccountKind
    requires_funds: bool
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not (self.name and self.name.strip()):
            raise MissingAccountNameError("account name cannot be empty")
        if not isinstance(self.currency, Currency):
            raise CurrencyInvalidError(f"{self.currency!r} is not a valid currency")
        if not isinstance(self.kind, AccountKind):
            raise AccountKindInvalidError(f"{self.kind!r} is not a valid account kind")
