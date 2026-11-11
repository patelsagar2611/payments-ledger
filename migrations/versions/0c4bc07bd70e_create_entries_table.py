"""create entries table

Revision ID: 0c4bc07bd70e
Revises: 85ea05d97f6f
Create Date: 2026-11-12 03:21:52.976562

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c4bc07bd70e"
down_revision: str | Sequence[str] | None = "85ea05d97f6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        ALTER TABLE transfers ADD CONSTRAINT transfers_id_currency_key
            UNIQUE(id, currency)
        """
    )
    op.execute(
        """
        CREATE TABLE entries (
            id              UUID            PRIMARY KEY,
            transfer_id     UUID            NOT NULL,
            account_id      UUID            NOT NULL,
            amount_minor    BIGINT          NOT NULL
                CHECK (amount_minor <> 0),
            currency        CHAR(3)         NOT NULL,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
            CONSTRAINT entries_account_id_fkey
                FOREIGN KEY(account_id, currency) REFERENCES accounts(id, currency),
            CONSTRAINT entries_transfer_id_fkey
                FOREIGN KEY(transfer_id, currency) REFERENCES transfers(id, currency)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_entries_account_created ON entries(account_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_entries_transfer ON entries(transfer_id)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE entries")
    op.execute("ALTER TABLE transfers DROP CONSTRAINT transfers_id_currency_key")
