"""Add password_hash to users table

Revision ID: 9e345ed3a32e
Revises: 
Create Date: 2025-12-10 16:30:04.175760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e345ed3a32e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove password_hash column from users table
    op.drop_column('users', 'password_hash')
