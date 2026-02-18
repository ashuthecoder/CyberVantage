"""
Database models and helper functions
"""
import datetime
import os
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect, text
from config.app_config import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    encrypted_data = db.Column(db.LargeBinary, nullable=True)  # For sensitive info
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # Admin flag
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    password_reset_token = db.Column(db.String(255), nullable=True)  # For password reset
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    # OTP fields for password reset
    password_reset_otp = db.Column(db.String(6), nullable=True)  # 6-digit OTP
    otp_expires = db.Column(db.DateTime, nullable=True)  # OTP expiration
    otp_attempts = db.Column(db.Integer, default=0)  # Failed OTP attempts counter
    # Demographics fields for personalized learning
    demographics_completed = db.Column(db.Boolean, default=False, nullable=False)
    tech_confidence = db.Column(db.String(50), nullable=True)  # beginner, intermediate, advanced
    cybersecurity_experience = db.Column(db.String(50), nullable=True)  # none, some, experienced

    def set_password(self, password):
        # Hash password with Werkzeug
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        # Verify password with Werkzeug (primary)
        if not self.password_hash:
            return False

        if self.password_hash.startswith('pbkdf2:') or self.password_hash.startswith('scrypt:'):
            return check_password_hash(self.password_hash, password)

        # Backward compatibility for previously-stored bcrypt hashes
        if self.password_hash.startswith('$2a$') or self.password_hash.startswith('$2b$') or self.password_hash.startswith('$2y$'):
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

        return False
    
    def is_admin_user(self):
        """Check if user has admin privileges"""
        return self.is_admin
    
    def generate_reset_token(self):
        """Generate a secure password reset token"""
        import secrets
        import datetime as dt
        
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        self.password_reset_expires = dt.datetime.utcnow() + dt.timedelta(hours=1)
        return token
    
    def verify_reset_token(self, token):
        """Verify password reset token and check expiration"""
        import datetime as dt
        if not self.password_reset_token or not self.password_reset_expires:
            return False
        if dt.datetime.utcnow() > self.password_reset_expires:
            return False
        return self.password_reset_token == token
    
    def clear_reset_token(self):
        """Clear password reset token after use"""
        self.password_reset_token = None
        self.password_reset_expires = None
    
    def generate_otp(self):
        """Generate a 6-digit OTP for password reset"""
        import secrets
        import datetime as dt
        
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.password_reset_otp = otp
        self.otp_expires = dt.datetime.utcnow() + dt.timedelta(minutes=15)  # 15 min expiry
        self.otp_attempts = 0  # Reset attempts counter
        return otp
    
    def verify_otp(self, otp):
        """Verify OTP and check expiration"""
        import datetime as dt
        
        if not self.password_reset_otp or not self.otp_expires:
            return False
        
        # Check if OTP expired
        if dt.datetime.utcnow() > self.otp_expires:
            return False
        
        # Check if too many failed attempts (max 5)
        if self.otp_attempts >= 5:
            return False
        
        # Verify OTP
        if self.password_reset_otp == otp:
            return True
        else:
            self.otp_attempts += 1
            return False
    
    def clear_otp(self):
        """Clear OTP after successful use"""
        self.password_reset_otp = None
        self.otp_expires = None
        self.otp_attempts = 0

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
    """Update database schema to add missing columns."""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            
            # Detect database type
            db_type = db.engine.dialect.name
            print(f"[DB] Database type: {db_type}")
            
            # Check if simulation_email table exists and update
            if inspector.has_table('simulation_email'):
                columns = [col['name'] for col in inspector.get_columns('simulation_email')]
                
                if 'simulation_id' not in columns:
                    print("[DB] Adding simulation_id column to SimulationEmail table")
                    with db.engine.begin() as conn:
                        conn.execute(text("ALTER TABLE simulation_email ADD COLUMN simulation_id TEXT"))
                    print("[DB] Column added successfully")
            
            # Check if user table exists and add demographics fields
            if inspector.has_table('user'):
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                
                if 'demographics_completed' not in user_columns:
                    print("[DB] Adding demographics_completed column to User table")
                    with db.engine.begin() as conn:
                        # Use database-agnostic syntax
                        if db_type == 'postgresql':
                            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN demographics_completed BOOLEAN DEFAULT FALSE NOT NULL"))
                        else:
                            conn.execute(text("ALTER TABLE user ADD COLUMN demographics_completed BOOLEAN DEFAULT 0 NOT NULL"))
                    print("[DB] Column added successfully")
                
                if 'tech_confidence' not in user_columns:
                    print("[DB] Adding tech_confidence column to User table")
                    with db.engine.begin() as conn:
                        if db_type == 'postgresql':
                            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN tech_confidence VARCHAR(50)"))
                        else:
                            conn.execute(text("ALTER TABLE user ADD COLUMN tech_confidence VARCHAR(50)"))
                    print("[DB] Column added successfully")
                
                if 'cybersecurity_experience' not in user_columns:
                    print("[DB] Adding cybersecurity_experience column to User table")
                    with db.engine.begin() as conn:
                        if db_type == 'postgresql':
                            conn.execute(text("ALTER TABLE \"user\" ADD COLUMN cybersecurity_experience VARCHAR(50)"))
                        else:
                            conn.execute(text("ALTER TABLE user ADD COLUMN cybersecurity_experience VARCHAR(50)"))
                    print("[DB] Column added successfully")
            
            return True
    except Exception as e:
        print(f"[DB] Error updating database schema: {str(e)}")
        import traceback
        traceback.print_exc()
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
    log_dir = os.getenv("LOG_DIR", "logs")
    log_file = os.path.join(log_dir, 'simulation_activity.log')
    
    try:
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            log_dir = '/tmp/logs'
            log_file = os.path.join(log_dir, 'simulation_activity.log')
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
        with app.app_context():
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('simulation_email')]
            if 'simulation_id' in columns:
                result = db.session.execute(
                    text("SELECT simulation_id FROM simulation_email WHERE id=:eid"),
                    {"eid": email_id}
                ).fetchone()
                return result[0] if result and result[0] else None
            return None
    except Exception as e:
        print(f"[DB] Error getting simulation_id: {str(e)}")
        return None

def set_simulation_id_for_email(email_id, simulation_id, app):
    """Set the simulation ID for a specific email"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('simulation_email')]
            if 'simulation_id' in columns:
                db.session.execute(
                    text("UPDATE simulation_email SET simulation_id=:sid WHERE id=:eid"),
                    {"sid": simulation_id, "eid": email_id}
                )
                db.session.commit()
                return True
            return False
    except Exception as e:
        print(f"[DB] Error setting simulation_id: {str(e)}")
        return False

def get_emails_for_simulation(simulation_id, app):
    """Get all emails for a specific simulation"""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('simulation_email')]
            if 'simulation_id' in columns:
                result = db.session.execute(
                    text("SELECT id FROM simulation_email WHERE simulation_id=:sid"),
                    {"sid": simulation_id}
                ).fetchall()
                return [row[0] for row in result]
            return []
    except Exception as e:
        print(f"[DB] Error getting emails for simulation: {str(e)}")
        return []

# Function to load predefined emails from JSON file
def load_predefined_emails():
    """Load predefined phishing emails from external JSON file"""
    import json
    try:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'predefined_emails.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            emails = json.load(f)
            # Ensure is_spam is boolean (in case JSON has it as string)
            for email in emails:
                if isinstance(email.get('is_spam'), str):
                    email['is_spam'] = email['is_spam'].lower() == 'true'
            return emails
    except FileNotFoundError:
        print(f"[DB] Warning: predefined_emails.json not found at {json_path}, using empty list")
        return []
    except json.JSONDecodeError as e:
        print(f"[DB] Error parsing predefined_emails.json: {e}")
        return []
    except Exception as e:
        print(f"[DB] Error loading predefined emails: {e}")
        return []

# Load predefined phishing emails from external file
predefined_emails = load_predefined_emails()