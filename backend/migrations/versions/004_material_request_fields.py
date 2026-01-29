"""Add fields for material requests tracking

Revision ID: 004_material_request_fields
Revises: 003_add_notifications
Create Date: 2026-01-25 16:50

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_material_request_fields'
down_revision = '003_add_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем недостающие поля в material_requests
    op.add_column('material_requests', sa.Column('comment', sa.Text(), nullable=True, comment='Комментарии к заявке'))
    op.add_column('material_requests', sa.Column('expected_delivery_date', sa.Date(), nullable=True, comment='Ожидаемая дата доставки'))
    op.add_column('material_requests', sa.Column('supplier', sa.String(255), nullable=True, comment='Поставщик'))
    op.add_column('material_requests', sa.Column('order_number', sa.String(100), nullable=True, comment='Номер заказа у поставщика'))
    op.add_column('material_requests', sa.Column('rejection_reason', sa.Text(), nullable=True, comment='Причина отклонения заявки'))
    
    # Добавляем поле rejection_reason в equipment_orders
    op.add_column('equipment_orders', sa.Column('rejection_reason', sa.Text(), nullable=True, comment='Причина отказа в заявке'))


def downgrade() -> None:
    op.drop_column('equipment_orders', 'rejection_reason')
    op.drop_column('material_requests', 'rejection_reason')
    op.drop_column('material_requests', 'order_number')
    op.drop_column('material_requests', 'supplier')
    op.drop_column('material_requests', 'expected_delivery_date')
    op.drop_column('material_requests', 'comment')
