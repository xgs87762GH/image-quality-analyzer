"""WebSocket 模块"""
from flask_socketio import SocketIO

socketio = None


def init_socketio(app):
    """初始化 SocketIO 并绑定到 Flask 应用"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )
    from backend.websocket.analysis_socket import register_analysis_events
    register_analysis_events(socketio)
    return socketio


__all__ = ["socketio", "init_socketio"]
