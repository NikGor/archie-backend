import os
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
DATABASE_URL = os.getenv("DATABASE_URL")

class Conversation(Base):
    __tablename__ = "ai_assistant_conversation"
    conversation_id = Column(String, primary_key=True)
    title = Column(Text, nullable=False, default="New Conversation")
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_input_cached_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    total_output_reasoning_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "ai_assistant_message"
    message_id = Column(String, primary_key=True)
    conversation_id = Column(
        String, ForeignKey("ai_assistant_conversation.conversation_id"), nullable=False
    )
    role = Column(Text, nullable=False)
    text_format = Column(Text, nullable=False, default="plain")
    text = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    previous_message_id = Column(String, nullable=True)
    model = Column(Text, nullable=True)
    llm_model = Column(Text, nullable=True)
    llm_trace = Column(JSONB, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    input_cached_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=True)
    output_reasoning_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=True)
    total_cost = Column(Float, nullable=True)
    conversation = relationship("Conversation", back_populates="messages")
