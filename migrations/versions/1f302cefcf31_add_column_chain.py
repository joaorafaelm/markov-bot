"""add column chain

Revision ID: 1f302cefcf31
Revises: 1ecbfa3f2b07
Create Date: 2018-11-02 13:48:55.790486

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f302cefcf31'
down_revision = '9f6345f08863'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('messages') as batch_op:
        batch_op.add_column(sa.Column('chain', sa.String))


def downgrade():
    with op.batch_alter_table('messages') as batch_op:
        batch_op.drop_column('chain')
