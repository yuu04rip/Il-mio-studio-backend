"""add is_deleted to servizi

Revision ID: d1f33e1b0038
Revises: 45d1d2fc98b0
Create Date: 2025-09-15 21:42:47.548971

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1f33e1b0038'
down_revision = '45d1d2fc98b0'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('servizi', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade():
    op.drop_column('servizi', 'is_deleted')