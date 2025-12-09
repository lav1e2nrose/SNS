"""
Message model for chat messages with sentiment analysis.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.db.base import Base


class Message(Base):
    """Chat message entity with sentiment score fields."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Read status field
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Sentiment analysis fields
    sentiment_score = Column(Float, nullable=True)  # Overall sentiment score (-1 to 1)
    positive_score = Column(Float, nullable=True)   # Positive sentiment probability
    negative_score = Column(Float, nullable=True)   # Negative sentiment probability
    neutral_score = Column(Float, nullable=True)    # Neutral sentiment probability
    
    __table_args__ = (
        CheckConstraint('sentiment_score >= -1 AND sentiment_score <= 1', name='check_sentiment_range'),
        CheckConstraint('positive_score >= 0 AND positive_score <= 1', name='check_positive_range'),
        CheckConstraint('negative_score >= 0 AND negative_score <= 1', name='check_negative_range'),
        CheckConstraint('neutral_score >= 0 AND neutral_score <= 1', name='check_neutral_range'),
    )
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"
