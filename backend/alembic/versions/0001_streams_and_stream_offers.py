"""streams and stream_offers

Revision ID: 0001
Revises: 
Create Date: 2026-11-22 10:33:03.722793
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('streams',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('campaign_id', sa.Integer(), nullable=False),
    sa.Column('keitaro_stream_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('keitaro_stream_id')
    )
    with op.batch_alter_table('streams', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_streams_campaign_id'), ['campaign_id'], unique=False)

    op.create_table('stream_offers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stream_id', sa.Integer(), nullable=False),
    sa.Column('offer_id', sa.Integer(), nullable=False),
    sa.Column('offer_name', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('share', sa.Integer(), nullable=False),
    sa.Column('pinned', sa.Boolean(), nullable=False),
    sa.Column('base_status', sa.String(), nullable=True),
    sa.Column('base_share', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['stream_id'], ['streams.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('stream_id', 'offer_id')
    )
    with op.batch_alter_table('stream_offers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_stream_offers_stream_id'), ['stream_id'], unique=False)



def downgrade() -> None:
    with op.batch_alter_table('stream_offers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_stream_offers_stream_id'))

    op.drop_table('stream_offers')
    with op.batch_alter_table('streams', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_streams_campaign_id'))

    op.drop_table('streams')
