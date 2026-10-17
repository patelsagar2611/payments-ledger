import asyncio
import uuid

import pytest

from payments.domain.account import Account, AccountKind
from payments.domain.money import Currency, Money
from payments.domain.transfer import Transfer
from payments.ledger.in_memory_repository import InMemoryLedgerRepository
from payments.ledger.ledger_repository import (
    AccountNotFoundError,
    InsufficientFundsError,
    LedgerRepository,
    TransferNotFoundError,
)


@pytest.fixture
def repo() -> LedgerRepository:
    return InMemoryLedgerRepository()


@pytest.fixture
def customer() -> Account:
    return Account(
        name="customer",
        currency=Currency.INR,
        kind=AccountKind.CUSTOMER,
        requires_funds=True,
    )


@pytest.fixture
def system() -> Account:
    return Account(
        name="system",
        currency=Currency.INR,
        kind=AccountKind.SYSTEM,
        requires_funds=False,
    )


@pytest.fixture
def merchant() -> Account:
    return Account(
        name="merchant",
        currency=Currency.INR,
        kind=AccountKind.MERCHANT,
        requires_funds=True,
    )


@pytest.fixture
async def fund_customer(
    repo: LedgerRepository, customer: Account, system: Account
) -> None:
    await repo.save_account(system)
    await repo.save_account(customer)

    credit_customer = Transfer.create(
        amount=Money(100, Currency.INR), source=system, destination=customer
    )
    await repo.save_transfer(credit_customer)


async def test_new_account_has_zero_balance(
    repo: LedgerRepository, customer: Account
) -> None:
    await repo.save_account(customer)

    balance = await repo.get_balance(customer.id)

    assert balance == Money(0, Currency.INR)


async def test_unknown_account_balance_check_fails(
    repo: LedgerRepository, customer: Account
) -> None:
    with pytest.raises(AccountNotFoundError):
        await repo.get_balance(customer.id)


async def test_get_unknown_account_raises(repo: LedgerRepository) -> None:
    with pytest.raises(AccountNotFoundError):
        await repo.get_account(uuid.uuid4())


async def test_account_save(repo: LedgerRepository, customer: Account) -> None:
    await repo.save_account(customer)

    customer_acc = await repo.get_account(customer.id)

    assert customer_acc == customer


async def test_valid_transfer_funds_to_customer(
    repo: LedgerRepository, customer: Account, system: Account
) -> None:
    await repo.save_account(system)
    await repo.save_account(customer)

    transfer = Transfer.create(
        amount=Money(500, Currency.INR), source=system, destination=customer
    )
    await repo.save_transfer(transfer)

    system_balance = await repo.get_balance(system.id)
    customer_balance = await repo.get_balance(customer.id)

    assert system_balance == Money(-500, Currency.INR)
    assert customer_balance == Money(500, Currency.INR)


async def test_invalid_transfer_funds_to_merchant(
    repo: LedgerRepository,
    customer: Account,
    system: Account,
    merchant: Account,
    fund_customer: None,
) -> None:
    await repo.save_account(merchant)

    credit_merchant = Transfer.create(
        amount=Money(150, Currency.INR), source=customer, destination=merchant
    )
    with pytest.raises(InsufficientFundsError):
        await repo.save_transfer(credit_merchant)

    customer_balance = await repo.get_balance(customer.id)

    assert customer_balance == Money(100, Currency.INR)

    with pytest.raises(TransferNotFoundError):
        await repo.get_transfer(credit_merchant.id)


async def test_valid_transfer_funds_to_merchant(
    repo: LedgerRepository,
    customer: Account,
    system: Account,
    merchant: Account,
    fund_customer: None,
) -> None:
    await repo.save_account(merchant)

    credit_merchant = Transfer.create(
        amount=Money(100, Currency.INR), source=customer, destination=merchant
    )
    await repo.save_transfer(credit_merchant)

    merchant_balance = await repo.get_balance(merchant.id)
    customer_balance = await repo.get_balance(customer.id)

    assert merchant_balance == Money(100, Currency.INR)
    assert customer_balance == Money(0, Currency.INR)


async def test_invalid_transfer_funds_to_unknown_account(
    repo: LedgerRepository, customer: Account, system: Account
) -> None:
    await repo.save_account(system)

    transfer = Transfer.create(
        amount=Money(500, Currency.INR), source=system, destination=customer
    )
    with pytest.raises(AccountNotFoundError):
        await repo.save_transfer(transfer)

    system_balance = await repo.get_balance(system.id)

    assert system_balance == Money(0, Currency.INR)


async def test_invalid_transfer_funds_from_unknown_account(
    repo: LedgerRepository, customer: Account, system: Account
) -> None:
    await repo.save_account(system)

    transfer = Transfer.create(
        amount=Money(500, Currency.INR), source=customer, destination=system
    )
    with pytest.raises(AccountNotFoundError):
        await repo.save_transfer(transfer)

    system_balance = await repo.get_balance(system.id)

    assert system_balance == Money(0, Currency.INR)


async def test_transfer_save_and_get(
    repo: LedgerRepository, customer: Account, system: Account
) -> None:
    await repo.save_account(system)
    await repo.save_account(customer)

    transfer = Transfer.create(
        amount=Money(500, Currency.INR), source=system, destination=customer
    )
    await repo.save_transfer(transfer)

    saved_transfer = await repo.get_transfer(transfer.id)

    assert transfer == saved_transfer

    with pytest.raises(TransferNotFoundError):
        await repo.get_transfer(uuid.uuid4())


async def test_concurrent_transfers(
    repo: LedgerRepository,
    customer: Account,
    system: Account,
    merchant: Account,
    fund_customer: None,
) -> None:
    await repo.save_account(merchant)

    credit_merchant_1 = Transfer.create(
        amount=Money(80, Currency.INR), source=customer, destination=merchant
    )
    credit_merchant_2 = Transfer.create(
        amount=Money(80, Currency.INR), source=customer, destination=merchant
    )
    results = await asyncio.gather(
        repo.save_transfer(credit_merchant_1),
        repo.save_transfer(credit_merchant_2),
        return_exceptions=True,
    )

    success = sum(x is None for x in results)
    fails = sum(1 for x in results if isinstance(x, InsufficientFundsError))
    customer_balance = await repo.get_balance(customer.id)

    assert success == 1
    assert fails == 1
    assert customer_balance == Money(20, Currency.INR)
