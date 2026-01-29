"""Add labor_costs, other_costs, delivery_costs tables

Revision ID: 013
Revises: 012, fb5610ce5e43
Create Date: 2026-01-27 18:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = ('012', 'fb5610ce5e43')
branch_labels = None
depends_on = None


def upgrade():
    # Таблица затрат на рабочих (LaborCost)
    op.create_table(
        'labor_costs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_object_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cost_object_id'], ['cost_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    op.create_index('idx_labor_costs_object', 'labor_costs', ['cost_object_id'])
    op.create_index('idx_labor_costs_date', 'labor_costs', ['date'])
    op.create_index('idx_labor_costs_created_by', 'labor_costs', ['created_by_id'])

    # Таблица иных затрат (OtherCost)
    op.create_table(
        'other_costs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_object_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cost_object_id'], ['cost_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    op.create_index('idx_other_costs_object', 'other_costs', ['cost_object_id'])
    op.create_index('idx_other_costs_date', 'other_costs', ['date'])
    op.create_index('idx_other_costs_created_by', 'other_costs', ['created_by_id'])

    # Таблица затрат на доставку и спецтехнику (DeliveryCost)
    op.create_table(
        'delivery_costs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cost_object_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('cost_type', sa.String(50), nullable=False),  # 'delivery' или 'equipment'
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cost_object_id'], ['cost_objects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
    )
    op.create_index('idx_delivery_costs_object', 'delivery_costs', ['cost_object_id'])
    op.create_index('idx_delivery_costs_date', 'delivery_costs', ['date'])
    op.create_index('idx_delivery_costs_type', 'delivery_costs', ['cost_type'])
    op.create_index('idx_delivery_costs_created_by', 'delivery_costs', ['created_by_id'])


def downgrade():
    # Удаляем индексы и таблицу delivery_costs
    op.drop_index('idx_delivery_costs_created_by', table_name='delivery_costs')
    op.drop_index('idx_delivery_costs_type', table_name='delivery_costs')
    op.drop_index('idx_delivery_costs_date', table_name='delivery_costs')
    op.drop_index('idx_delivery_costs_object', table_name='delivery_costs')
    op.drop_table('delivery_costs')

    # Удаляем индексы и таблицу other_costs
    op.drop_index('idx_other_costs_created_by', table_name='other_costs')
    op.drop_index('idx_other_costs_date', table_name='other_costs')
    op.drop_index('idx_other_costs_object', table_name='other_costs')
    op.drop_table('other_costs')

    # Удаляем индексы и таблицу labor_costs
    op.drop_index('idx_labor_costs_created_by', table_name='labor_costs')
    op.drop_index('idx_labor_costs_date', table_name='labor_costs')
    op.drop_index('idx_labor_costs_object', table_name='labor_costs')
    op.drop_table('labor_costs')
