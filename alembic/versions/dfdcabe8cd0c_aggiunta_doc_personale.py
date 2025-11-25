from alembic import op
import sqlalchemy as sa

revision = 'dfdcabe8cd0c'
down_revision = '18f5602bcdd4'
branch_labels = None
depends_on = None

def upgrade():
    # aggiorna l'enum nella colonna 'tipo' della tabella documentazioni
    op.execute("""
               ALTER TABLE `documentazioni`
                   MODIFY COLUMN `tipo` ENUM(
                       'carta_identita','documento_proprieta','passaporto',
                       'tessera_sanitaria','visure_catastali','planimetria',
                       'atto','compromesso','preventivo'
                       ) NOT NULL;
               """)

def downgrade():
    # rollback: rimuovere 'preventivo' ad es. (attenzione ai dati esistenti)
    op.execute("""
               ALTER TABLE `documentazioni`
                   MODIFY COLUMN `tipo` ENUM(
                       'carta_identita','documento_proprieta','passaporto',
                       'tessera_sanitaria','visure_catastali','planimetria',
                       'atto','compromesso'
                       ) NOT NULL;
               """)
