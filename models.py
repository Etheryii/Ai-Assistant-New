"""
Database models for the Etherius AI Support Bot
"""

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4

# Create a SQLAlchemy database instance
from main import db

class Session(db.Model):
    """Model for chat sessions"""
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_identifier = Column(String(64), nullable=True)  # Could be IP, browser fingerprint, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship with messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    @classmethod
    def get_or_create(cls, session_id, user_identifier=None):
        """Get an existing session or create a new one"""
        session = cls.query.filter_by(session_id=session_id).first()
        if not session:
            session = cls(
                session_id=session_id,
                user_identifier=user_identifier
            )
            db.session.add(session)
            db.session.commit()
        return session
    
    def update_last_activity(self):
        """Update the last_activity timestamp"""
        self.last_activity = datetime.datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
        }


class Message(db.Model):
    """Model for chat messages"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('sessions.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    token_count = Column(Integer, nullable=True)
    used_knowledge_base = Column(Boolean, default=False)
    sources = Column(Text, nullable=True)  # JSON string of source documents
    
    # Relationship with session
    session = relationship("Session", back_populates="messages")
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'token_count': self.token_count,
            'used_knowledge_base': self.used_knowledge_base,
            'sources': self.sources
        }


def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid4())