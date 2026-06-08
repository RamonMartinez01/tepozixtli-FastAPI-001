"""cambio_vectorial_a_cog_url

Revision ID: 6204b45e4251
Revises: d64bb05bddd9
Create Date: 2026-06-08 00:32:24.864230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6204b45e4251'
down_revision: Union[str, Sequence[str], None] = 'd64bb05bddd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Agregamos la nueva columna (cog_url)
    op.add_column('indicadores_macro', sa.Column('cog_url', sa.String(length=500), nullable=False, server_default=''))
    
    # 2. Eliminamos la columna vieja (datos_vectoriales)
    op.drop_column('indicadores_macro', 'datos_vectoriales')


def downgrade() -> None:
    # (Opcional, pero buena práctica) El camino de regreso en caso de error
    from sqlalchemy.dialects import postgresql
    op.add_column('indicadores_macro', sa.Column('datos_vectoriales', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_column('indicadores_macro', 'cog_url')