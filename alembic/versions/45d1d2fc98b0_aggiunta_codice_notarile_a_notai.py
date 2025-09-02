"""Aggiunta codice_notarile a notai

Revision ID: 45d1d2fc98b0
Revises: 
Create Date: 2025-08-21 19:50:32.812992

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '45d1d2fc98b0'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Solo aggiunta colonna!
    op.add_column('notai', sa.Column('codice_notarile', sa.Integer(), nullable=False))

def downgrade():
    # Solo rimozione colonna!
    op.drop_column('notai', 'codice_notarile')