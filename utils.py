import uuid
from datetime import datetime, timezone

import html2text
from strip_markdown import strip_markdown


def generate_id_with_timestamp(prefix: str) -> str:
    """
    Generate an ID with the pattern: prefix-YYYYMMDDHHMMSS-uuid

    Args:
        prefix: The prefix for the ID (e.g., 'message', 'conversation')

    Returns:
        Generated ID string
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID for brevity
    return f"{prefix}-{timestamp}-{unique_id}"


def generate_message_id() -> str:
    """Generate a message ID with timestamp."""
    return generate_id_with_timestamp("message")


def generate_conversation_id() -> str:
    """Generate a conversation ID with timestamp."""
    return generate_id_with_timestamp("conversation")


def clean_html_to_plain(html_text: str) -> str:
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    return h.handle(html_text).strip()


def clean_markdown_to_plain(markdown_text: str) -> str:
    return strip_markdown(markdown_text)


def clean_text_to_plain(text: str, text_format: str) -> str:
    if text_format == "html":
        return clean_html_to_plain(text)
    elif text_format == "markdown":
        return clean_markdown_to_plain(text)
    else:
        return text
