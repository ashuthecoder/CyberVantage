"""
Database models and helper functions
"""
import datetime
import sqlite3
import os
from passlib.hash import bcrypt
from config.app_config import db

def get_actual_database_path():
    """Get the actual database path that SQLAlchemy is using"""
    return str(db.engine.url).replace('sqlite:///', '')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    encrypted_data = db.Column(db.LargeBinary, nullable=True)  # For sensitive info

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

class SimulationResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_id = db.Column(db.Integer, nullable=False)  # 1-5 for predefined, random IDs for AI-generated
    is_spam_actual = db.Column(db.Boolean, nullable=False)  # The correct answer
    user_response = db.Column(db.Boolean, nullable=False)  # User's yes/no response
    user_explanation = db.Column(db.Text, nullable=True)  # User's explanation (for AI emails)
    ai_feedback = db.Column(db.Text, nullable=True)  # AI's evaluation of the user's explanation
    score = db.Column(db.Integer, nullable=True)  # Score given by AI (if applicable)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('simulation_responses', lazy=True))

class SimulationEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)  # The email content
    is_spam = db.Column(db.Boolean, nullable=False)  # Whether it's a spam email
    is_predefined = db.Column(db.Boolean, nullable=False)  # Whether it's predefined or AI-generated
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # simulation_id managed via raw SQL (optional column)

class SimulationSession(db.Model):
    """Tracks individual simulation attempts/sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(36), nullable=False)  # UUID for session tracking
    phase1_completed = db.Column(db.Boolean, default=False)
    phase2_completed = db.Column(db.Boolean, default=False)
    phase1_score = db.Column(db.Integer, nullable=True)  # Score out of 5
    phase2_score = db.Column(db.Integer, nullable=True)  # Score out of 5  
    avg_phase2_score = db.Column(db.Float, nullable=True)  # Average AI score out of 10
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('simulation_sessions', lazy=True))

# Database helper functions
def update_database_schema(app):
    """Add the simulation_id column to the SimulationEmail table if it exists and the column is missing."""
    try:
        # Use the actual database path from SQLAlchemy engine
        db_path = get_actual_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure the table exists before attempting to alter it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
        table = cursor.fetchone()
        if not table:
            print("[DB] simulation_email table does not exist yet. Skipping ALTER until db.create_all() runs.")
            conn.close()
            return True

        # Check existing columns
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'simulation_id' not in columns:
            print("[DB] Adding simulation_id column to SimulationEmail table")
            cursor.execute("ALTER TABLE simulation_email ADD COLUMN simulation_id TEXT")
            conn.commit()
            print("[DB] Column added successfully")
        else:
            print("[DB] simulation_id column already exists")

        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Error updating database schema: {str(e)}")
        return False

def group_responses_into_sessions(responses):
    """
    Group simulation responses into logical sessions based on timing and email patterns.
    A session is considered complete when there are responses to 5 phase1 emails (1-5)
    and optionally 5 phase2 emails (>5).
    """
    if not responses:
        return []
    
    sessions = []
    current_session = []
    
    # Sort by creation time
    responses = sorted(responses, key=lambda r: r.created_at)
    
    for i, response in enumerate(responses):
        if not current_session:
            # Start new session
            current_session = [response]
        else:
            # Check if this response belongs to current session or starts a new one
            last_response = current_session[-1]
            time_gap = response.created_at - last_response.created_at
            
            # New session if gap > 2 hours OR if we see email_id=1 again (restart)
            if time_gap.total_seconds() > 7200 or (response.email_id == 1 and any(r.email_id == 1 for r in current_session)):
                # Finalize current session
                sessions.append(current_session)
                current_session = [response]
            else:
                current_session.append(response)
    
    # Add final session
    if current_session:
        sessions.append(current_session)
    
    # Calculate statistics for each session
    session_stats = []
    for session in sessions:
        phase1_responses = [r for r in session if r.email_id <= 5]
        phase2_responses = [r for r in session if r.email_id > 5]
        
        phase1_correct = sum(1 for r in phase1_responses if r.user_response == r.is_spam_actual)
        phase2_correct = sum(1 for r in phase2_responses if r.user_response == r.is_spam_actual)
        
        phase2_scores = [r.score for r in phase2_responses if r.score is not None]
        avg_phase2_score = sum(phase2_scores) / len(phase2_scores) if phase2_scores else None
        
        session_stats.append({
            'responses': session,
            'started_at': min(r.created_at for r in session),
            'completed_at': max(r.created_at for r in session),
            'phase1_total': len(phase1_responses),
            'phase1_correct': phase1_correct,
            'phase2_total': len(phase2_responses), 
            'phase2_correct': phase2_correct,
            'avg_phase2_score': avg_phase2_score,
            'total_responses': len(session),
            'is_complete': len(phase1_responses) >= 5  # At least completed phase 1
        })
    
    return session_stats

def log_simulation_event(user_id, username, event_type, session_id=None, details=None):
    """
    Log simulation events to a dedicated log file.
    event_type: 'started', 'completed', 'phase1_completed', 'phase2_completed'
    """
    log_dir = 'logs'
    log_file = os.path.join(log_dir, 'simulation_activity.log')
    
    try:
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"[{timestamp}] USER:{username}(ID:{user_id}) SESSION:{session_id} EVENT:{event_type}"
        
        if details:
            log_entry += f" DETAILS:{details}"
        
        log_entry += "\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"[LOG] Error writing simulation log: {str(e)}")

def get_simulation_id_for_email(email_id, app):
    """Get the simulation ID for a specific email"""
    try:
        db_path = get_actual_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'simulation_id' in columns:
            cursor.execute("SELECT simulation_id FROM simulation_email WHERE id=?", (email_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        conn.close()
        return None
    except Exception as e:
        print(f"[DB] Error getting simulation_id: {str(e)}")
        return None

def set_simulation_id_for_email(email_id, simulation_id, app):
    """Set the simulation ID for a specific email"""
    try:
        db_path = get_actual_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'simulation_id' in columns:
            cursor.execute("UPDATE simulation_email SET simulation_id=? WHERE id=?", (simulation_id, email_id))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False
    except Exception as e:
        print(f"[DB] Error setting simulation_id: {str(e)}")
        return False

def get_emails_for_simulation(simulation_id, app):
    """Get all emails for a specific simulation"""
    try:
        db_path = get_actual_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'simulation_id' in columns:
            cursor.execute("SELECT id FROM simulation_email WHERE simulation_id=?", (simulation_id,))
            emails = cursor.fetchall()
            conn.close()
            return [email[0] for email in emails]
        conn.close()
        return []
    except Exception as e:
        print(f"[DB] Error getting emails for simulation: {str(e)}")
        return []

# Predefined phishing emails
predefined_emails = [
    {
        "id": 1,
        "sender": "security@paypa1.com",
        "subject": "Your account has been compromised",
        "date": "August 12, 2025",
        "content": """
            <p>Dear Valued Customer,</p>
            <p>We have detected unusual activity on your account. Your account has been temporarily limited.</p>
            <p>Please click the link below to verify your information and restore full access to your account:</p>
            <p><a href="https://paypa1-secure.com/verify">https://paypa1-secure.com/verify</a></p>
            <p>If you don't verify your account within 24 hours, it will be permanently suspended.</p>
            <p>Thank you,<br>PayPal Security Team</p>
        """,
        "is_spam": True
    },
    {
        "id": 2,
        "sender": "amazondelivery@amazon-shipment.net",
        "subject": "Your Amazon package delivery failed",
        "date": "August 10, 2025",
        "content": """
            <p>Dear Customer,</p>
            <p>We attempted to deliver your package today but were unable to complete the delivery.</p>
            <p>To reschedule your delivery, please confirm your details by clicking here:</p>
            <p><a href="http://amazon-redelivery.net/confirm">Confirm Delivery Details</a></p>
            <p>Your package will be returned to our warehouse if you don't respond within 3 days.</p>
            <p>Amazon Delivery Services</p>
        """,
        "is_spam": True
    },
    {
        "id": 3,
        "sender": "notifications@linkedin.com",
        "subject": "You have 3 new connection requests",
        "date": "August 11, 2025",
        "content": """
            <p>Hi there,</p>
            <p>You have 3 new connection requests waiting for your response.</p>
            <p>- Jane Smith, Senior Developer at Tech Solutions</p>
            <p>- Michael Johnson, Project Manager at Enterprise Inc.</p>
            <p>- Sarah Williams, HR Director at Global Innovations</p>
            <p>Log in to your LinkedIn account to view and respond to these requests.</p>
            <p>The LinkedIn Team</p>
        """,
        "is_spam": False
    },
    {
        "id": 4,
        "sender": "microsoft365@outlook.cn",
        "subject": "Your Microsoft password will expire today",
        "date": "August 13, 2025",
        "content": """
            <p>URGENT: Your Microsoft password will expire in 12 hours</p>
            <p>To ensure uninterrupted access to your Microsoft 365 services, please update your password immediately.</p>
            <p>Click here to update: <a href="http://ms-365-password-portal.cn/reset">Reset Password Now</a></p>
            <p>Ignore this message at your own risk. Account lockout will occur at midnight.</p>
            <p>Microsoft 365 Support Team</p>
        """,
        "is_spam": True
    },
    {
        "id": 5,
        "sender": "newsletter@nytimes.com",
        "subject": "Your Weekly News Digest from The New York Times",
        "date": "August 9, 2025",
        "content": """
            <h2>This Week's Top Stories</h2>
            <p>• Global Climate Summit Concludes with New Emission Targets</p>
            <p>• Tech Companies Announce Collaboration on AI Safety Standards</p>
            <p>• Medical Breakthrough: New Treatment Shows Promise for Alzheimer's</p>
            <p>• Sports: Championship Finals Set After Dramatic Semifinals</p>
            <p>• Arts: Review of the Summer's Most Anticipated Exhibition</p>
            <p>Read these stories and more on our website. Not interested in these emails? <a href="https://nytimes.com/newsletter/unsubscribe">Unsubscribe here</a>.</p>
            <p>© 2025 The New York Times Company</p>
        """,
        "is_spam": False
    }
]