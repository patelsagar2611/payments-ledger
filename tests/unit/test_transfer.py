import uuid
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from payments.domain.account import (
    Account,
    AccountKind,
)
from payments.domain.money import Currency, CurrencyMismatchError, Money
from payments.domain.transfer import (
    Entry,
    InvalidEntryAccountError,
    InvalidEntryTransferIdError,
    InvalidTransferAmountError,
    InvalidTransferEntriesTotalError,
    SameAccountTransferError,
    Transfer,
    TransferStatus,
)


@pytest.fixture
def source_account() -> Account:
    return Account(
        name="source",
        currency=Currency.INR,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )


@pytest.fixture
def destination_account() -> Account:
    return Account(
        name="destination",
        currency=Currency.INR,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )


@pytest.fixture
def third_party_account() -> Account:
    return Account(
        name="third_party",
        currency=Currency.INR,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )


@pytest.fixture
def destination_account_usd() -> Account:
    return Account(
        name="destination",
        currency=Currency.USD,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )


@pytest.fixture
def amount_money() -> Money:
    return Money(50, Currency.INR)


@pytest.fixture
def amount_money_usd() -> Money:
    return Money(50, Currency.USD)


def generate_entry(
    account_id: uuid.UUID, transfer_id: uuid.UUID, amount: Money
) -> Entry:
    return Entry(account_id=account_id, transfer_id=transfer_id, amount=amount)


def test_valid_transfer(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    amount = amount_money
    transfer = Transfer.create(
        amount=amount, source=source_acc, destination=destination_acc
    )

    assert transfer.status == TransferStatus.COMPLETED
    assert len(transfer.entries) == 2
    for entry in transfer.entries:
        if entry.account_id == source_acc.id:
            assert entry.transfer_id == transfer.id
            assert entry.amount.amount_minor == -amount.amount_minor
        elif entry.account_id == destination_acc.id:
            assert entry.transfer_id == transfer.id
            assert entry.amount.amount_minor == amount.amount_minor
        else:
            pytest.fail(f"unexpected entry account {entry.account_id!r}")


@pytest.mark.parametrize(
    ("amount"),
    [
        pytest.param(-50),
        pytest.param(0),
    ],
)
def test_invalid_amount_transfer(
    source_account: Account, destination_account: Account, amount: int
) -> None:
    with pytest.raises(InvalidTransferAmountError):
        Transfer.create(
            amount=Money(amount, Currency.INR),
            source=source_account,
            destination=destination_account,
        )


def test_same_account_transfer(source_account: Account, amount_money: Money) -> None:
    with pytest.raises(SameAccountTransferError):
        Transfer.create(
            amount=amount_money, source=source_account, destination=source_account
        )


def test_currency_mismatch_dest_transfer(
    source_account: Account, destination_account_usd: Account, amount_money: Money
) -> None:
    with pytest.raises(CurrencyMismatchError):
        Transfer.create(
            amount=amount_money,
            source=source_account,
            destination=destination_account_usd,
        )


def test_currency_mismatch_transfer(
    source_account: Account, destination_account: Account, amount_money_usd: Money
) -> None:
    with pytest.raises(CurrencyMismatchError):
        Transfer.create(
            amount=amount_money_usd,
            source=source_account,
            destination=destination_account,
        )


def test_entries_are_frozen(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    destination_acc = destination_account

    transfer = Transfer.create(
        amount=amount_money, source=source_account, destination=destination_acc
    )

    entry = generate_entry(destination_acc.id, uuid.uuid4(), Money(100, Currency.INR))
    with pytest.raises(FrozenInstanceError):
        transfer.entries += (entry,)  # type: ignore[misc]


def test_entry_items_are_frozen(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    transfer = Transfer.create(
        amount=amount_money, source=source_account, destination=destination_account
    )

    with pytest.raises(FrozenInstanceError):
        transfer.entries[0].account_id = uuid.uuid4()  # type: ignore[misc]


def test_manual_entries_transfer(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.USD)
    credit_entry = generate_entry(destination_acc.id, transfer_id, credit_amount)

    with pytest.raises(CurrencyMismatchError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_timezone_transfer(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    before_timestamp = datetime.now(UTC)
    transfer = Transfer.create(
        amount=amount_money, source=source_account, destination=destination_account
    )
    after_timestamp = datetime.now(UTC)

    assert before_timestamp <= transfer.created_at <= after_timestamp
    assert transfer.created_at.tzinfo == UTC


def test_entries_with_different_transfer_id(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()
    transfer_id2 = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.INR)
    credit_entry = generate_entry(destination_acc.id, transfer_id2, credit_amount)

    with pytest.raises(InvalidEntryTransferIdError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_entries_with_different_account(
    source_account: Account,
    destination_account: Account,
    third_party_account: Account,
    amount_money: Money,
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.INR)
    credit_entry = generate_entry(third_party_account.id, transfer_id, credit_amount)

    with pytest.raises(InvalidEntryAccountError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_entries_with_same_incorrect_amounts(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-45, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(45, Currency.INR)
    credit_entry = generate_entry(destination_acc.id, transfer_id, credit_amount)

    with pytest.raises(InvalidTransferEntriesTotalError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_entries_with_different_incorrect_amounts(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-45, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(55, Currency.INR)
    credit_entry = generate_entry(destination_acc.id, transfer_id, credit_amount)

    with pytest.raises(InvalidTransferEntriesTotalError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_entries_with_empty_tuple(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)

    with pytest.raises(InvalidTransferEntriesTotalError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(),
        )


def test_entries_with_same_source_dest_acc(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.INR)
    credit_entry = generate_entry(source_acc.id, transfer_id, credit_amount)

    with pytest.raises(InvalidTransferEntriesTotalError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_transfer_with_negative_amount(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(-50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.INR)
    credit_entry = generate_entry(destination_acc.id, transfer_id, credit_amount)

    with pytest.raises(InvalidTransferAmountError):
        Transfer(
            id=transfer_id,
            amount=amount,
            source_id=source_acc.id,
            destination_id=destination_acc.id,
            status=TransferStatus.COMPLETED,
            entries=(debit_entry, credit_entry),
        )


def test_entries_with_different_order_tuple(
    source_account: Account, destination_account: Account, amount_money: Money
) -> None:
    source_acc = source_account
    destination_acc = destination_account
    transfer_id = uuid.uuid4()

    amount = Money(50, Currency.INR)
    debit_amount = Money(-50, Currency.INR)
    debit_entry = generate_entry(source_acc.id, transfer_id, debit_amount)
    credit_amount = Money(50, Currency.INR)
    credit_entry = generate_entry(destination_acc.id, transfer_id, credit_amount)

    # entry order is not part of validity: Postgres may return rows in any order
    transfer = Transfer(
        id=transfer_id,
        amount=amount,
        source_id=source_acc.id,
        destination_id=destination_acc.id,
        status=TransferStatus.COMPLETED,
        entries=(credit_entry, debit_entry),
    )

    assert transfer.entries == (credit_entry, debit_entry)
