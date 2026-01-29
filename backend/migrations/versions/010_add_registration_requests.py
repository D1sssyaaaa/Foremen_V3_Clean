"""add_registration_requests

Revision ID: 010
Revises: 009
Create Date: 2026-01-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создание таблицы для заявок на регистрацию"""
    op.create_table('registration_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('telegram_chat_id', sa.String(length=50), nullable=False),
        sa.Column('telegram_username', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('processed_by_id', sa.Integer(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['processed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_chat_id')
    )
    op.create_index('ix_registration_requests_id', 'registration_requests', ['id'], unique=False)
    op.create_index('ix_registration_requests_status', 'registration_requests', ['status'], unique=False)


def downgrade() -> None:
    """Удаление таблицы заявок на регистрацию"""
    op.drop_index('ix_registration_requests_status', table_name='registration_requests')
    op.drop_index('ix_registration_requests_id', table_name='registration_requests')
    op.drop_table('registration_requests')
