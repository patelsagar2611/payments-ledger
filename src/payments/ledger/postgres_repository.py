import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from payments.domain.account import Account, AccountKind
from payments.domain.money import Currency, Money
from payments.domain.transfer import Transfer
from payments.ledger.ledger_repository import AccountNotFoundError


class PostgresLedgerRepository:
    """LedgerRepository backed by Postgres.

    Each method borrows its own connection from the engine's pool and runs in
    its own transaction, so concurrent callers never share a connection.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def get_account(self, account_id: uuid.UUID) -> Account:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT id, name, currency, kind, requires_funds, created_at
                    FROM accounts
                    WHERE id = :id
                    """
                ),
                {"id": account_id},
            )
            row = result.one_or_none()

        if row is None:
            raise AccountNotFoundError(f"account {account_id} not found.")

        return Account(
            id=row.id,
            name=row.name,
            currency=Currency(row.currency),
            kind=AccountKind(row.kind),
            requires_funds=row.requires_funds,
            created_at=row.created_at,
        )

    async def save_account(self, account: Account) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(
                text(
                    """
                    INSERT INTO accounts
                        (id, name, currency, kind, requires_funds, created_at)
                    VALUES
                        (:id, :name, :currency, :kind, :requires_funds, :created_at)
                    """
                ),
                {
                    "id": account.id,
                    "name": account.name,
                    "currency": account.currency,
                    "kind": account.kind,
                    "requires_funds": account.requires_funds,
                    "created_at": account.created_at,
                },
            )

    async def get_balance(self, account_id: uuid.UUID) -> Money:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT
                        currency,
                        (SELECT COALESCE(SUM(amount_minor), 0)
                        FROM entries
                        WHERE account_id = :id)::bigint AS balance
                    FROM accounts
                    WHERE id = :id
                    """
                ),
                {"id": account_id},
            )
            row = result.one_or_none()

        if row is None:
            raise AccountNotFoundError(f"account {account_id} not found.")

        return Money(row.balance, Currency(row.currency))

    async def get_transfer(self, transfer_id: uuid.UUID) -> Transfer:
        raise NotImplementedError

    async def save_transfer(self, transfer: Transfer) -> None:
        raise NotImplementedError
