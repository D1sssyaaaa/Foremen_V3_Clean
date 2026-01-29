"""Add telegram_notifications table

Revision ID: add_notifications
Revises: add_material_type
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_notifications'
down_revision = '002_add_material_type'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы telegram_notifications
    op.create_table(
        'telegram_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('telegram_message_id', sa.Integer(), nullable=True),
        sa.Column('telegram_chat_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для быстрого поиска
    op.create_index('ix_telegram_notifications_user_id', 'telegram_notifications', ['user_id'])
    op.create_index('ix_telegram_notifications_notification_type', 'telegram_notifications', ['notification_type'])
    op.create_index('ix_telegram_notifications_is_read', 'telegram_notifications', ['is_read'])
    op.create_index('ix_telegram_notifications_status', 'telegram_notifications', ['status'])
    op.create_index('ix_telegram_notifications_created_at', 'telegram_notifications', ['created_at'])
    
    # Композитный индекс для частых запросов
    op.create_index(
        'ix_telegram_notifications_user_unread',
        'telegram_notifications',
        ['user_id', 'is_read', 'created_at']
    )


def downgrade() -> None:
    op.drop_index('ix_telegram_notifications_user_unread', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_created_at', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_status', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_is_read', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_notification_type', table_name='telegram_notifications')
    op.drop_index('ix_telegram_notifications_user_id', table_name='telegram_notifications')
    op.drop_table('telegram_notifications')
