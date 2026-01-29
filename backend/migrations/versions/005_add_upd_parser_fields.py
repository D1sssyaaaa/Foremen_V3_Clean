"""Добавление полей парсера УПД

Revision ID: 005
Revises: 004
Create Date: 2026-01-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic
revision = '005'
down_revision = '004_material_request_fields'
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем поля generator и parsing_issues в material_costs
    with op.batch_alter_table('material_costs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('generator', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('parsing_issues', sa.JSON(), nullable=True))

def downgrade():
    with op.batch_alter_table('material_costs', schema=None) as batch_op:
        batch_op.drop_column('parsing_issues')
        batch_op.drop_column('generator')
