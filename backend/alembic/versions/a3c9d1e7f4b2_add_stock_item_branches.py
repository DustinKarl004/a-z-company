"""add stock item branches

Revision ID: a3c9d1e7f4b2
Revises: e5f6a7b8c9d0
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3c9d1e7f4b2'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_item_branches',
        sa.Column('item_id', sa.String(length=12), sa.ForeignKey('stock_items.id'), primary_key=True),
        sa.Column('branch_id', sa.String(length=12), sa.ForeignKey('branches.id'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('stock_item_branches')
