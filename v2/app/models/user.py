"""
User model for CyberVantage.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """
    User model representing application users.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Learning progress tracking
    learning_progress = db.Column(db.JSON, default=dict)
    
    # Simulation results
    simulation_results = db.Column(db.JSON, default=dict)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
    
    def to_dict(self):
        """
        Convert user object to dictionary for JSON responses.
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'learning_progress': self.learning_progress,
            'simulation_results': self.simulation_results
        }