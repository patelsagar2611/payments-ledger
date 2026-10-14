import re
import uuid

import pytest

from payments.domain.account import (
    Account,
    AccountKind,
    AccountKindInvalidError,
    MissingAccountNameError,
)
from payments.domain.money import (
    Currency,
    CurrencyInvalidError,
)


def test_valid_account() -> None:
    account = Account(
        name="acc_name",
        currency=Currency.INR,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )
    assert isinstance(account.id, uuid.UUID)


@pytest.mark.parametrize(
    ("name", "currency", "kind", "expected_exception", "message"),
    [
        pytest.param(
            " ",
            Currency.INR,
            AccountKind.CUSTOMER,
            MissingAccountNameError,
            "name cannot be empty",
            id="empty_name",
        ),
        pytest.param(
            "123456",
            "EUR",
            AccountKind.CUSTOMER,
            CurrencyInvalidError,
            "'EUR' is not a valid",
            id="currency",
        ),
        pytest.param(
            "acc_name",
            Currency.INR,
            "BALD",
            AccountKindInvalidError,
            "not a valid account kind",
            id="accountkind",
        ),
    ],
)
def test_account_create(
    name: object,
    currency: object,
    kind: object,
    expected_exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(expected_exception, match=re.escape(message)):
        Account(name=name, currency=currency, kind=kind, requires_funds=True)  # type: ignore[arg-type]
