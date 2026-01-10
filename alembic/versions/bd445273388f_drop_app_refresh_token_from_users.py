"""drop app_refresh_token from users

Revision ID: bd445273388f
Revises: 73f6fb4f9342
Create Date: 2026-01-11 00:02:55.662361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd445273388f'
down_revision: Union[str, Sequence[str], None] = '73f6fb4f9342'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        'uq_users_app_refresh_token',
        'users',
        type_='unique'
    )
    op.drop_column('users', 'app_refresh_token')



def downgrade() -> None:
    op.add_column(
        'users',
        sa.Column('app_refresh_token', sa.String(), nullable=True)
    )

    op.create_unique_constraint(
        'uq_users_app_refresh_token',
        'users',
        ['app_refresh_token']
    )

