import json
import logging
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from database import Conversation as SQLAConversation
from database import Message as SQLAMessage

from archie_shared.chat.models import ChatMessage, ConversationModel as Conversation

load_dotenv()
logger = logging.getLogger(__name__)


class ChatDatabase:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///data/chat.db")
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"backend_001: Database connection established: \033[36m{self.db_url}\033[0m")

    def _create_db_message_from_chat_message(self, message: ChatMessage) -> SQLAMessage:
        """Create SQLAlchemy Message from ChatMessage."""
        return SQLAMessage(
            message_id=message.message_id or str(uuid.uuid4()),
            conversation_id=message.conversation_id,
            role=message.role,
            text_format=message.text_format,
            text=message.text,
            metadata_json=json.dumps(message.metadata) if message.metadata and not hasattr(message.metadata, 'model_dump') else (message.metadata.model_dump_json() if hasattr(message.metadata, 'model_dump') else None),
            created_at=message.created_at,
            previous_message_id=message.previous_message_id,
            model=message.model,
            llm_model=message.llm_trace.model if message.llm_trace else None,
            input_tokens=message.llm_trace.input_tokens if message.llm_trace else 0,
            input_cached_tokens=message.llm_trace.input_tokens_details.cached_tokens if message.llm_trace and message.llm_trace.input_tokens_details else 0,
            output_tokens=message.llm_trace.output_tokens if message.llm_trace else 0,
            output_reasoning_tokens=message.llm_trace.output_tokens_details.reasoning_tokens if message.llm_trace and message.llm_trace.output_tokens_details else 0,
            total_tokens=message.llm_trace.total_tokens if message.llm_trace else 0,
            total_cost=message.llm_trace.total_cost if message.llm_trace else 0.0,
            llm_trace=message.llm_trace.model_dump_json() if message.llm_trace else None,
        )

    def _update_db_message_from_chat_message(
        self, db_message: SQLAMessage, message: ChatMessage
    ) -> None:
        """Update SQLAlchemy Message from ChatMessage."""
        db_message.conversation_id = message.conversation_id
        db_message.role = message.role
        db_message.text_format = message.text_format
        db_message.text = message.text
        db_message.metadata_json = json.dumps(message.metadata) if message.metadata and not hasattr(message.metadata, 'model_dump') else (message.metadata.model_dump_json() if hasattr(message.metadata, 'model_dump') else None)
        db_message.created_at = message.created_at
        db_message.previous_message_id = message.previous_message_id
        db_message.model = message.model
        db_message.llm_model = message.llm_trace.model if message.llm_trace else None
        db_message.input_tokens = message.llm_trace.input_tokens if message.llm_trace else 0
        db_message.input_cached_tokens = message.llm_trace.input_tokens_details.cached_tokens if message.llm_trace and message.llm_trace.input_tokens_details else 0
        db_message.output_tokens = message.llm_trace.output_tokens if message.llm_trace else 0
        db_message.output_reasoning_tokens = message.llm_trace.output_tokens_details.reasoning_tokens if message.llm_trace and message.llm_trace.output_tokens_details else 0
        db_message.total_tokens = message.llm_trace.total_tokens if message.llm_trace else 0
        db_message.total_cost = message.llm_trace.total_cost if message.llm_trace else 0.0
        db_message.llm_trace = message.llm_trace.model_dump_json() if message.llm_trace else None

    def _create_chat_message_from_db_message(
        self, db_message: SQLAMessage
    ) -> ChatMessage:
        """Create ChatMessage from SQLAlchemy Message."""
        # Parse metadata from JSON
        metadata = None
        if db_message.metadata_json:
            try:
                metadata = json.loads(db_message.metadata_json)
            except json.JSONDecodeError:
                metadata = None

        # Parse llm_trace from JSON
        llm_trace = None
        if db_message.llm_trace:
            try:
                from archie_shared.chat.models import LllmTrace
                llm_trace_data = json.loads(db_message.llm_trace)
                llm_trace = LllmTrace(**llm_trace_data)
            except (json.JSONDecodeError, TypeError):
                llm_trace = None

        return ChatMessage(
            message_id=str(db_message.message_id),
            conversation_id=str(db_message.conversation_id),
            role=db_message.role,
            text_format=db_message.text_format,
            text=db_message.text,
            metadata=metadata,
            created_at=db_message.created_at,
            previous_message_id=str(db_message.previous_message_id) if db_message.previous_message_id else None,
            model=db_message.model,
            llm_trace=llm_trace,
        )

    async def save_message(self, message: ChatMessage) -> None:
        with self.Session() as session:
            if message.conversation_id:
                await self._ensure_conversation_exists(message.conversation_id)

            db_message = session.get(SQLAMessage, message.message_id)
            if db_message:
                self._update_db_message_from_chat_message(db_message, message)
            else:
                db_message = self._create_db_message_from_chat_message(message)
                session.add(db_message)

            session.commit()

    async def save_conversation(self, conversation: Conversation) -> None:
        with self.Session() as session:
            db_conversation = session.get(
                SQLAConversation, conversation.conversation_id
            )
            if db_conversation:
                db_conversation.created_at = conversation.created_at
                db_conversation.updated_at = conversation.updated_at
                db_conversation.title = conversation.title
                db_conversation.total_input_tokens = conversation.total_input_tokens
                db_conversation.total_output_tokens = conversation.total_output_tokens
                db_conversation.total_tokens = conversation.total_tokens
                db_conversation.total_cost = conversation.total_cost
            else:
                db_conversation = SQLAConversation(
                    conversation_id=conversation.conversation_id,
                    title=conversation.title,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    total_input_tokens=conversation.total_input_tokens,
                    total_output_tokens=conversation.total_output_tokens,
                    total_tokens=conversation.total_tokens,
                    total_cost=conversation.total_cost,
                )
                session.add(db_conversation)

            # Save messages within the same session
            if conversation.messages:
                for message in conversation.messages:
                    message.conversation_id = conversation.conversation_id

                    db_message = session.get(SQLAMessage, message.message_id)
                    if db_message:
                        self._update_db_message_from_chat_message(db_message, message)
                    else:
                        db_message = self._create_db_message_from_chat_message(message)
                        session.add(db_message)

            session.commit()

    async def get_conversation_history(
        self, conversation_id: str, order_desc: bool = False
    ) -> list[ChatMessage]:
        with self.Session() as session:
            query = session.query(SQLAMessage).filter(
                SQLAMessage.conversation_id == conversation_id
            )

            if order_desc:
                query = query.order_by(SQLAMessage.created_at.desc())
            else:
                query = query.order_by(SQLAMessage.created_at.asc())

            db_messages = query.all()

            messages = [
                self._create_chat_message_from_db_message(db_msg)
                for db_msg in db_messages
            ]

            return messages

    async def get_conversation_history_for_agent(
        self, conversation_id: str
    ) -> list[dict[str, str]]:
        """Get conversation history in OpenAI API compatible format (chronological order)."""
        with self.Session() as session:
            messages = (
                session.query(SQLAMessage)
                .filter(SQLAMessage.conversation_id == conversation_id)
                .order_by(SQLAMessage.created_at.asc())
                .all()
            )

            return [{"role": msg.role, "content": msg.text} for msg in messages]

    async def _ensure_conversation_exists(self, conversation_id: str) -> None:
        """Ensure conversation record exists."""
        with self.Session() as session:
            existing = (
                session.query(SQLAConversation)
                .filter(SQLAConversation.conversation_id == conversation_id)
                .first()
            )

            if not existing:
                new_conversation = SQLAConversation(
                    conversation_id=conversation_id,
                    title="New Conversation",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_tokens=0,
                    total_cost=0.0,
                )
                session.add(new_conversation)
                session.commit()
                logger.info(
                    f"backend_002: Auto-created conv: \033[32m{conversation_id}\033[0m"
                )

    async def list_conversations(self, limit: int = 50) -> list[str]:
        """List recent conversation IDs."""
        with self.Session() as session:
            conversations = (
                session.query(SQLAConversation.conversation_id)
                .order_by(SQLAConversation.created_at.desc())
                .limit(limit)
                .all()
            )

            return [conv.conversation_id for conv in conversations]

    async def get_all_conversations(self, limit: int = 50) -> list[Conversation]:
        """Get all conversations ordered by creation time (newest first)."""
        with self.Session() as session:
            db_conversations = (
                session.query(SQLAConversation)
                .order_by(SQLAConversation.created_at.desc())
                .limit(limit)
                .all()
            )

            conversations = []
            for db_conv in db_conversations:
                conversation = Conversation(
                    conversation_id=db_conv.conversation_id,
                    title=db_conv.title,
                    created_at=db_conv.created_at,
                    updated_at=db_conv.updated_at,
                    total_input_tokens=db_conv.total_input_tokens,
                    total_output_tokens=db_conv.total_output_tokens,
                    total_tokens=db_conv.total_tokens,
                    total_cost=db_conv.total_cost,
                    messages=[],
                )
                conversations.append(conversation)

            return conversations

    async def get_conversation_with_messages(
        self, conversation_id: str
    ) -> Conversation | None:
        """Get a complete conversation with all its messages."""
        with self.Session() as session:
            # Get conversation info
            db_conversation = (
                session.query(SQLAConversation)
                .filter(SQLAConversation.conversation_id == conversation_id)
                .first()
            )

            if not db_conversation:
                return None

            # Get messages for this conversation (sorted by newest first for API response)
            messages = await self.get_conversation_history(
                conversation_id, order_desc=True
            )

            conversation = Conversation(
                conversation_id=db_conversation.conversation_id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                updated_at=db_conversation.updated_at,
                total_input_tokens=db_conversation.total_input_tokens,
                total_output_tokens=db_conversation.total_output_tokens,
                total_tokens=db_conversation.total_tokens,
                total_cost=db_conversation.total_cost,
                messages=messages,
            )

            return conversation

    async def create_conversation(
        self, conversation_id: str | None = None, title: str = "New Conversation"
    ) -> Conversation:
        """Create a new conversation."""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        created_at = datetime.now(timezone.utc)
        updated_at = created_at

        with self.Session() as session:
            try:
                # Check if conversation already exists
                existing = (
                    session.query(SQLAConversation)
                    .filter(SQLAConversation.conversation_id == conversation_id)
                    .first()
                )

                if existing:
                    raise ValueError(
                        f"Conversation with ID {conversation_id} already exists"
                    )

                # Create new conversation
                new_conversation = SQLAConversation(
                    conversation_id=conversation_id,
                    title=title,
                    created_at=created_at,
                    updated_at=updated_at,
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_tokens=0,
                    total_cost=0.0,
                )
                session.add(new_conversation)
                session.commit()

                logger.info(
                    f"backend_003: Created conv: \033[32m{conversation_id}\033[0m"
                )

                return Conversation(
                    conversation_id=conversation_id,
                    title=title,
                    messages=[],
                    created_at=created_at,
                    updated_at=updated_at,
                    total_input_tokens=0,
                    total_output_tokens=0,
                    total_tokens=0,
                    total_cost=0.0,
                )
            except Exception as e:
                session.rollback()
                raise e

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        with self.Session() as session:
            # Delete messages first (due to foreign key constraint)
            session.query(SQLAMessage).filter(
                SQLAMessage.conversation_id == conversation_id
            ).delete()

            # Delete conversation
            session.query(SQLAConversation).filter(
                SQLAConversation.conversation_id == conversation_id
            ).delete()

            session.commit()
            logger.info(f"backend_004: Deleted conv: \033[31m{conversation_id}\033[0m")


# Global database instance
_db_instance = None


def get_database() -> ChatDatabase:
    """Get global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ChatDatabase()
    return _db_instance
