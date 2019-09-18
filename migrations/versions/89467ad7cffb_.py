"""empty message

Revision ID: 89467ad7cffb
Revises: 1aeea7528fe9
Create Date: 2019-09-18 15:42:40.027707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89467ad7cffb'
down_revision = '1aeea7528fe9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('local_purchase_order', sa.Column('status', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('local_purchase_order', 'status')
    # ### end Alembic commands ###
