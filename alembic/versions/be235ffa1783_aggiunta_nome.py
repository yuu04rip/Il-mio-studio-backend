"""Aggiunta nome

Revision ID: be235ffa1783
Revises: 8115627155af
Create Date: 2025-11-07 18:44:45.478637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'be235ffa1783'
down_revision: Union[str, Sequence[str], None] = '8115627155af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) add columns
    op.add_column('servizi', sa.Column('cliente_nome', sa.String(length=255), nullable=True))
    op.add_column('servizi', sa.Column('cliente_cognome', sa.String(length=255), nullable=True))

    # 2) populate existing rows using clienti -> users join (MySQL syntax). Adjust if your user table is named differently.
    #    This statement will work on MySQL. If you use Postgres, you can adapt: UPDATE servizi SET ... FROM clienti c JOIN users u ON c.utente_id = u.id WHERE servizi.cliente_id = c.id;
    op.execute("""
               UPDATE servizi s
                   JOIN clienti c ON s.cliente_id = c.id
                   JOIN users u ON c.utente_id = u.id
               SET s.cliente_nome = u.nome,
                   s.cliente_cognome = u.cognome
               WHERE u.id IS NOT NULL;
               """)


def downgrade():
    # remove columns
    op.drop_column('servizi', 'cliente_cognome')
    op.drop_column('servizi', 'cliente_nome')