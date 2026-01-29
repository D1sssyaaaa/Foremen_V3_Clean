"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-25

Создание базовых таблиц системы
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('roles', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('telegram_chat_id', sa.String(50), nullable=True, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_phone', 'users', ['phone'])
    
    # Cost Objects
    op.create_table(
        'cost_objects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('contract_number', sa.String(100), nullable=True),
        sa.Column('contract_amount', sa.Float(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_cost_objects_code', 'cost_objects', ['code'])
    
    # Object-Foremen (many-to-many)
    op.create_table(
        'object_foremen',
        sa.Column('object_id', sa.Integer(), sa.ForeignKey('cost_objects.id', ondelete='CASCADE')),
        sa.Column('foreman_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
    )
    
    # Brigades
    op.create_table(
        'brigades',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('foreman_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Brigade Members
    op.create_table(
        'brigade_members',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brigade_id', sa.Integer(), sa.ForeignKey('brigades.id', ondelete='CASCADE'), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Time Sheets
    op.create_table(
        'time_sheets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brigade_id', sa.Integer(), sa.ForeignKey('brigades.id'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='ЧЕРНОВИК'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_time_sheets_status', 'time_sheets', ['status'])
    
    # Time Sheet Items
    op.create_table(
        'time_sheet_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('time_sheet_id', sa.Integer(), sa.ForeignKey('time_sheets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('brigade_members.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_time_sheet_items_date', 'time_sheet_items', ['date'])
    
    # Equipment Orders
    op.create_table(
        'equipment_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=False),
        sa.Column('foreman_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('equipment_type', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='НОВАЯ'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_equipment_orders_status', 'equipment_orders', ['status'])
    
    # Equipment Costs
    op.create_table(
        'equipment_costs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('equipment_order_id', sa.Integer(), sa.ForeignKey('equipment_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours_worked', sa.Float(), nullable=False),
        sa.Column('hour_rate', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Material Requests
    op.create_table(
        'material_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=False),
        sa.Column('foreman_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='НОВАЯ'),
        sa.Column('urgency', sa.String(20), nullable=False, server_default='обычная'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_material_requests_status', 'material_requests', ['status'])
    
    # Material Request Items
    op.create_table(
        'material_request_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('request_id', sa.Integer(), sa.ForeignKey('material_requests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Material Costs (УПД)
    op.create_table(
        'material_costs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=True),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('supplier_inn', sa.String(20), nullable=True),
        sa.Column('document_number', sa.String(100), nullable=False),
        sa.Column('document_date', sa.Date(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('vat_amount', sa.Float(), nullable=True),
        sa.Column('vat_rate', sa.Float(), nullable=True),
        sa.Column('xml_file_path', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='NEW'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_material_costs_document_number', 'material_costs', ['document_number'])
    
    # Material Cost Items
    op.create_table(
        'material_cost_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('material_cost_id', sa.Integer(), sa.ForeignKey('material_costs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('vat_rate', sa.Float(), nullable=True),
        sa.Column('vat_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # UPD Distribution
    op.create_table(
        'upd_distribution',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('material_cost_id', sa.Integer(), sa.ForeignKey('material_costs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('material_request_id', sa.Integer(), sa.ForeignKey('material_requests.id'), nullable=True),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=True),
        sa.Column('material_cost_item_id', sa.Integer(), sa.ForeignKey('material_cost_items.id'), nullable=True),
        sa.Column('distributed_quantity', sa.Float(), nullable=False),
        sa.Column('distributed_amount', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Cost Entries (агрегированные затраты)
    op.create_table(
        'cost_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cost_object_id', sa.Integer(), sa.ForeignKey('cost_objects.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),  # labor, equipment, materials
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reference_id', sa.Integer(), nullable=True),  # ID связанной записи
        sa.Column('reference_type', sa.String(50), nullable=True),  # тип связанной записи
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_cost_entries_object_date', 'cost_entries', ['cost_object_id', 'date'])
    op.create_index('ix_cost_entries_type', 'cost_entries', ['type'])


def downgrade() -> None:
    op.drop_table('cost_entries')
    op.drop_table('upd_distribution')
    op.drop_table('material_cost_items')
    op.drop_table('material_costs')
    op.drop_table('material_request_items')
    op.drop_table('material_requests')
    op.drop_table('equipment_costs')
    op.drop_table('equipment_orders')
    op.drop_table('time_sheet_items')
    op.drop_table('time_sheets')
    op.drop_table('brigade_members')
    op.drop_table('brigades')
    op.drop_table('object_foremen')
    op.drop_table('cost_objects')
    op.drop_table('users')
