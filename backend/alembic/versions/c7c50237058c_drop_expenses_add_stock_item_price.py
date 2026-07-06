"""drop expenses add stock item price

Revision ID: c7c50237058c
Revises: 1e9b77c2922b
Create Date: 2026-07-06 11:27:07.841056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7c50237058c'
down_revision: Union[str, None] = '1e9b77c2922b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('expenses')
    op.add_column('stock_items', sa.Column('price', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('stock_items', 'price')
    op.create_table('expenses',
    sa.Column('branch_id', sa.String(length=12), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.Column('amount', sa.Float(), nullable=False),
    sa.Column('created_by_id', sa.String(length=12), nullable=False),
    sa.Column('id', sa.String(length=12), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
