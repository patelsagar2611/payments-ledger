"""create transfers table

Revision ID: 85ea05d97f6f
Revises: caaef387cb76
Create Date: 2026-11-11 14:57:02.831027

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "85ea05d97f6f"
down_revision: str | Sequence[str] | None = "caaef387cb76"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE TABLE transfers (
            id              UUID        PRIMARY KEY,
            amount_minor    BIGINT      NOT NULL
                CHECK (amount_minor > 0),
            currency        CHAR(3)     NOT NULL,
            source_id       UUID        NOT NULL,
            destination_id  UUID        NOT NULL,
            status          TEXT        NOT NULL
                CONSTRAINT transfers_status_check
                CHECK (status IN ('COMPLETED', 'REVERSED')),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT transfers_accounts_check
                CHECK(source_id <> destination_id),
            CONSTRAINT transfers_source_id_fkey
                FOREIGN KEY(source_id, currency) REFERENCES accounts(id, currency),
            CONSTRAINT transfers_destination_id_fkey
                FOREIGN KEY(destination_id, currency) REFERENCES accounts(id, currency)
        )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE transfers")
