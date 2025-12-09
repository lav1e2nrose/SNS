"""
WebSocket connection manager for real-time chat.
"""
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections for real-time chat.
    """
    
    def __init__(self):
        """Initialize the connection manager with empty connections dict."""
        # Dictionary mapping user_id to list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection to register
            user_id: ID of the user connecting
        """
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
            user_id: ID of the user disconnecting
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: int):
        """
        Send a message to a specific user's active connections.
        
        Args:
            message: Message to send
            user_id: ID of the user to send message to
        """
        if user_id in self.active_connections:
            # Send to all active connections for this user
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Connection is broken, mark for removal
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)


# Global connection manager instance
manager = ConnectionManager()
