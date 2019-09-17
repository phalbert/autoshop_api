"""empty message

Revision ID: 95bd152c7d30
Revises: 
Create Date: 2019-09-17 16:42:07.708748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95bd152c7d30'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('entries_credit_idx', table_name='entries')
    op.drop_index('entries_debit_idx', table_name='entries')
    op.add_column('expense', sa.Column('credit_status', sa.String(length=50), nullable=True))
    op.add_column('expense', sa.Column('on_credit', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('expense', 'on_credit')
    op.drop_column('expense', 'credit_status')
    op.create_index('entries_debit_idx', 'entries', ['debit'], unique=False)
    op.create_index('entries_credit_idx', 'entries', ['credit'], unique=False)
    # ### end Alembic commands ###
