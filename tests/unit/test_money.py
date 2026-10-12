import re
from dataclasses import FrozenInstanceError

import pytest

from payments.domain.money import (
    Currency,
    CurrencyInvalidError,
    CurrencyMismatchError,
    Money,
)


def test_sum() -> None:
    item_a = Money(10, Currency.INR)
    item_b = Money(20, Currency.INR)

    total = item_a + item_b

    assert total == Money(30, Currency.INR)
    # operands are untouched; addition returns a new object
    assert item_a == Money(10, Currency.INR)
    assert item_b == Money(20, Currency.INR)


def test_sum_different_currencies_raises() -> None:
    item_a = Money(10, Currency.INR)
    item_b = Money(5, Currency.USD)

    with pytest.raises(CurrencyMismatchError):
        item_a + item_b


@pytest.mark.parametrize(
    ("amount", "currency", "expected_exception", "message"),
    [
        pytest.param(10.5, Currency.INR, TypeError, "got 10.5", id="float"),
        pytest.param(True, Currency.INR, TypeError, "got True", id="bool"),
        pytest.param("100", Currency.INR, TypeError, "got '100'", id="str"),
        pytest.param(
            10, "EUR", CurrencyInvalidError, "'EUR' is not a valid", id="currency"
        ),
    ],
)
def test_invalid_money_raises(
    amount: object,
    currency: object,
    expected_exception: type[Exception],
    message: str,
) -> None:
    with pytest.raises(expected_exception, match=re.escape(message)):
        Money(amount, currency)  # type: ignore[arg-type]


def test_money_is_frozen() -> None:
    item_a = Money(10, Currency.INR)

    with pytest.raises(FrozenInstanceError):
        item_a.amount_minor = 20  # type: ignore[misc]
