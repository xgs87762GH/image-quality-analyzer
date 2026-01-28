"""
WebSocket message codes (v2).

All server -> client messages follow:
{ "type": str, "code": str, "message": str, "data": object }
"""

from __future__ import annotations


class MessageCode:
    """WebSocket message codes for unified batch_update channel."""

    # Analysis lifecycle
    ANALYSIS_STARTED = "ANALYSIS_STARTED"
    ANALYSIS_PROGRESS = "ANALYSIS_PROGRESS"
    ANALYSIS_TASK_UPDATE = "ANALYSIS_TASK_UPDATE"
    ANALYSIS_BATCH_UPDATE = "ANALYSIS_BATCH_UPDATE"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"

    # Heartbeat
    HEARTBEAT_RESPONSE = "HEARTBEAT_RESPONSE"
    BATCH_STILL_RUNNING = "BATCH_STILL_RUNNING"
    BATCH_NOT_FOUND = "BATCH_NOT_FOUND"

    # Generic
    ERROR = "ERROR"
    INFO = "INFO"
    SUCCESS = "SUCCESS"

