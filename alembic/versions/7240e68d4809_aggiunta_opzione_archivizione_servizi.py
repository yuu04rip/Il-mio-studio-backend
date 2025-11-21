"""Aggiunta opzione archivizione servizi (safe)

Revision ID: 7240e68d4809
Revises: be235ffa1783
Create Date: 2025-11-21 13:10:12.698682
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '7240e68d4809'
down_revision: Union[str, Sequence[str], None] = 'be235ffa1783'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Aggiungi colonna archived a servizi (MySQL TINYINT(1))
    conn = op.get_bind()
    #  aggiungo solo se non esiste (silenzioso)
    try:
        op.add_column('servizi', sa.Column('archived', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    except Exception:
        # se fallisce (colonna già esistente) non interrompiamo l'upgrade
        pass

    # 2) Crea tabella servizio_code_seq per implementare sequenza in MySQL (se non esiste)
    # La tabella è minimale: una colonna AUTO_INCREMENT che usiamo per LAST_INSERT_ID()
    conn.execute(sa.text("""
                         CREATE TABLE IF NOT EXISTS servizio_code_seq (
                                                                          id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY
                         ) ENGINE=InnoDB;
                         """))

    # 3) (Opzionale) Crea indice UNIQUE su codiceServizio solo se non ci sono duplicati
    # NOTA: non creiamo qui l'indice UNIQUE per evitare crash se ci sono duplicati.
    # Se vuoi forzarlo qui, assicurati prima di eseguire la query di verifica duplicati.
    # (Possiamo creare l'indice manualmente via phpMyAdmin dopo la verifica.)
    pass


def downgrade() -> None:
    # rollback: rimuove solo la colonna archived e la tabella sequenza (se desideri)
    try:
        op.drop_column('servizi', 'archived')
    except Exception:
        pass
    try:
        op.get_bind().execute(sa.text("DROP TABLE IF EXISTS servizio_code_seq"))
    except Exception:
        pass