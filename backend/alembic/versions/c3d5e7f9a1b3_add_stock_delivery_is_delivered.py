"""add stock delivery is_delivered

Revision ID: c3d5e7f9a1b3
Revises: b2c4e6f8a0d2
Create Date: 2026-07-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d5e7f9a1b3'
down_revision: Union[str, None] = 'b2c4e6f8a0d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'stock_deliveries',
        sa.Column('is_delivered', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column('stock_deliveries', 'is_delivered')
