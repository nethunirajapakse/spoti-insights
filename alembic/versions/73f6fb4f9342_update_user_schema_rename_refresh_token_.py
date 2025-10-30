"""Update User schema: rename refresh_token and add app_refresh_token"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '73f6fb4f9342'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename column refresh_token -> spotify_refresh_token
    op.alter_column(
        'users',
        'refresh_token',
        new_column_name='spotify_refresh_token',
        existing_type=sa.String(),
        existing_nullable=False
    )

    # Add new column app_refresh_token
    op.add_column(
        'users',
        sa.Column('app_refresh_token', sa.String(), nullable=True)
    )
    # Add unique constraint
    op.create_unique_constraint(
        'uq_users_app_refresh_token',
        'users',
        ['app_refresh_token']
    )


def downgrade() -> None:
    # Drop the new column and constraint
    op.drop_constraint('uq_users_app_refresh_token', 'users', type_='unique')
    op.drop_column('users', 'app_refresh_token')

    # Rename spotify_refresh_token back to refresh_token
    op.alter_column(
        'users',
        'spotify_refresh_token',
        new_column_name='refresh_token',
        existing_type=sa.String(),
        existing_nullable=False
    )
