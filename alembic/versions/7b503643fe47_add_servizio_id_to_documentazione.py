"""add servizio_id to documentazione

Revision ID: 7b503643fe47
Revises: e1d9460d7855
Create Date: 2025-10-16 23:27:33.605331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7b503643fe47'
down_revision: Union[str, Sequence[str], None] = 'e1d9460d7855'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: aggiungi servizio_id a documentazioni"""
    op.add_column('documentazioni', sa.Column('servizio_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_documentazioni_servizio_id_servizi',
        'documentazioni',
        'servizi',
        ['servizio_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema: rimuovi servizio_id da documentazioni"""
    op.drop_constraint('fk_documentazioni_servizio_id_servizi', 'documentazioni', type_='foreignkey')
    op.drop_column('documentazioni', 'servizio_id')