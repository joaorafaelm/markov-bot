"""change chat_id column type

Revision ID: 1ecbfa3f2b07
Revises: 9f6345f08863
Create Date: 2018-11-01 19:38:15.539695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ecbfa3f2b07'
down_revision = '9f6345f08863'
branch_labels = None
depends_on = None


def change_column_type(from_, to_):
    with op.batch_alter_table('messages') as batch_op:
        batch_op.add_column(sa.Column('new_chat_id', to_))

    tab = sa.sql.table(
        'messages',
        sa.sql.column('chat_id', from_),
        sa.sql.column('new_chat_id', to_)
    )
    op.execute(
        tab.update().values({
            'new_chat_id': sa.cast(tab.c.chat_id, to_)
        })
    )

    with op.batch_alter_table('messages') as batch_op:
        batch_op.drop_column('chat_id')
        batch_op.alter_column('new_chat_id', new_column_name='chat_id')


def upgrade():
    change_column_type(sa.String, sa.Integer)


def downgrade():
    change_column_type(sa.Integer, sa.String)
