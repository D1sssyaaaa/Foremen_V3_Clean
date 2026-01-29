"""add delivery_address to material_requests

Revision ID: 008
Revises: 6bd94b7b74eb
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008'
down_revision = '6bd94b7b74eb'
branch_labels = None
depends_on = None


def upgrade():
    """Add delivery_address column to material_requests"""
    op.add_column('material_requests', sa.Column('delivery_address', sa.Text(), nullable=True))
    print("Added delivery_address column to material_requests")


def downgrade():
    """Remove delivery_address column from material_requests"""
    op.drop_column('material_requests', 'delivery_address')
