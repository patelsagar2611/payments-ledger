import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from payments.domain.account import Account, AccountKind
from payments.domain.money import Currency, Money
from payments.domain.transfer import Entry, Transfer, TransferStatus
from payments.ledger.ledger_repository import (
    AccountNotFoundError,
    InsufficientFundsError,
    TransferNotFoundError,
)


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
        async with self._engine.begin() as conn:
            transfer_result = await conn.execute(
                text(
                    """
                    SELECT
                        currency, amount_minor, source_id,
                        destination_id, status, created_at
                    FROM transfers
                    WHERE id = :id
                    """
                ),
                {"id": transfer_id},
            )
            t_row = transfer_result.one_or_none()

            if t_row is None:
                raise TransferNotFoundError(f"transfer {transfer_id} not found.")

            entry_result = await conn.execute(
                text(
                    """
                    SELECT id, account_id, amount_minor, currency, created_at
                    FROM entries
                    WHERE transfer_id = :transfer_id
                    ORDER BY amount_minor
                    """
                ),
                {"transfer_id": transfer_id},
            )
            entry_rows = entry_result.all()

        entries = tuple(
            Entry(
                id=row.id,
                account_id=row.account_id,
                transfer_id=transfer_id,
                amount=Money(row.amount_minor, Currency(row.currency)),
                created_at=row.created_at,
            )
            for row in entry_rows
        )

        return Transfer(
            id=transfer_id,
            amount=Money(t_row.amount_minor, Currency(t_row.currency)),
            source_id=t_row.source_id,
            destination_id=t_row.destination_id,
            status=TransferStatus(t_row.status),
            entries=entries,
            created_at=t_row.created_at,
        )

    async def save_transfer(self, transfer: Transfer) -> None:
        async with self._engine.begin() as conn:
            result = await conn.execute(
                text(
                    """
                    SELECT id, requires_funds
                    FROM accounts
                    WHERE id IN (:source_id, :destination_id)
                    """
                ),
                {
                    "source_id": transfer.source_id,
                    "destination_id": transfer.destination_id,
                },
            )
            accounts = {row.id: row for row in result.all()}
            if transfer.destination_id not in accounts:
                raise AccountNotFoundError(
                    f"account {transfer.destination_id} not found."
                )
            if transfer.source_id not in accounts:
                raise AccountNotFoundError(f"account {transfer.source_id} not found.")
            if accounts[transfer.source_id].requires_funds:
                await conn.execute(
                    text(
                        """
                        SELECT id FROM accounts where id = :id FOR UPDATE
                        """
                    ),
                    {"id": transfer.source_id},
                )
                balance_result = await conn.execute(
                    text(
                        """
                        SELECT COALESCE(sum(amount_minor), 0)::bigint
                        FROM entries
                        WHERE account_id = :id
                        """
                    ),
                    {"id": transfer.source_id},
                )
                balance = balance_result.scalar_one()
                if balance < transfer.amount.amount_minor:
                    raise InsufficientFundsError(
                        f"account {transfer.source_id} has insufficient balance."
                    )

            await conn.execute(
                text(
                    """
                    INSERT INTO transfers
                        (id, amount_minor, currency, source_id, destination_id,
                         status, created_at)
                    VALUES
                        (:id, :amount_minor, :currency, :source_id, :destination_id,
                         :status, :created_at)
                    """
                ),
                {
                    "id": transfer.id,
                    "amount_minor": transfer.amount.amount_minor,
                    "currency": transfer.amount.currency,
                    "source_id": transfer.source_id,
                    "destination_id": transfer.destination_id,
                    "status": transfer.status,
                    "created_at": transfer.created_at,
                },
            )
            await conn.execute(
                text(
                    """
                    INSERT INTO entries
                        (id, transfer_id, account_id, amount_minor, currency,
                         created_at)
                    VALUES
                        (:id, :transfer_id, :account_id, :amount_minor, :currency,
                         :created_at)
                    """
                ),
                [
                    {
                        "id": entry.id,
                        "transfer_id": entry.transfer_id,
                        "account_id": entry.account_id,
                        "amount_minor": entry.amount.amount_minor,
                        "currency": entry.amount.currency,
                        "created_at": entry.created_at,
                    }
                    for entry in transfer.entries
                ],
            )
