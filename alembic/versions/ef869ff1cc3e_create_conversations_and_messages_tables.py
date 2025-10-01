from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "ef869ff1cc3e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "conversations",
        "conversation_id",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "conversations",
        "created_at",
        existing_type=sa.TEXT(),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.add_column("messages", sa.Column("message_metadata", sa.Text(), nullable=True))
    op.alter_column(
        "messages",
        "message_id",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "messages",
        "conversation_id",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "role",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "text_format",
        existing_type=sa.TEXT(),
        type_=sa.String(),
        nullable=False,
        existing_server_default=sa.text("'plain'"),
    )
    op.alter_column(
        "messages",
        "created_at",
        existing_type=sa.TEXT(),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
    op.drop_index(op.f("idx_messages_conversation_id"), table_name="messages")
    op.drop_index(op.f("idx_messages_created_at"), table_name="messages")
    op.drop_column("messages", "metadata")


def downgrade() -> None:
    op.add_column("messages", sa.Column("metadata", sa.TEXT(), nullable=True))
    op.create_index(
        op.f("idx_messages_created_at"), "messages", ["created_at"], unique=False
    )
    op.create_index(
        op.f("idx_messages_conversation_id"),
        "messages",
        ["conversation_id"],
        unique=False,
    )
    op.alter_column(
        "messages",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "text_format",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        nullable=True,
        existing_server_default=sa.text("'plain'"),
    )
    op.alter_column(
        "messages",
        "role",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "conversation_id",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "message_id",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        nullable=True,
    )
    op.drop_column("messages", "message_metadata")
    op.alter_column(
        "conversations",
        "created_at",
        existing_type=sa.DateTime(),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
    op.alter_column(
        "conversations",
        "conversation_id",
        existing_type=sa.String(),
        type_=sa.TEXT(),
        nullable=True,
    )
