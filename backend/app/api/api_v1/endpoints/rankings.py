"""
Rankings endpoints for friend ranking and relationship insights.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from collections import defaultdict
import math
from datetime import datetime, timedelta, timezone
from backend.app.schemas.ranking import FriendRanking, ActivityPoint, ScorePoint
from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.friendship import Friendship
from backend.app.models.message import Message
router = APIRouter()

SCORE_LOG_SCALE = 10.0  # scales the impact of message frequency (logarithmic)
SCORE_SENTIMENT_SCALE = 20.0  # scales the impact of average sentiment
SCORE_DECIMAL_PLACES = 2


def calculate_score(count: int, sentiment: float) -> float:
    """Calculate capped intimacy-like score for a given day."""
    return (
        min(100.0, math.log(count + 1) * SCORE_LOG_SCALE + (sentiment + 1) * SCORE_SENTIMENT_SCALE)
        if count > 0 else 0.0
    )


def average_sentiment(sentiments: list) -> float:
    """Return average sentiment or 0.0 when empty."""
    return sum(sentiments) / len(sentiments) if sentiments else 0.0

@router.get("/top-friends", response_model=List[FriendRanking])
def get_top_friends(
    # Upper bound keeps payloads manageable and avoids overly heavy queries; typical UI shows 10–50 entries, so 1000 is a safety ceiling to prevent large payloads
    limit: int = Query(0, ge=0, le=1000),
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of friends sorted by their intimacy scores.
    
    This endpoint retrieves friends from the Friendship table and orders them by intimacy score.
    If friendships don't have intimacy scores, it calculates a basic score from message counts
    and sentiment scores.
    
    Args:
        limit: Maximum number of friends to return (0 returns all, default: 0)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of FriendRanking objects sorted by intimacy score (highest first)
        
    Raises:
        HTTPException: If query fails
    """
    try:
        end_date = datetime.now(timezone.utc)
        # Inclusive window covering `days` days ending today
        # Example: days=7 -> includes today plus previous 6 days of history
        start_date = end_date - timedelta(days=days - 1)
        
        # Query friendships where current user is involved
        # Get friendships where current_user is either user or friend
        friendships_as_user = db.query(
            Friendship,
            User
        ).join(
            User, User.id == Friendship.friend_id
        ).filter(
            Friendship.user_id == current_user.id,
            Friendship.status == "accepted"
        ).all()
        
        friendships_as_friend = db.query(
            Friendship,
            User
        ).join(
            User, User.id == Friendship.user_id
        ).filter(
            Friendship.friend_id == current_user.id,
            Friendship.status == "accepted"
        ).all()
        
        # Combine friendships and track unique friends to avoid duplicates
        friend_data: Dict[int, tuple] = {}  # friend_id -> (friendship, friend)
        
        for friendship, friend in friendships_as_user:
            if friend.id not in friend_data:
                friend_data[friend.id] = (friendship, friend)
        
        for friendship, friend in friendships_as_friend:
            if friend.id not in friend_data:
                friend_data[friend.id] = (friendship, friend)
        
        # Process unique friendships
        friend_rankings = []
        friend_ids = list(friend_data.keys())
        friend_ids_set = set(friend_ids)
        
        messages_by_friend: Dict[int, list] = defaultdict(list)
        if friend_ids:
            all_recent_messages = db.query(Message).filter(
                (
                    (Message.sender_id == current_user.id) & (Message.receiver_id.in_(friend_ids))
                ) | (
                    (Message.receiver_id == current_user.id) & (Message.sender_id.in_(friend_ids))
                ),
                Message.created_at.isnot(None),
                Message.created_at >= start_date
            ).all()
            for msg in all_recent_messages:
                other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
                if other_id in friend_ids_set:
                    messages_by_friend[other_id].append(msg)
        
        for friend_id, (friendship, friend) in friend_data.items():
            # Fetch messages in the recent window for trend calculation
            recent_messages = messages_by_friend.get(friend.id, [])
            daily_counts = defaultdict(int)
            daily_sentiments = defaultdict(list)
            
            for msg in recent_messages:
                msg_date = msg.created_at.date()
                daily_counts[msg_date] += 1
                if msg.sentiment_score is not None:
                    daily_sentiments[msg_date].append(msg.sentiment_score)
            
            activity_trend: List[ActivityPoint] = []
            score_trend: List[ScorePoint] = []
            for i in range(days):
                day_date = (start_date + timedelta(days=i)).date()
                count = daily_counts.get(day_date, 0)
                sentiments = daily_sentiments.get(day_date, [])
                avg_sentiment_day = average_sentiment(sentiments)
                daily_score = calculate_score(count, avg_sentiment_day)
                iso_date = day_date.isoformat()
                activity_trend.append(ActivityPoint(date=iso_date, count=count))
                score_trend.append(ScorePoint(date=iso_date, score=round(daily_score, SCORE_DECIMAL_PLACES)))
            
            # Get last message timestamp
            last_message = db.query(Message).filter(
                (
                    (Message.sender_id == current_user.id) & (Message.receiver_id == friend.id)
                ) | (
                    (Message.sender_id == friend.id) & (Message.receiver_id == current_user.id)
                )
            ).order_by(desc(Message.created_at)).first()
            
            last_interaction = last_message.created_at if last_message else None
            
            # If intimacy score is not set or is 0, calculate a basic score from messages
            intimacy_score = friendship.intimacy_score
            if intimacy_score is None or intimacy_score == 0.0:
                # Count messages for this friendship
                message_count = db.query(func.count(Message.id)).filter(
                    (
                        (Message.sender_id == current_user.id) & (Message.receiver_id == friend.id)
                    ) | (
                        (Message.sender_id == friend.id) & (Message.receiver_id == current_user.id)
                    )
                ).scalar() or 0
                
                # Calculate average sentiment
                avg_sentiment = db.query(func.avg(Message.sentiment_score)).filter(
                    (
                        (Message.sender_id == current_user.id) & (Message.receiver_id == friend.id)
                    ) | (
                        (Message.sender_id == friend.id) & (Message.receiver_id == current_user.id)
                    ),
                    Message.sentiment_score.isnot(None)
                ).scalar() or 0.0
                
                # Simple intimacy score calculation using logarithmic scaling and sentiment
                # Capped at 100
                intimacy_score = min(100.0, math.log(message_count + 1) * 10 + (avg_sentiment + 1) * 20)
            
            friend_rankings.append(
                FriendRanking(
                    friend_id=friend.id,
                    username=friend.username,
                    full_name=friend.full_name,
                    intimacy_score=intimacy_score,
                    interaction_count=friendship.interaction_count,
                    positive_interactions=friendship.positive_interactions,
                    negative_interactions=friendship.negative_interactions,
                    last_interaction=last_interaction,
                    activity_trend=activity_trend,
                    score_trend=score_trend
                )
            )
        
        # Sort by intimacy score (descending) and limit (0 means no limit)
        friend_rankings.sort(key=lambda x: x.intimacy_score, reverse=True)
        
        if limit > 0:
            return friend_rankings[:limit]
        return friend_rankings
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve friend rankings: {str(e)}"
        )
