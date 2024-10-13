"""Add strava_token_expiry column to User model

Revision ID: add_strava_token_expiry
Revises: 
Create Date: 2024-10-13 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_strava_token_expiry'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('user', sa.Column('strava_token_expiry', sa.DateTime(), nullable=True))

def downgrade():
    op.drop_column('user', 'strava_token_expiry')
