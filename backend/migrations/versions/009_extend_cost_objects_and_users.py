"""extend cost_objects and users

Revision ID: 009
Revises: 008
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """
    1. Добавляем material_amount и labor_amount в cost_objects
    2. Добавляем status в cost_objects
    3. Добавляем birth_date и profile_photo_url в users
    """
    # 1. Разделение contract_amount на material_amount и labor_amount
    with op.batch_alter_table('cost_objects') as batch_op:
        batch_op.add_column(sa.Column('material_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('labor_amount', sa.Float(), nullable=True))
        
        # Статус объекта: ACTIVE, PREPARATION_TO_CLOSE, CLOSED, ARCHIVE
        batch_op.add_column(sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'))
        batch_op.create_index('idx_cost_objects_status', ['status'])
    
    # 2. Расширение профиля пользователя
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('birth_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('profile_photo_url', sa.String(500), nullable=True))
    
    print("✓ Added material_amount, labor_amount, status to cost_objects")
    print("✓ Added birth_date, profile_photo_url to users")


def downgrade():
    """Rollback changes"""
    with op.batch_alter_table('cost_objects') as batch_op:
        batch_op.drop_index('idx_cost_objects_status')
        batch_op.drop_column('status')
        batch_op.drop_column('labor_amount')
        batch_op.drop_column('material_amount')
    
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('profile_photo_url')
        batch_op.drop_column('birth_date')
