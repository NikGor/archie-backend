import os
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    conversation_id = Column(String, primary_key=True)
    title = Column(String, nullable=False, default="New Conversation")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    llm_trace = Column(Text, nullable=True)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    message_id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(String, nullable=False)
    text_format = Column(String, nullable=False, default="plain")
    text = Column(Text, nullable=False)
    message_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    llm_trace = Column(Text, nullable=True)
    conversation = relationship("Conversation", back_populates="messages")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/chat.db")
