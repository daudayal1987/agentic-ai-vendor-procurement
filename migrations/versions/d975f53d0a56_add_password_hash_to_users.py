"""add password hash to users

Revision ID: d975f53d0a56
Revises: 8dfdb5b36f6d
Create Date: 2026-09-25 14:19:25.079104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd975f53d0a56'
down_revision: Union[str, Sequence[str], None] = '8dfdb5b36f6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the column allowing NULLs temporarily
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    
    # 2. Backfill a default placeholder configuration string for existing entries
    op.execute("UPDATE users SET password_hash = 'CHANGE_ME' WHERE password_hash IS NULL")
    
    # 3. Enforce the structural NOT NULL rule safely
    op.alter_column('users', 'password_hash', nullable=False)

def downgrade() -> None:
    op.drop_column('users', 'password_hash')