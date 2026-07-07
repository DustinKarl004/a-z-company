"""make sales.item_id nullable for total-sales-only entries

Revision ID: e5f6a7b8c9d0
Revises: a01024772aa2
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'a01024772aa2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sales') as batch_op:
        batch_op.alter_column('item_id', existing_type=sa.String(length=12), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('sales') as batch_op:
        batch_op.alter_column('item_id', existing_type=sa.String(length=12), nullable=False)
