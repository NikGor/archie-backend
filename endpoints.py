import logging

import yaml
from fastapi import APIRouter, Query
from fastapi.responses import Response

from api_controller import get_api_controller
from archie_shared.chat.models import (
    ChatMessage,
    ConversationModel as Conversation,
    ConversationRequest,
    ConversationResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()
controller = get_api_controller()


@router.get(
    "/conversations",
    tags=["conversations"],
    summary="Get all conversations",
    description="Retrieve a list of all conversations with their metadata (without messages)",
)
async def get_conversations(
    limit: int = Query(50, description="Maximum number of conversations to return")
) -> list[Conversation]:
    """Get all conversations."""
    return await controller.get_all_conversations(limit=limit)


@router.post(
    "/conversations",
    tags=["conversations"],
    summary="Create a new conversation",
    description="Create a new conversation with an optional custom ID",
)
async def create_conversation(request: ConversationRequest) -> ConversationResponse:
    """Create a new conversation."""
    return await controller.create_new_conversation(request)


@router.get(
    "/conversations/{conversation_id}",
    tags=["conversations"],
    summary="Get conversation metadata",
    description="Get conversation information without messages",
)
async def get_conversation(conversation_id: str) -> Conversation:
    """Get conversation metadata (without messages)."""
    return await controller.get_conversation_metadata(conversation_id)


@router.get(
    "/messages",
    tags=["messages"],
    summary="Get messages",
    description="Get messages from all conversations or filter by specific conversation_id",
)
async def get_messages(
    conversation_id: str = Query(
        None, description="Filter messages by conversation ID"
    ),
    limit: int = Query(50, description="Maximum number of messages to return"),
) -> list[ChatMessage]:
    """Get messages, optionally filtered by conversation_id."""
    return await controller.get_messages_by_conversation(
        conversation_id=conversation_id, limit=limit
    )


@router.post(
    "/messages",
    tags=["messages"],
    summary="Create a new message",
    description="Create a new message in an existing conversation or automatically create a new conversation if conversation_id is not provided",
)
async def create_message(request: ChatMessage) -> MessageResponse:
    """Create a new message in a conversation. If conversation_id is not provided, creates a new conversation."""
    return await controller.create_new_message(request)


@router.get(
    "/chat_history",
    tags=["chat"],
    summary="Get chat history",
    description="Get conversation messages in YAML format with plain text",
)
async def get_chat_history(
    conversation_id: str = Query(description="ID of the conversation to retrieve"),
) -> Response:
    """Get chat history with messages converted to plain text in YAML format."""
    history_messages, headers = await controller.get_chat_history_yaml(conversation_id)

    # Create YAML response
    yaml_data = {"messages": history_messages}
    yaml_content = yaml.dump(
        yaml_data, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

    return Response(
        content=yaml_content,
        media_type="text/yaml",
        headers=headers,
    )
