"""
Friendship management endpoints for adding, removing, and managing friends.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.friendship import Friendship
from backend.app.schemas.friendship import (
    FriendshipCreate,
    FriendshipUpdate,
    FriendshipResponse,
    FriendResponse
)

router = APIRouter()


@router.get("/", response_model=List[FriendResponse])
def get_friends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all friends for the current user.
    
    Returns both friends where the user initiated the request and
    friends where the user received the request.
    """
    # Get friendships where user is the initiator
    friendships_as_user = db.query(
        Friendship, User
    ).join(
        User, User.id == Friendship.friend_id
    ).filter(
        Friendship.user_id == current_user.id
    ).all()
    
    # Get friendships where user is the friend
    friendships_as_friend = db.query(
        Friendship, User
    ).join(
        User, User.id == Friendship.user_id
    ).filter(
        Friendship.friend_id == current_user.id
    ).all()
    
    friends = []
    seen_ids = set()
    
    for friendship, friend in friendships_as_user:
        if friend.id not in seen_ids:
            friends.append(FriendResponse(
                id=friend.id,
                username=friend.username,
                full_name=friend.full_name,
                intimacy_score=friendship.intimacy_score or 0.0,
                status=friendship.status
            ))
            seen_ids.add(friend.id)
    
    for friendship, friend in friendships_as_friend:
        if friend.id not in seen_ids:
            friends.append(FriendResponse(
                id=friend.id,
                username=friend.username,
                full_name=friend.full_name,
                intimacy_score=friendship.intimacy_score or 0.0,
                status=friendship.status
            ))
            seen_ids.add(friend.id)
    
    return friends


@router.post("/", response_model=FriendshipResponse, status_code=status.HTTP_201_CREATED)
def add_friend(
    request: FriendshipCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a friend request to another user.
    """
    # Cannot add yourself as friend
    if request.friend_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as a friend"
        )
    
    # Check if friend exists
    friend = db.query(User).filter(User.id == request.friend_id).first()
    if not friend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if friendship already exists
    existing = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == request.friend_id)) |
        ((Friendship.user_id == request.friend_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Friendship already exists"
        )
    
    # Create new friendship
    friendship = Friendship(
        user_id=current_user.id,
        friend_id=request.friend_id,
        status="pending",
        intimacy_score=0.0,
        interaction_count=0,
        positive_interactions=0,
        negative_interactions=0
    )
    
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    
    return friendship


@router.put("/{friend_id}", response_model=FriendshipResponse)
def update_friendship(
    friend_id: int,
    request: FriendshipUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update friendship status (accept, block, etc.).
    """
    # Find the friendship
    friendship = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )
    
    # Validate status
    valid_statuses = ["pending", "accepted", "blocked"]
    if request.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    friendship.status = request.status
    db.commit()
    db.refresh(friendship)
    
    return friendship


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a friend from your friends list.
    """
    # Find the friendship
    friendship = db.query(Friendship).filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id)) |
        ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if not friendship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friendship not found"
        )
    
    db.delete(friendship)
    db.commit()
    
    return None
