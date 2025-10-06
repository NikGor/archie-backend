"""Add llm_trace field to messages

Revision ID: 4a6ebffe0f74
Revises: d3bd9f810a99
Create Date: 2025-10-06 21:31:48.884131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4a6ebffe0f74'
down_revision: Union[str, Sequence[str], None] = 'd3bd9f810a99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add llm_trace column to ai_assistant_message table
    op.add_column('ai_assistant_message', sa.Column('llm_trace', postgresql.JSONB(astext_type=Text()), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove llm_trace column from ai_assistant_message table
    op.drop_column('ai_assistant_message', 'llm_trace')
