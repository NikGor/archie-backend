from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Literal, Optional

from archie_shared.chat.models import (
    ChatMessage as BaseChatMessage,
    ConversationModel as BaseConversation,
    ChatRequest as BaseChatRequest,
    LllmTrace,
)
from pydantic import BaseModel, Field


# Используем базовые модели из archie_shared, но расширяем их для PostgreSQL


class ChatMessage(BaseChatMessage):
    """Extended chat message model with PostgreSQL-specific fields"""

    # Дополнительные поля для PostgreSQL
    input_tokens: Optional[int] = Field(
        None, description="Number of input tokens used"
    )
    input_cached_tokens: int = Field(
        0, description="Number of cached input tokens used"
    )
    output_tokens: Optional[int] = Field(
        None, description="Number of output tokens generated"
    )
    output_reasoning_tokens: int = Field(
        0, description="Number of reasoning tokens used"
    )
    total_tokens: Optional[int] = Field(
        None, description="Total tokens used"
    )
    total_cost: Optional[Decimal] = Field(
        None, description="Total cost of the request"
    )
    llm_model: Optional[str] = Field(
        None, description="LLM model used for generating this message"
    )

    @property
    def metadata_json(self) -> Optional[dict]:
        """Convert metadata to dict for PostgreSQL JSONB storage"""
        if self.metadata is None:
            return None
        return self.metadata.model_dump() if hasattr(self.metadata, 'model_dump') else self.metadata


class Conversation(BaseConversation):
    """Extended conversation model with PostgreSQL-specific fields"""

    # Дополнительные поля для PostgreSQL
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the conversation was last updated",
    )
    total_input_tokens: int = Field(
        0, description="Total input tokens used in this conversation"
    )
    total_output_tokens: int = Field(
        0, description="Total output tokens generated in this conversation"
    )
    total_tokens: int = Field(
        0, description="Total tokens used in this conversation"
    )
    total_cost: Decimal = Field(
        Decimal("0.000000"), description="Total cost of this conversation"
    )


# Используем ChatRequest из archie_shared как базу для наших запросов
class MessageRequest(BaseChatRequest):
    """Extended message request model"""
    
    metadata_json: Optional[dict] = Field(
        None, description="Additional metadata for the message in JSON format" 
    )


class ConversationRequest(BaseModel):
    """Request model for creating a new conversation"""

    conversation_id: Optional[str] = Field(
        None,
        description="Optional custom conversation ID. If not provided, will be auto-generated",
    )
    title: Optional[str] = Field(
        "New Conversation", description="Title of the conversation"
    )


class ConversationResponse(BaseModel):
    """Response model for conversation creation"""

    conversation_id: str = Field(description="ID of the created conversation")
    title: str = Field(description="Title of the conversation")
    created_at: datetime = Field(
        description="Timestamp when the conversation was created"
    )
    message: str = Field(
        "Conversation created successfully", description="Success message"
    )


class MessageResponse(BaseModel):
    """Response model for message creation"""

    message_id: str = Field(description="ID of the created message")
    conversation_id: str = Field(description="ID of the conversation")
    created_at: datetime = Field(description="Timestamp when the message was created")
    message: str = Field("Message created successfully", description="Success message")


class ChatHistoryMessage(BaseModel):
    """Simplified message model for chat history"""

    role: Literal["user", "assistant", "system"] = Field(
        description="Role of the message sender"
    )
    text: str = Field(description="Content of the message (cleaned to plain text)")
    metadata_json: Optional[dict] = Field(
        None, description="Additional metadata for the message in JSON format"
    )


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoint"""

    messages: List[ChatHistoryMessage] = Field(
        description="List of messages in the conversation"
    )
