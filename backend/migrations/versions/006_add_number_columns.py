"""add number columns to requests and orders

Revision ID: 006
Revises: 005
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем колонку number в time_sheets
    op.add_column('time_sheets', sa.Column('number', sa.String(50), nullable=True))
    
    # Добавляем колонку number в equipment_orders
    op.add_column('equipment_orders', sa.Column('number', sa.String(50), nullable=True))
    
    # Добавляем колонку number в material_requests
    op.add_column('material_requests', sa.Column('number', sa.String(50), nullable=True))
    
    # Создаем уникальные индексы (но разрешаем NULL, так как старые записи не имеют номеров)
    op.create_index('ix_time_sheets_number', 'time_sheets', ['number'], unique=False)
    op.create_index('ix_equipment_orders_number', 'equipment_orders', ['number'], unique=False)
    op.create_index('ix_material_requests_number', 'material_requests', ['number'], unique=False)


def downgrade():
    op.drop_index('ix_material_requests_number', table_name='material_requests')
    op.drop_index('ix_equipment_orders_number', table_name='equipment_orders')
    op.drop_index('ix_time_sheets_number', table_name='time_sheets')
    
    op.drop_column('material_requests', 'number')
    op.drop_column('equipment_orders', 'number')
    op.drop_column('time_sheets', 'number')
