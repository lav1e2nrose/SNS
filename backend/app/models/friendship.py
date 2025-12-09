"""
Friendship model for friend relationships with intimacy tracking.
"""
from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, String, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.base import Base


class Friendship(Base):
    """Friend relationship entity with intimacy score fields."""
    
    __tablename__ = "friendships"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Intimacy and relationship tracking
    intimacy_score = Column(Float, default=0.0)  # Overall intimacy score (0 to 100)
    interaction_count = Column(Integer, default=0)  # Number of interactions
    positive_interactions = Column(Integer, default=0)  # Count of positive interactions
    negative_interactions = Column(Integer, default=0)  # Count of negative interactions
    
    __table_args__ = (
        CheckConstraint('intimacy_score >= 0 AND intimacy_score <= 100', name='check_intimacy_range'),
        CheckConstraint('interaction_count >= 0', name='check_interaction_count'),
        CheckConstraint('positive_interactions >= 0', name='check_positive_interactions'),
        CheckConstraint('negative_interactions >= 0', name='check_negative_interactions'),
    )
    
    # Status
    status = Column(String(20), default="pending")  # pending, accepted, blocked
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="friendships_initiated")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friendships_received")
    
    def __repr__(self):
        return f"<Friendship(id={self.id}, user_id={self.user_id}, friend_id={self.friend_id}, intimacy_score={self.intimacy_score})>"
