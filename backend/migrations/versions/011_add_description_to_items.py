"""add description to material request items

Revision ID: 011
Revises: 010
Create Date: 2026-01-26 11:25:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # Добавляем поле description в material_request_items
    op.add_column('material_request_items', sa.Column('description', sa.Text(), nullable=True))


def downgrade():
    # Удаляем поле description
    op.drop_column('material_request_items', 'description')
