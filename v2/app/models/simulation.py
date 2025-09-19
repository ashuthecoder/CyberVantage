"""
Simulation models for CyberVantage.
"""
from app.models.user import db
from datetime import datetime

class Simulation(db.Model):
    """
    Model for tracking user simulation sessions.
    """
    __tablename__ = 'simulations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    phase = db.Column(db.Integer, default=1)  # 1 = Phase 1 (predefined), 2 = Phase 2 (AI-generated)
    completion_count = db.Column(db.Integer, default=0)
    active_email = db.Column(db.Text, nullable=True)  # JSON string of the current email
    emails_generated = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')  # active, completed, abandoned
    
    # Relationships
    results = db.relationship('SimulationResult', backref='simulation', lazy=True)
    
    def __repr__(self):
        return f'<Simulation {self.id} for User {self.user_id}>'

class SimulationResult(db.Model):
    """
    Model for tracking user responses to simulation emails.
    """
    __tablename__ = 'simulation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    simulation_id = db.Column(db.Integer, db.ForeignKey('simulations.id'), nullable=False)
    email_data = db.Column(db.Text, nullable=False)  # JSON string of the email
    user_assessment = db.Column(db.Boolean, nullable=False)  # True = phishing, False = legitimate
    actual_assessment = db.Column(db.Boolean, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    user_explanation = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)  # AI feedback on user explanation
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SimulationResult {self.id} for Simulation {self.simulation_id}>'