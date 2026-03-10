"""Session management for multi-turn conversations."""

import hashlib
import json
from typing import Any


class SessionStore:
    """
    Maps Anthropic API-style conversations to Claude CLI session IDs.

    Uses the first user message as the conversation key, so all turns
    in the same conversation will map to the same CLI session.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, str] = {}

    def get_session_id(self, messages: list[Any]) -> str | None:
        """Gets session ID for multi-turn continuation, None for new conversations."""
        if len(messages) <= 1:
            return None
        # Use first message as conversation key
        conversation_key = self._get_conversation_key(messages)
        return self._sessions.get(conversation_key)

    def update_session(self, messages: list[Any], cli_session_id: str) -> None:
        """Updates the session store after a successful turn."""
        conversation_key = self._get_conversation_key(messages)
        self._sessions[conversation_key] = cli_session_id

    def _get_conversation_key(self, messages: list[Any]) -> str:
        """
        Gets a stable conversation key from the first user message.
        This ensures all turns in the same conversation map to the same session.
        """
        # Find the first user message
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "user":
                return self._hash(msg)

        # Fallback to first message
        if messages:
            return self._hash(messages[0])
        return ""

    def _hash(self, data: Any) -> str:
        """Hash data using MD5."""
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
