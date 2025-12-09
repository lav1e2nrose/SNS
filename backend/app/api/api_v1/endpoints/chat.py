"""
Chat endpoints for real-time messaging and history.
"""
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
import json
from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.message import Message
from backend.app.models.friendship import Friendship
from backend.app.schemas.message import MessageResponse
from backend.app.services.connection_manager import manager
from backend.app.core.security import decode_access_token

router = APIRouter()


@router.websocket("/ws/{friend_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    friend_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat between users.
    
    Args:
        websocket: WebSocket connection
        friend_id: ID of the friend to chat with
        token: JWT token for authentication (passed as query parameter)
        db: Database session
    """
    # Authenticate user from token
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify friend exists
    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from WebSocket
            data = await websocket.receive_text()
            
            # Parse message content
            try:
                message_data = json.loads(data)
                content = message_data.get("content", "")
            except json.JSONDecodeError:
                # If not JSON, treat entire message as content
                content = data
            
            if not content:
                continue
            
            # Save message to database with placeholder sentiment scores
            message = Message(
                sender_id=user_id,
                receiver_id=friend_id,
                content=content,
                is_read=False,
                sentiment_score=0.0,  # Placeholder for Phase 3
                positive_score=0.0,   # Placeholder for Phase 3
                negative_score=0.0,   # Placeholder for Phase 3
                neutral_score=0.0     # Placeholder for Phase 3
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            
            # Update friendship interaction count
            friendship = db.query(Friendship).filter(
                or_(
                    and_(Friendship.user_id == user_id, Friendship.friend_id == friend_id),
                    and_(Friendship.user_id == friend_id, Friendship.friend_id == user_id)
                )
            ).first()
            
            if friendship:
                friendship.interaction_count = (friendship.interaction_count or 0) + 1
                # Update intimacy score based on interaction count (simple increment)
                # More sophisticated calculation happens in the analysis endpoint
                if friendship.intimacy_score is None:
                    friendship.intimacy_score = 0.0
                # Small increment for each message, capped at 100
                friendship.intimacy_score = min(100.0, friendship.intimacy_score + 0.1)
                db.commit()
            
            # Prepare response message
            response_data = {
                "id": message.id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "content": message.content,
                "is_read": message.is_read,
                "created_at": message.created_at.isoformat(),
                "sentiment_score": message.sentiment_score
            }
            
            # Send message to friend if they're connected
            await manager.send_personal_message(
                json.dumps(response_data),
                friend_id
            )
            
            # Echo back to sender for confirmation
            await websocket.send_text(json.dumps(response_data))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)
        raise


@router.get("/chat/{friend_id}", response_model=List[MessageResponse])
def get_chat_history(
    friend_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation history between current user and a friend.
    
    Args:
        friend_id: ID of the friend
        skip: Number of messages to skip (for pagination)
        limit: Maximum number of messages to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of messages in the conversation
        
    Raises:
        HTTPException: If friend does not exist
    """
    # Verify friend exists
    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend not found"
        )
    
    # Get messages between current user and friend (both directions)
    messages = db.query(Message).filter(
        (
            (Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)
        ) | (
            (Message.sender_id == friend_id) & (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Reverse to get chronological order (oldest first)
    messages.reverse()
    
    return messages


@router.put("/chat/{friend_id}/read", response_model=dict)
def mark_messages_as_read(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all messages from a friend as read.
    
    Args:
        friend_id: ID of the friend
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Number of messages marked as read
        
    Raises:
        HTTPException: If friend does not exist
    """
    # Verify friend exists
    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend not found"
        )
    
    # Update all unread messages from friend to current user
    updated_count = db.query(Message).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    
    return {"marked_as_read": updated_count}


@router.get("/chat/{friend_id}/unread", response_model=dict)
def get_unread_count(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get count of unread messages from a friend.
    
    Args:
        friend_id: ID of the friend
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Count of unread messages
        
    Raises:
        HTTPException: If friend does not exist
    """
    # Verify friend exists
    friend = db.query(User).filter(User.id == friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend not found"
        )
    
    # Count unread messages from friend to current user
    unread_count = db.query(Message).filter(
        Message.sender_id == friend_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()
    
    return {"unread_count": unread_count}
