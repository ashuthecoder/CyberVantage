"""
Database models using SQLAlchemy
"""
import datetime
import bcrypt
import secrets
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, LargeBinary, Float
from sqlalchemy.orm import relationship
from api.core.database import Base

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    encrypted_data = Column(LargeBinary, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    tech_confidence = Column(String(50), nullable=True)
    cybersecurity_experience = Column(String(50), nullable=True)
    age_group = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    demographics_completed = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    simulation_responses = relationship("SimulationResponse", back_populates="user")
    simulation_sessions = relationship("SimulationSession", back_populates="user")
    
    def set_password(self, password: str):
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password with bcrypt"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def generate_reset_token(self) -> str:
        """Generate a secure password reset token"""
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        self.password_reset_expires = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        return token
    
    def verify_reset_token(self, token: str) -> bool:
        """Verify password reset token and check expiration"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if datetime.datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token
    
    def clear_reset_token(self):
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None


class SimulationResponse(Base):
    __tablename__ = "simulation_response"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    email_id = Column(Integer, nullable=False)
    is_spam_actual = Column(Boolean, nullable=False)
    user_response = Column(Boolean, nullable=False)
    user_explanation = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="simulation_responses")


class SimulationEmail(Base):
    __tablename__ = "simulation_email"
    
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String(120), nullable=False)
    subject = Column(String(255), nullable=False)
    date = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    is_spam = Column(Boolean, nullable=False)
    is_predefined = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SimulationSession(Base):
    __tablename__ = "simulation_session"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    session_id = Column(String(36), nullable=False)
    phase1_completed = Column(Boolean, default=False)
    phase2_completed = Column(Boolean, default=False)
    phase1_score = Column(Integer, nullable=True)
    phase2_score = Column(Integer, nullable=True)
    avg_phase2_score = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="simulation_sessions")
