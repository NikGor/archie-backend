from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class LllmTrace(BaseModel):
    """LLM usage tracking information"""
    model: str = Field(description="Name of the LLM model used")
    input_tokens: int = Field(description="Number of input tokens consumed")
    output_tokens: int = Field(description="Number of output tokens generated")
    total_tokens: int = Field(description="Total number of tokens used")
    total_cost: float = Field(description="Total cost of the request")


class ChatMessage(BaseModel):
    """Chat message model for all communications"""
    message_id: Optional[str] = Field(
        None, description="Unique identifier for the message"
    )
    role: Literal["user", "assistant", "system"] = Field(
        description="Role of the message sender"
    )
    text_format: Literal["plain", "markdown", "html", "voice"] = Field(
        "plain", description="Format of the message text"
    )
    text: str = Field(description="Content of the message")
    metadata: Optional[dict] = Field(
        None, description="Additional metadata for the message"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the message was created",
    )
    conversation_id: Optional[str] = Field(
        None, description="ID of the conversation this message belongs to"
    )
    llm_trace: Optional[LllmTrace] = Field(
        None, description="LLM usage tracking information"
    )


class Conversation(BaseModel):
    """Conversation model containing multiple messages"""
    conversation_id: str = Field(description="Unique identifier for the conversation")
    messages: list[ChatMessage] = Field(
        description="List of messages in the conversation"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the conversation was created",
    )
    llm_trace: Optional[LllmTrace] = Field(
        None, description="Aggregated LLM usage tracking for the conversation"
    )


class ConversationRequest(BaseModel):
    """Request model for creating a new conversation"""
    conversation_id: Optional[str] = Field(
        None,
        description="Optional custom conversation ID. If not provided, will be auto-generated",
    )


class ConversationResponse(BaseModel):
    """Response model for conversation creation"""
    conversation_id: str = Field(description="ID of the created conversation")
    created_at: datetime = Field(
        description="Timestamp when the conversation was created"
    )
    message: str = Field(
        "Conversation created successfully", description="Success message"
    )


class MessageRequest(BaseModel):
    """Request model for creating a new message"""
    role: Literal["user", "assistant", "system"] = Field(
        description="Role of the message sender"
    )
    text: str = Field(description="Content of the message")
    text_format: Literal["plain", "markdown", "html", "voice"] = Field(
        "plain", description="Format of the message text"
    )
    conversation_id: Optional[str] = Field(None, description="ID of the conversation. If not provided, a new conversation will be created")
    metadata: Optional[dict] = Field(
        None, description="Additional metadata for the message"
    )


class MessageResponse(BaseModel):
    """Response model for message creation"""
    message_id: str = Field(description="ID of the created message")
    conversation_id: str = Field(description="ID of the conversation")
    created_at: datetime = Field(
        description="Timestamp when the message was created"
    )
    message: str = Field(
        "Message created successfully", description="Success message"
    )
