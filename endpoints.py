import logging

from fastapi import APIRouter, HTTPException, Query

from app.models import (
    ChatMessage,
    Conversation,
    ConversationRequest,
    ConversationResponse,
    MessageRequest,
    MessageResponse,
)
from app.backend import get_database
from utils import generate_message_id, generate_conversation_id

logger = logging.getLogger(__name__)
router = APIRouter()
db = get_database()



@router.get("/conversations", tags=["conversations"], 
            summary="Get all conversations",
            description="Retrieve a list of all conversations with their metadata (without messages)")
async def get_conversations(
    limit: int = Query(50, description="Maximum number of conversations to return")
) -> list[Conversation]:
    """Get all conversations."""
    try:
        logger.info(f"Fetching conversations with limit: {limit}")
        conversations = db.get_all_conversations(limit=limit)
        logger.info(f"Successfully retrieved {len(conversations)} conversations")
        return conversations
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/conversations", tags=["conversations"],
             summary="Create a new conversation",
             description="Create a new conversation with an optional custom ID")
async def create_conversation(
    request: ConversationRequest,
) -> ConversationResponse:
    """Create a new conversation."""
    try:
        logger.info(
            f"Creating new conversation with ID: {request.conversation_id or 'auto-generated'}"
        )
        conversation = db.create_conversation(request.conversation_id)
        logger.info(f"Successfully created conversation {conversation.conversation_id}")

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            created_at=conversation.created_at,
        )
    except ValueError as e:
        logger.warning(f"Validation error creating conversation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/conversations/{conversation_id}", tags=["conversations"],
            summary="Get conversation metadata",
            description="Get conversation information without messages")
async def get_conversation(conversation_id: str) -> Conversation:
    """Get conversation metadata (without messages)."""
    try:
        logger.info(f"Fetching conversation metadata: {conversation_id}")
        conversation = db.get_conversation_with_messages(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail=f"Conversation {conversation_id} not found"
            )
        # Return conversation without messages
        conversation.messages = []
        logger.info(f"Successfully retrieved conversation metadata: {conversation_id}")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching conversation {conversation_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/messages", tags=["messages"],
            summary="Get messages",
            description="Get messages from all conversations or filter by specific conversation_id")
async def get_messages(
    conversation_id: str = Query(None, description="Filter messages by conversation ID"),
    limit: int = Query(50, description="Maximum number of messages to return")
) -> list[ChatMessage]:
    """Get messages, optionally filtered by conversation_id."""
    try:
        if conversation_id:
            logger.info(f"Fetching messages for conversation: {conversation_id}")
            messages = db.get_conversation_history(conversation_id, order_desc=False)
            logger.info(f"Successfully retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages[:limit]
        else:
            logger.info("Fetching all messages")
            # TODO: Implement get_all_messages method in database
            # For now, return empty list
            logger.warning("Getting all messages not implemented yet")
            return []
    except Exception as e:
        logger.error(f"Error fetching messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/messages", tags=["messages"],
             summary="Create a new message",
             description="Create a new message in an existing conversation or automatically create a new conversation if conversation_id is not provided")
async def create_message(request: MessageRequest) -> MessageResponse:
    """Create a new message in a conversation. If conversation_id is not provided, creates a new conversation."""
    try:
        conversation_id = request.conversation_id
        
        # If no conversation_id provided, create a new conversation
        if not conversation_id:
            conversation_id = generate_conversation_id()
            new_conversation = db.create_conversation(conversation_id)
            logger.info(f"Created new conversation: {conversation_id}")
        else:
            # Check if conversation exists
            conversation = db.get_conversation_with_messages(conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Conversation {conversation_id} not found"
                )
            logger.info(f"Using existing conversation: {conversation_id}")
        
        # Create message
        message = ChatMessage(
            message_id=generate_message_id(),
            role=request.role,
            text=request.text,
            text_format=request.text_format,
            conversation_id=conversation_id,
            metadata=request.metadata,
        )
        
        # Save message to database
        db.save_message(message)
        logger.info(f"Successfully created message {message.message_id}")

        return MessageResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            created_at=message.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")
