"""
Unified WebSocket message helpers (v2).

Server -> client message format:
{
  "type": "<business_type>",
  "code": "<message_code>",
  "message": "<english_message>",
  "data": { ... }
}
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def create_unified_message(
    type: str,
    code: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a unified WebSocket message."""
    return {
        "type": type,
        "code": code,
        "message": message,
        "data": data or {},
    }

