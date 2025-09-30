import logging
import yaml

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.models import (
    ChatMessage,
    Conversation,
    ConversationRequest,
    ConversationResponse,
    MessageRequest,
    MessageResponse,
    ChatHistoryResponse,
    ChatHistoryMessage,
)
from app.backend import get_database
from utils import generate_message_id, generate_conversation_id, clean_text_to_plain

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
        conversations = await db.get_all_conversations(limit=limit)
        logger.info(f"endpoints_001: Retrieved \033[33m{len(conversations)}\033[0m conversations")
        return conversations
    except Exception as e:
        logger.error(f"endpoints_error_001: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/conversations", tags=["conversations"],
             summary="Create a new conversation",
             description="Create a new conversation with an optional custom ID")
async def create_conversation(
    request: ConversationRequest,
) -> ConversationResponse:
    """Create a new conversation."""
    try:
        conversation = await db.create_conversation(request.conversation_id, request.title or "New Conversation")
        logger.info(f"endpoints_002: Created conv: \033[32m{conversation.conversation_id}\033[0m")

        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            title=conversation.title,
            created_at=conversation.created_at,
        )
    except ValueError as e:
        logger.warning(f"endpoints_warn_001: Validation error: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"endpoints_error_002: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/conversations/{conversation_id}", tags=["conversations"],
            summary="Get conversation metadata",
            description="Get conversation information without messages")
async def get_conversation(conversation_id: str) -> Conversation:
    """Get conversation metadata (without messages)."""
    try:
        conversation = await db.get_conversation_with_messages(conversation_id)
        if not conversation:
            logger.info(f"endpoints_003: Conv not found: \033[36m{conversation_id}\033[0m")
            raise HTTPException(
                status_code=404, detail=f"Conversation {conversation_id} not found"
            )
        # Return conversation without messages
        conversation.messages = []
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"endpoints_error_003: \033[31m{str(e)}\033[0m")
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
            messages = await db.get_conversation_history(conversation_id, order_desc=False)
            logger.info(f"endpoints_004: Retrieved \033[33m{len(messages)}\033[0m msgs for conv: \033[36m{conversation_id}\033[0m")
            return messages[:limit]
        else:
            # TODO: Implement get_all_messages method in database
            # For now, return empty list
            logger.warning("endpoints_warn_002: Getting all messages not implemented yet")
            return []
    except Exception as e:
        logger.error(f"endpoints_error_004: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.post("/messages", tags=["messages"],
             summary="Create a new message",
             description="Create a new message in an existing conversation or automatically create a new conversation if conversation_id is not provided")
async def create_message(request: MessageRequest) -> MessageResponse:
    """Create a new message in a conversation. If conversation_id is not provided, creates a new conversation."""
    try:
        logger.info("=== STEP 2: Message Processing ===")
        conversation_id = request.conversation_id
        
        # If no conversation_id provided, create a new conversation
        if not conversation_id:
            conversation_id = generate_conversation_id()
            new_conversation = await db.create_conversation(conversation_id)
            logger.info(f"endpoints_005: Created new conv: \033[32m{conversation_id}\033[0m")
        else:
            # Check if conversation exists
            conversation = await db.get_conversation_with_messages(conversation_id)
            if not conversation:
                logger.info(f"endpoints_006: Conv not found: \033[36m{conversation_id}\033[0m")
                raise HTTPException(
                    status_code=404, 
                    detail=f"Conversation {conversation_id} not found"
                )
        
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
        await db.save_message(message)
        logger.info(f"endpoints_007: Created msg: \033[36m{message.message_id}\033[0m, Role: \033[35m{request.role}\033[0m")

        return MessageResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            created_at=message.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"endpoints_error_005: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/chat_history", tags=["chat"],
            summary="Get chat history",
            description="Get conversation messages in YAML format with plain text")
async def get_chat_history(
    conversation_id: str = Query(description="ID of the conversation to retrieve")
) -> Response:
    """Get chat history with messages converted to plain text in YAML format."""
    try:
        # Get conversation with messages
        conversation = await db.get_conversation_with_messages(conversation_id)
        if not conversation:
            logger.info(f"endpoints_008: Conv not found for history: \033[36m{conversation_id}\033[0m")
            raise HTTPException(
                status_code=404, 
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Convert messages to simplified format with plain text
        history_messages = []
        if conversation.messages:
            for message in conversation.messages:
                # Clean text based on format
                clean_text = clean_text_to_plain(message.text, message.text_format)
                
                message_dict = {
                    "role": message.role,
                    "text": clean_text
                }
                
                # Only include metadata if it exists
                if message.metadata:
                    message_dict["metadata"] = message.metadata
                    
                history_messages.append(message_dict)
        
        # Create YAML response
        yaml_data = {"messages": history_messages}
        yaml_content = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        logger.info(f"endpoints_009: Chat history exported: \033[33m{len(history_messages)}\033[0m msgs")
        
        return Response(
            content=yaml_content,
            media_type="text/yaml",
            headers={"Content-Disposition": f"inline; filename=chat_history_{conversation_id}.yaml"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"endpoints_error_006: \033[31m{str(e)}\033[0m")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")
