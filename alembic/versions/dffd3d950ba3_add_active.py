"""Add_active

Revision ID: dffd3d950ba3
Revises: 8d4fbd102b78
Create Date: 2026-05-16 13:30:31.094322

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dffd3d950ba3'
down_revision: Union[str, Sequence[str], None] = '8d4fbd102b78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 🌟 修改這裡：加入 server_default='true'
    op.add_column('email_configs', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('email_configs', 'is_active')
