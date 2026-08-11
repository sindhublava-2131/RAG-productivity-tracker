"""add token_blacklist table

Revision ID: 0002_token_blacklist
Revises: 0001_initial
Create Date: 2026-08-11

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_token_blacklist"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_token_blacklist_id", "token_blacklist", ["id"], unique=False)
    op.create_index("ix_token_blacklist_jti", "token_blacklist", ["jti"], unique=True)
    op.create_index(
        "ix_token_blacklist_user_id", "token_blacklist", ["user_id"], unique=False
    )
    op.create_index(
        "ix_token_blacklist_expires_at", "token_blacklist", ["expires_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_token_blacklist_expires_at", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_user_id", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_jti", table_name="token_blacklist")
    op.drop_index("ix_token_blacklist_id", table_name="token_blacklist")
    op.drop_table("token_blacklist")
