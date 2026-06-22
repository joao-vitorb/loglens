from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c571e385bfbd"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alert_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("window_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "log_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_log_entries_level"), "log_entries", ["level"], unique=False)
    op.create_index(op.f("ix_log_entries_source"), "log_entries", ["source"], unique=False)
    op.create_index(op.f("ix_log_entries_timestamp"), "log_entries", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_log_entries_timestamp"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_source"), table_name="log_entries")
    op.drop_index(op.f("ix_log_entries_level"), table_name="log_entries")
    op.drop_table("log_entries")
    op.drop_table("alert_rules")
