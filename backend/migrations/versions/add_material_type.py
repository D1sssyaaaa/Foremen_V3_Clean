"""Add material_type to material_requests

Revision ID: add_material_type
Revises: 
Create Date: 2026-01-24

Добавление поля material_type для поддержки инертных материалов
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_material_type'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавить поле material_type
    op.add_column('material_requests', 
        sa.Column('material_type', sa.String(20), nullable=False, server_default='regular')
    )
    
    # Добавить поле delivery_time (желаемое время доставки для инертных)
    op.add_column('material_requests',
        sa.Column('delivery_time', sa.String(50), nullable=True)
    )
    
    # Создать индекс для фильтрации по типу материалов
    op.create_index('idx_material_requests_type', 'material_requests', ['material_type'])


def downgrade() -> None:
    # Удалить индекс
    op.drop_index('idx_material_requests_type', table_name='material_requests')
    
    # Удалить поля
    op.drop_column('material_requests', 'delivery_time')
    op.drop_column('material_requests', 'material_type')
