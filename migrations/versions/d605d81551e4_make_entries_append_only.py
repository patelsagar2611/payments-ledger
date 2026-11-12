"""make entries append only

Revision ID: d605d81551e4
Revises: 0c4bc07bd70e
Create Date: 2026-11-12 13:09:29.751663

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d605d81551e4"
down_revision: str | Sequence[str] | None = "0c4bc07bd70e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE FUNCTION entries_reject_change() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'entries are append-only: % is not allowed', TG_OP;
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER entries_no_update_delete
            BEFORE UPDATE OR DELETE ON entries
            FOR EACH ROW
            EXECUTE FUNCTION entries_reject_change()
        """
    )
    op.execute(
        """
        CREATE TRIGGER entries_no_truncate
            BEFORE TRUNCATE ON entries
            FOR EACH STATEMENT
            EXECUTE FUNCTION entries_reject_change()
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER entries_no_update_delete ON entries")
    op.execute("DROP TRIGGER entries_no_truncate ON entries")
    op.execute("DROP FUNCTION entries_reject_change()")
