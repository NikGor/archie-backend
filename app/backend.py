import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import ChatMessage, Conversation
from database import Base, Conversation as SQLAConversation, Message as SQLAMessage

load_dotenv()
logger = logging.getLogger(__name__)


class ChatDatabase:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///data/chat.db")
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self._init_database()

    def _init_database(self) -> None:
        Base.metadata.create_all(self.engine)
        logger.info(f"backend_001: Database initialized: \033[36m{self.db_url}\033[0m")

    async def save_message(self, message: ChatMessage) -> None:
        with self.Session() as session:
            if message.conversation_id:
                await self._ensure_conversation_exists(message.conversation_id)

            db_message = session.get(SQLAMessage, message.message_id)
            if db_message:
                db_message.conversation_id = message.conversation_id
                db_message.role = message.role
                db_message.text_format = message.text_format
                db_message.text = message.text
                db_message.message_metadata = json.dumps(message.metadata) if message.metadata else None
                db_message.created_at = message.created_at
                db_message.llm_trace = json.dumps(message.llm_trace.dict()) if message.llm_trace else None
            else:
                db_message = SQLAMessage(
                    message_id=message.message_id,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    text_format=message.text_format,
                    text=message.text,
                    message_metadata=json.dumps(message.metadata) if message.metadata else None,
                    created_at=message.created_at,
                    llm_trace=json.dumps(message.llm_trace.dict()) if message.llm_trace else None,
                )
                session.add(db_message)
            
            session.commit()

    async def save_conversation(self, conversation: Conversation) -> None:
        with self.Session() as session:
            db_conversation = session.get(SQLAConversation, conversation.conversation_id)
            if db_conversation:
                db_conversation.created_at = conversation.created_at
                db_conversation.title = conversation.title
                db_conversation.llm_trace = json.dumps(conversation.llm_trace.dict()) if conversation.llm_trace else None
            else:
                db_conversation = SQLAConversation(
                    conversation_id=conversation.conversation_id,
                    title=conversation.title,
                    created_at=conversation.created_at,
                    llm_trace=json.dumps(conversation.llm_trace.dict()) if conversation.llm_trace else None,
                )
                session.add(db_conversation)

            # Save messages within the same session
            if conversation.messages:
                for message in conversation.messages:
                    message.conversation_id = conversation.conversation_id
                    
                    db_message = session.get(SQLAMessage, message.message_id)
                    if db_message:
                        db_message.conversation_id = message.conversation_id
                        db_message.role = message.role
                        db_message.text_format = message.text_format
                        db_message.text = message.text
                        db_message.message_metadata = json.dumps(message.metadata) if message.metadata else None
                        db_message.created_at = message.created_at
                        db_message.llm_trace = json.dumps(message.llm_trace.dict()) if message.llm_trace else None
                    else:
                        db_message = SQLAMessage(
                            message_id=message.message_id,
                            conversation_id=message.conversation_id,
                            role=message.role,
                            text_format=message.text_format,
                            text=message.text,
                            message_metadata=json.dumps(message.metadata) if message.metadata else None,
                            created_at=message.created_at,
                            llm_trace=json.dumps(message.llm_trace.dict()) if message.llm_trace else None,
                        )
                        session.add(db_message)

            session.commit()

    async def get_conversation_history(
        self, conversation_id: str, order_desc: bool = False
    ) -> list[ChatMessage]:
        with self.Session() as session:
            query = session.query(SQLAMessage).filter(SQLAMessage.conversation_id == conversation_id)
            
            if order_desc:
                query = query.order_by(SQLAMessage.created_at.desc())
            else:
                query = query.order_by(SQLAMessage.created_at.asc())
            
            db_messages = query.all()
            
            messages = []
            for db_msg in db_messages:
                metadata = None
                if db_msg.message_metadata:
                    metadata = json.loads(db_msg.message_metadata)
                
                llm_trace = None
                if db_msg.llm_trace:
                    llm_trace = json.loads(db_msg.llm_trace)
                
                message = ChatMessage(
                    message_id=db_msg.message_id,
                    conversation_id=db_msg.conversation_id,
                    role=db_msg.role,
                    text_format=db_msg.text_format,
                    text=db_msg.text,
                    metadata=metadata,
                    created_at=db_msg.created_at,
                    llm_trace=llm_trace,
                )
                messages.append(message)

            return messages

    async def get_conversation_history_for_agent(
        self, conversation_id: str
    ) -> list[dict[str, str]]:
        """Get conversation history in OpenAI API compatible format (chronological order)."""
        with self.Session() as session:
            messages = session.query(SQLAMessage).filter(
                SQLAMessage.conversation_id == conversation_id
            ).order_by(SQLAMessage.created_at.asc()).all()

            return [{"role": msg.role, "content": msg.text} for msg in messages]

    async def _ensure_conversation_exists(
        self, conversation_id: str
    ) -> None:
        """Ensure conversation record exists."""
        with self.Session() as session:
            existing = session.query(SQLAConversation).filter(
                SQLAConversation.conversation_id == conversation_id
            ).first()

            if not existing:
                new_conversation = SQLAConversation(
                    conversation_id=conversation_id,
                    title="New Conversation",
                    created_at=datetime.now(timezone.utc)
                )
                session.add(new_conversation)
                session.commit()
                logger.info(f"backend_002: Auto-created conv: \033[32m{conversation_id}\033[0m")

    async def list_conversations(self, limit: int = 50) -> list[str]:
        """List recent conversation IDs."""
        with self.Session() as session:
            conversations = session.query(SQLAConversation.conversation_id).order_by(
                SQLAConversation.created_at.desc()
            ).limit(limit).all()

            return [conv.conversation_id for conv in conversations]

    async def get_all_conversations(self, limit: int = 50) -> list[Conversation]:
        """Get all conversations ordered by creation time (newest first)."""
        with self.Session() as session:
            db_conversations = session.query(SQLAConversation).order_by(
                SQLAConversation.created_at.desc()
            ).limit(limit).all()

            conversations = []
            for db_conv in db_conversations:
                conversation = Conversation(
                    conversation_id=db_conv.conversation_id,
                    title=db_conv.title,
                    created_at=db_conv.created_at,
                    messages=[]
                )
                conversations.append(conversation)

            return conversations

    async def get_conversation_with_messages(
        self, conversation_id: str
    ) -> Conversation | None:
        """Get a complete conversation with all its messages."""
        with self.Session() as session:
            # Get conversation info
            db_conversation = session.query(SQLAConversation).filter(
                SQLAConversation.conversation_id == conversation_id
            ).first()

            if not db_conversation:
                return None

            # Get messages for this conversation (sorted by newest first for API response)
            messages = await self.get_conversation_history(conversation_id, order_desc=True)

            conversation = Conversation(
                conversation_id=db_conversation.conversation_id,
                title=db_conversation.title,
                created_at=db_conversation.created_at,
                messages=messages
            )

            return conversation

    async def create_conversation(
        self, conversation_id: str | None = None, title: str = "New Conversation"
    ) -> Conversation:
        """Create a new conversation."""
        import uuid

        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        created_at = datetime.now(timezone.utc)

        with self.Session() as session:
            try:
                # Check if conversation already exists
                existing = session.query(SQLAConversation).filter(
                    SQLAConversation.conversation_id == conversation_id
                ).first()
                
                if existing:
                    raise ValueError(f"Conversation with ID {conversation_id} already exists")

                # Create new conversation
                new_conversation = SQLAConversation(
                    conversation_id=conversation_id,
                    title=title,
                    created_at=created_at
                )
                session.add(new_conversation)
                session.commit()
                
                logger.info(f"backend_003: Created new conv: \033[32m{conversation_id}\033[0m")

                return Conversation(
                    conversation_id=conversation_id, 
                    title=title,
                    messages=[], 
                    created_at=created_at
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
