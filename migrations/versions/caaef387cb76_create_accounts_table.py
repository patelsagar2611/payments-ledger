"""create accounts table

Revision ID: caaef387cb76
Revises:
Create Date: 2026-11-11 14:37:02.931237

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "caaef387cb76"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE accounts (
            id              UUID        PRIMARY KEY,
            name            TEXT        NOT NULL,
            currency        CHAR(3)     NOT NULL,
            kind            TEXT        NOT NULL
                CONSTRAINT accounts_kind_check
                CHECK (kind IN ('CUSTOMER', 'MERCHANT', 'SYSTEM')),
            requires_funds  BOOLEAN     NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT accounts_id_currency_key UNIQUE(id, currency)
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE accounts")
