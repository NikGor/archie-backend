import logging

from fastapi import HTTPException

from app.backend import get_database
from app.models import (
    ChatMessage,
    Conversation,
    ConversationRequest,
    ConversationResponse,
    MessageRequest,
    MessageResponse,
)
from utils import clean_text_to_plain, generate_conversation_id, generate_message_id

logger = logging.getLogger(__name__)


class ApiController:
    """Controller layer connecting endpoints to services. Facade pattern implementation."""

    def __init__(self):
        self.db = get_database()

    def create_http_exception(
        self,
        status_code: int,
        detail: str,
        error_code: str,
    ) -> HTTPException:
        """Create standardized HTTP exception with logging."""
        logger.error(f"api_controller_error_{error_code}: \033[31m{detail}\033[0m")
        return HTTPException(status_code=status_code, detail=detail)

    async def get_all_conversations(
        self,
        limit: int = 50,
    ) -> list[Conversation]:
        """Get all conversations with limit."""
        try:
            conversations = await self.db.get_all_conversations(limit=limit)
            logger.info(
                f"api_controller_001: Retrieved \033[33m{len(conversations)}\033[0m conversations"
            )
            return conversations
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to retrieve conversations: {e!s}", "001"
            )

    async def create_new_conversation(
        self,
        request: ConversationRequest,
    ) -> ConversationResponse:
        """Create a new conversation."""
        try:
            conversation = await self.db.create_conversation(
                request.conversation_id, request.title or "New Conversation"
            )
            logger.info(
                f"api_controller_002: Created conv: \033[32m{conversation.conversation_id}\033[0m"
            )

            return ConversationResponse(
                conversation_id=conversation.conversation_id,
                title=conversation.title,
                created_at=conversation.created_at,
            )
        except ValueError as e:
            logger.warning(
                f"api_controller_warn_001: Validation error: \033[31m{e!s}\033[0m"
            )
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to create conversation: {e!s}", "002"
            )

    async def get_conversation_metadata(
        self,
        conversation_id: str,
    ) -> Conversation:
        """Get conversation metadata without messages."""
        try:
            conversation = await self.db.get_conversation_with_messages(conversation_id)
            if not conversation:
                logger.info(
                    f"api_controller_003: Conv not found: \033[36m{conversation_id}\033[0m"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversation {conversation_id} not found",
                )
            # Return conversation without messages
            conversation.messages = []
            return conversation
        except HTTPException:
            raise
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to get conversation: {e!s}", "003"
            )

    async def get_messages_by_conversation(
        self,
        conversation_id: str | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        """Get messages, optionally filtered by conversation_id."""
        try:
            if conversation_id:
                messages = await self.db.get_conversation_history(
                    conversation_id, order_desc=False
                )
                logger.info(
                    f"api_controller_004: Retrieved \033[33m{len(messages)}\033[0m msgs for conv: \033[36m{conversation_id}\033[0m"
                )
                return messages[:limit]
            else:
                # TODO: Implement get_all_messages method in database
                # For now, return empty list
                logger.warning(
                    "api_controller_warn_002: Getting all messages not implemented yet"
                )
                return []
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to retrieve messages: {e!s}", "004"
            )

    async def create_new_message(
        self,
        request: MessageRequest,
    ) -> MessageResponse:
        """Create a new message in a conversation."""
        try:
            logger.info("=== STEP 2: Message Processing ===")
            conversation_id = request.conversation_id

            # If no conversation_id provided, create a new conversation
            if not conversation_id:
                conversation_id = generate_conversation_id()
                await self.db.create_conversation(conversation_id)
                logger.info(
                    f"api_controller_005: Created new conv: \033[32m{conversation_id}\033[0m"
                )
            else:
                # Check if conversation exists
                conversation = await self.db.get_conversation_with_messages(
                    conversation_id
                )
                if not conversation:
                    logger.info(
                        f"api_controller_006: Conv not found: \033[36m{conversation_id}\033[0m"
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Conversation {conversation_id} not found",
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
            await self.db.save_message(message)
            logger.info(
                f"api_controller_007: Created msg: \033[36m{message.message_id}\033[0m, Role: \033[35m{request.role}\033[0m"
            )

            return MessageResponse(
                message_id=message.message_id,
                conversation_id=message.conversation_id,
                created_at=message.created_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to create message: {e!s}", "005"
            )

    async def get_chat_history_yaml(
        self,
        conversation_id: str,
    ) -> tuple[str, dict[str, str]]:
        """Get chat history in YAML format with plain text."""
        try:
            # Get conversation with messages
            conversation = await self.db.get_conversation_with_messages(conversation_id)
            if not conversation:
                logger.info(
                    f"api_controller_008: Conv not found for history: \033[36m{conversation_id}\033[0m"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Conversation {conversation_id} not found",
                )

            # Convert messages to simplified format with plain text
            history_messages = []
            if conversation.messages:
                for message in conversation.messages:
                    # Clean text based on format
                    clean_text = clean_text_to_plain(message.text, message.text_format)

                    message_dict = {"role": message.role, "text": clean_text}

                    # Only include metadata if it exists
                    if message.metadata:
                        message_dict["metadata"] = message.metadata

                    history_messages.append(message_dict)

            logger.info(
                f"api_controller_009: Chat history prepared: \033[33m{len(history_messages)}\033[0m msgs"
            )

            return history_messages, {
                "Content-Disposition": f"inline; filename=chat_history_{conversation_id}.yaml"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise self.create_http_exception(
                500, f"Failed to get chat history: {e!s}", "006"
            )


# Global controller instance
_controller_instance = None


def get_api_controller() -> ApiController:
    """Get global API controller instance."""
    global _controller_instance
    if _controller_instance is None:
        _controller_instance = ApiController()
    return _controller_instance
