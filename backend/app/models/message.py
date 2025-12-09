"""
Message model for chat messages with sentiment analysis.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
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
    
    # Sentiment analysis fields
    sentiment_score = Column(Float, nullable=True)  # Overall sentiment score (-1 to 1)
    positive_score = Column(Float, nullable=True)   # Positive sentiment probability
    negative_score = Column(Float, nullable=True)   # Negative sentiment probability
    neutral_score = Column(Float, nullable=True)    # Neutral sentiment probability
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"
