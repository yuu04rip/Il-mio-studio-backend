"""Messaggio

Revision ID: 18f5602bcdd4
Revises: 7240e68d4809
Create Date: 2025-11-23 18:31:07.378109
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '18f5602bcdd4'
down_revision: Union[str, Sequence[str], None] = '7240e68d4809'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Al momento NON facciamo nulla qui.
    # Rimuoviamo i drop_table auto-generati che cancellavano tutto il DB.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # Puoi lasciare vuoto anche questo, o implementare il revert se necessario.
    pass