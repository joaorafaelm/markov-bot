"""create messages table

Revision ID: 9f6345f08863
Revises:
Create Date: 2018-11-01 16:47:10.046837

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f6345f08863'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('chat_id', sa.String),
        sa.Column('text', sa.String)
    )


def downgrade():
    op.drop_table('messages')
