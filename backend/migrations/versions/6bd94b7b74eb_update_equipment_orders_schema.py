"""update_equipment_orders_schema

Revision ID: 6bd94b7b74eb
Revises: 006
Create Date: 2026-01-25 19:51:32.529927

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bd94b7b74eb'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем недостающие колонки в equipment_orders
    op.add_column('equipment_orders', sa.Column('supplier', sa.String(255), nullable=True))
    op.add_column('equipment_orders', sa.Column('comment', sa.Text, nullable=True))
    op.add_column('equipment_orders', sa.Column('cancel_reason', sa.Text, nullable=True))
    
    # Удаляем устаревшие колонки
    with op.batch_alter_table('equipment_orders') as batch_op:
        batch_op.drop_column('quantity')
        batch_op.drop_column('description')
        batch_op.drop_column('approved_at')


def downgrade() -> None:
    # Возвращаем устаревшие колонки
    op.add_column('equipment_orders', sa.Column('quantity', sa.Integer, nullable=False, server_default='1'))
    op.add_column('equipment_orders', sa.Column('description', sa.Text, nullable=True))
    op.add_column('equipment_orders', sa.Column('approved_at', sa.DateTime, nullable=True))
    
    # Удаляем новые колонки
    with op.batch_alter_table('equipment_orders') as batch_op:
        batch_op.drop_column('supplier')
        batch_op.drop_column('comment')
        batch_op.drop_column('cancel_reason')
