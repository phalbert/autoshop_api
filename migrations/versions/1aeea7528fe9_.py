"""empty message

Revision ID: 1aeea7528fe9
Revises: caee648def07
Create Date: 2019-09-18 13:00:17.458401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1aeea7528fe9'
down_revision = 'caee648def07'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lpo_item', sa.Column('unit_price', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lpo_item', 'unit_price')
    # ### end Alembic commands ###
