"""columnas de ancla NEAR en lotes (near_tx_hash, near_block)

Revision ID: 0003_near
Revises: 0002_usuarios
Create Date: 2026-11-11

ATENCIÓN — esta migración es de la migración Stellar → NEAR y debe correr
SOLO contra la base de desarrollo local (SQLite) o contra la base nueva de
NEAR. NO se ejecuta contra Neon de producción: los lotes de producción
conservan sus columnas ``stellar_*`` como archivo.

Las columnas ``stellar_*`` NO se tocan: quedan como histórico de los lotes
del piloto anclados originalmente en Stellar.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_near"
down_revision = "0002_usuarios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # op.add_column basta (SQLite admite ALTER TABLE ... ADD COLUMN desde
    # siempre) y evita que batch_alter_table recree `lotes`, algo innecesario
    # aquí y más riesgoso dado que `eventos` apunta a ella con ON DELETE CASCADE.
    op.add_column("lotes", sa.Column("near_tx_hash", sa.String(length=64), nullable=True))
    op.add_column("lotes", sa.Column("near_block", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lotes", "near_block")
    op.drop_column("lotes", "near_tx_hash")
