"""add user roles

Revision ID: b2c4e6f8a0d2
Revises: a3c9d1e7f4b2
Create Date: 2026-07-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c4e6f8a0d2'
down_revision: Union[str, None] = 'a3c9d1e7f4b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('roles_json', sa.Text(), nullable=False, server_default='["staff"]'),
    )


def downgrade() -> None:
    op.drop_column('users', 'roles_json')
