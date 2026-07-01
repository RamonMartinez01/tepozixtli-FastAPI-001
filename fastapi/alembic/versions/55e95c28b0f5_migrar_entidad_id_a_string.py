"""migrar_entidad_id_a_string

Revision ID: 55e95c28b0f5
Revises: 6204b45e4251
Create Date: 2026-07-01 06:04:17.471399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '55e95c28b0f5'
down_revision: Union[str, None] = '6204b45e4251'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Como vamos a cambiar de tipo UUID a String, la forma más robusta y segura
    # en PostgreSQL es usar una ejecución SQL directa con conversión de tipo (CAST).
    op.execute("ALTER TABLE indicadores_macro ALTER COLUMN entidad_id TYPE VARCHAR(10) USING entidad_id::varchar;")

def downgrade() -> None:
    # Para revertir, casteamos el string de vuelta a UUID.
    # (Nota: Esto fallaría si el string contiene algo como '02001', 
    # pero es el estándar para declarar la reversión).
    op.execute("ALTER TABLE indicadores_macro ALTER COLUMN entidad_id TYPE UUID USING entidad_id::uuid;")