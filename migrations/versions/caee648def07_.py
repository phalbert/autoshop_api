"""empty message

Revision ID: caee648def07
Revises: 95bd152c7d30
Create Date: 2019-09-18 04:44:17.573143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caee648def07'
down_revision = '95bd152c7d30'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('accounts', sa.Column('minimum_balance', sa.Numeric(precision=20, scale=2), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('accounts', 'minimum_balance')
    # ### end Alembic commands ###
