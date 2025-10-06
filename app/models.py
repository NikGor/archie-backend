from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Literal, Optional

from archie_shared.chat.models import (
    ChatMessage,
    ConversationModel as Conversation,
    ChatRequest as BaseChatRequest,
    ConversationRequest,
    ConversationResponse,
    MessageResponse,
    ChatHistoryMessage,
    ChatHistoryResponse,
    LllmTrace,
)
from pydantic import BaseModel, Field


# Используем базовые модели из archie_shared, но расширяем их для PostgreSQL


# ChatMessage импортируется напрямую из archie_shared


# Conversation теперь импортируется напрямую из archie_shared как ConversationModel



# Все Response и Request модели теперь импортируются из archie_shared
