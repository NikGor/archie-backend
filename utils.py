"""
Utility functions for the application
"""

import uuid
from datetime import datetime, timezone


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
    """
    Clean HTML text and convert to plain text.
    
    Args:
        html_text: HTML formatted text
        
    Returns:
        Plain text with HTML tags removed
    """
    import re
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Replace HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, char in html_entities.items():
        clean_text = clean_text.replace(entity, char)
    
    # Clean up extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text


def clean_markdown_to_plain(markdown_text: str) -> str:
    """
    Clean Markdown text and convert to plain text.
    
    Args:
        markdown_text: Markdown formatted text
        
    Returns:
        Plain text with Markdown formatting removed
    """
    import re
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', markdown_text, flags=re.MULTILINE)
    
    # Remove bold and italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url)
    text = re.sub(r'<([^>]+)>', r'\1', text)               # <url>
    
    # Remove images
    text = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', text)
    
    # Remove code blocks and inline code
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)  # ```code```
    text = re.sub(r'`([^`]+)`', r'\1', text)                  # `code`
    
    # Remove horizontal rules
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*{3,}$', '', text, flags=re.MULTILINE)
    
    # Remove blockquotes
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Remove list markers
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)  # unordered lists
    text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)  # ordered lists
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # normalize line breaks
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def clean_text_to_plain(text: str, text_format: str) -> str:
    """
    Clean text based on its format and convert to plain text.
    
    Args:
        text: The text content
        text_format: Format of the text ('plain', 'markdown', 'html', 'voice')
        
    Returns:
        Plain text content
    """
    if text_format == "html":
        return clean_html_to_plain(text)
    elif text_format == "markdown":
        return clean_markdown_to_plain(text)
    else:
        # For 'plain' and 'voice' formats, return as is
        return text
