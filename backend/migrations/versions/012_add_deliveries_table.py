"""Add deliveries table for self-ordered deliveries

Revision ID: 012
Revises: 011
Create Date: 2026-01-27 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем таблицу deliveries для самостоятельно заказанных доставок
    op.create_table(
        'deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_object_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('delivery_date', sa.Date(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='NEW'),  # NEW, APPROVED, PAID
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cost_object_id'], ['cost_objects.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    
    # Создаем индексы для быстрого поиска
    op.create_index('idx_deliveries_object', 'deliveries', ['cost_object_id'])
    op.create_index('idx_deliveries_status', 'deliveries', ['status'])
    op.create_index('idx_deliveries_created_by', 'deliveries', ['created_by_id'])
    op.create_index('idx_deliveries_date', 'deliveries', ['delivery_date'])


def downgrade():
    # Удаляем индексы
    op.drop_index('idx_deliveries_date', table_name='deliveries')
    op.drop_index('idx_deliveries_created_by', table_name='deliveries')
    op.drop_index('idx_deliveries_status', table_name='deliveries')
    op.drop_index('idx_deliveries_object', table_name='deliveries')
    
    # Удаляем таблицу
    op.drop_table('deliveries')
