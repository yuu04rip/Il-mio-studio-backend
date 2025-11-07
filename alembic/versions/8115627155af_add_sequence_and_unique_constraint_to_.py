"""Add sequence and unique constraint to codiceServizio

Revision ID: 8115627155af
Revises: 7b503643fe47
Create Date: 2025-11-07 16:49:05.433700
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '8115627155af'
down_revision: Union[str, Sequence[str], None] = '7b503643fe47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE_NAME = 'servizi'
COL_NAME = 'codiceServizio'
UNIQUE_NAME = 'servizi_codice_unico'
SEQ_NAME = 'servizio_code_seq'

def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = inspect(bind)

    # 1) Postgres: create sequence if not exists
    if dialect == 'postgresql':
        op.execute(f'CREATE SEQUENCE IF NOT EXISTS {SEQ_NAME} START 1;')

        # alter column type in Postgres
        # note: use quoted identifier if needed (handled by SQLAlchemy op.alter_column)
        op.alter_column(TABLE_NAME, COL_NAME,
                        existing_type=sa.String(),
                        type_=sa.String(64),
                        existing_nullable=True)

        # add unique constraint if not exists (Postgres supports IF NOT EXISTS for ALTER TABLE ADD CONSTRAINT only via raw SQL from 9.6? safe approach: check constraint list)
        # we'll check constraints via inspector
        existing_constraints = {c['name'] for c in inspector.get_unique_constraints(TABLE_NAME)}
        if UNIQUE_NAME not in existing_constraints:
            op.create_unique_constraint(UNIQUE_NAME, TABLE_NAME, [COL_NAME])

    # 2) MySQL: no sequences; modify column type via MODIFY and create UNIQUE INDEX if missing
    elif dialect in ('mysql', 'mariadb'):
        # modify column type
        # use raw SQL MODIFY to ensure compatibility
        op.execute(f'ALTER TABLE `{TABLE_NAME}` MODIFY `{COL_NAME}` VARCHAR(64);')

        # inspect indexes to see if unique index/constraint exists
        existing_indexes = {idx['name'] for idx in inspector.get_indexes(TABLE_NAME)}
        # MySQL will often name the unique index same as constraint name if created via DDL, but we use UNIQUE_NAME as our desired name
        if UNIQUE_NAME not in existing_indexes:
            # create unique index
            op.create_index(UNIQUE_NAME, TABLE_NAME, [COL_NAME], unique=True)

    else:
        # fallback: try generic alter_column and create unique constraint if not exists
        op.alter_column(TABLE_NAME, COL_NAME,
                        existing_type=sa.String(),
                        type_=sa.String(64),
                        existing_nullable=True)
        existing_constraints = {c['name'] for c in inspector.get_unique_constraints(TABLE_NAME)}
        if UNIQUE_NAME not in existing_constraints:
            try:
                op.create_unique_constraint(UNIQUE_NAME, TABLE_NAME, [COL_NAME])
            except Exception:
                # best-effort fallback: raw SQL
                op.execute(f'ALTER TABLE {TABLE_NAME} ADD CONSTRAINT {UNIQUE_NAME} UNIQUE ({COL_NAME});')


def downgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = inspect(bind)

    # remove unique constraint / index if exists
    if dialect == 'postgresql':
        existing_constraints = {c['name'] for c in inspector.get_unique_constraints(TABLE_NAME)}
        if UNIQUE_NAME in existing_constraints:
            op.drop_constraint(UNIQUE_NAME, TABLE_NAME, type_='unique')
        # drop sequence if exists
        op.execute(f'DROP SEQUENCE IF EXISTS {SEQ_NAME};')

    elif dialect in ('mysql', 'mariadb'):
        existing_indexes = {idx['name'] for idx in inspector.get_indexes(TABLE_NAME)}
        if UNIQUE_NAME in existing_indexes:
            op.drop_index(UNIQUE_NAME, TABLE_NAME)
        # no sequence to drop in MySQL

    else:
        # generic
        existing_constraints = {c['name'] for c in inspector.get_unique_constraints(TABLE_NAME)}
        if UNIQUE_NAME in existing_constraints:
            op.drop_constraint(UNIQUE_NAME, TABLE_NAME, type_='unique')
