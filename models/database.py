"""
Database models and helper functions
"""
import datetime
import sqlite3
import os
import bcrypt
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
    # New fields for government schemes personalization
    location = db.Column(db.String(100), nullable=True)  # User's location (e.g., "Delhi", "Mumbai")
    role = db.Column(db.String(50), nullable=True)  # User's role (e.g., "student", "farmer", "entrepreneur")

    def set_password(self, password):
        # Hash password with bcrypt
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        # Verify password with bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
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

class GovernmentScheme(db.Model):
    """Model to store government schemes information"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # education, employment, business, agriculture, etc.
    target_audience = db.Column(db.String(100), nullable=False)  # student, farmer, entrepreneur, women, etc.
    location = db.Column(db.String(100), nullable=True)  # Specific state/city or "all" for national schemes
    eligibility = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    how_to_apply = db.Column(db.Text, nullable=True)
    official_url = db.Column(db.String(500), nullable=True)
    source_website = db.Column(db.String(200), nullable=True)  # e.g., "myscheme.gov.in"
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Database helper functions
def update_database_schema(app):
    """Add missing columns to existing tables."""
    try:
        # Connect directly to the SQLite database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print("[DB] Database file does not exist yet. Skipping schema update.")
            return True
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Update simulation_email table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
        table = cursor.fetchone()
        if table:
            # Check existing columns
            cursor.execute("PRAGMA table_info(simulation_email)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'simulation_id' not in columns:
                print("[DB] Adding simulation_id column to SimulationEmail table")
                cursor.execute("ALTER TABLE simulation_email ADD COLUMN simulation_id TEXT")
                conn.commit()
                print("[DB] Column added successfully")

        # Update user table for government schemes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        user_table = cursor.fetchone()
        if user_table:
            cursor.execute("PRAGMA table_info(user)")
            user_columns = [col[1] for col in cursor.fetchall()]
            
            if 'location' not in user_columns:
                print("[DB] Adding location column to User table")
                cursor.execute("ALTER TABLE user ADD COLUMN location VARCHAR(100)")
                conn.commit()
                
            if 'role' not in user_columns:
                print("[DB] Adding role column to User table")
                cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(50)")
                conn.commit()
                print("[DB] User table columns added successfully")
        
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
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
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
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
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
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
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

def populate_sample_schemes():
    """Populate the database with sample government schemes data"""
    try:
        # Check if schemes already exist
        existing_schemes = GovernmentScheme.query.first()
        if existing_schemes:
            print("[DB] Sample schemes already exist, skipping population")
            return True
            
        sample_schemes = [
            {
                "title": "PM Scholarship Scheme for Central Armed Police Forces and Assam Rifles",
                "description": "The Prime Minister's Scholarship Scheme provides financial assistance to the wards/widows of Central Armed Police Forces and Assam Rifles personnel for pursuing higher education.",
                "category": "education",
                "target_audience": "student",
                "location": "all",
                "eligibility": "Children/widows of CAPF and Assam Rifles personnel who have died/disabled in line of duty. Must have scored 60% or more in 12th standard.",
                "benefits": "Up to ₹3,000 per month for boys and ₹3,600 per month for girls for graduation and post-graduation courses.",
                "how_to_apply": "Apply online through National Scholarship Portal (scholarships.gov.in). Required documents include death/disability certificate, mark sheets, income certificate.",
                "official_url": "https://scholarships.gov.in/",
                "source_website": "scholarships.gov.in"
            },
            {
                "title": "Delhi Student Scholarship Scheme",
                "description": "Scholarship scheme by Government of Delhi for meritorious students from economically weaker sections to pursue higher education.",
                "category": "education",
                "target_audience": "student",
                "location": "Delhi",
                "eligibility": "Delhi domicile, family income less than ₹6 lakh per annum, minimum 60% marks in previous qualifying examination.",
                "benefits": "₹5,000 to ₹12,000 per annum depending on course and category.",
                "how_to_apply": "Apply through Delhi government education portal. Submit income certificate, domicile certificate, and academic records.",
                "official_url": "https://www.edudel.nic.in/",
                "source_website": "edudel.nic.in"
            },
            {
                "title": "Pradhan Mantri Mudra Yojana (PMMY)",
                "description": "Credit facility for micro and small enterprises and individuals to set up their business activities.",
                "category": "business",
                "target_audience": "entrepreneur",
                "location": "all",
                "eligibility": "Any citizen of India who has a business plan for non-farm sector income generating activity such as manufacturing, trading or service sector.",
                "benefits": "Loans up to ₹10 lakh without any guarantee or collateral. Three categories: Shishu (up to ₹50,000), Kishore (₹50,001 to ₹5 lakh), Tarun (₹5,00,001 to ₹10 lakh).",
                "how_to_apply": "Apply through any bank, NBFC, or MFI. Submit business plan, identity proof, address proof, category certificate if applicable.",
                "official_url": "https://www.mudra.org.in/",
                "source_website": "mudra.org.in"
            },
            {
                "title": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
                "description": "Skill development scheme to provide training and certification to youth for employment and entrepreneurship.",
                "category": "employment",
                "target_audience": "job-seeker",
                "location": "all",
                "eligibility": "Indian citizen between 18-35 years, preference to school/college dropouts, unemployed youth.",
                "benefits": "Free skill training with monetary reward up to ₹8,000 on successful completion. Placement assistance provided.",
                "how_to_apply": "Register through PMKVY portal or visit nearest training center. Documents required: Aadhaar card, bank account details.",
                "official_url": "https://www.pmkvyofficial.org/",
                "source_website": "pmkvyofficial.org"
            },
            {
                "title": "Stand Up India Scheme",
                "description": "Facilitate bank loans between ₹10 lakh and ₹1 crore to SC/ST and women entrepreneurs for setting up new enterprises.",
                "category": "business",
                "target_audience": "women",
                "location": "all",
                "eligibility": "SC/ST and/or Women entrepreneur, above 18 years, loan for greenfield project in manufacturing, services or trading sector.",
                "benefits": "Bank loan between ₹10 lakh to ₹1 crore with repayment period up to 7 years. Handholding support for project preparation and approvals.",
                "how_to_apply": "Apply through Stand-Up India portal or visit scheduled commercial bank branch. Business plan and required documents to be submitted.",
                "official_url": "https://www.standupmitra.in/",
                "source_website": "standupmitra.in"
            },
            {
                "title": "PM-KISAN Scheme",
                "description": "Direct income support of ₹6,000 per year to small and marginal farmer families across India.",
                "category": "agriculture",
                "target_audience": "farmer",
                "location": "all",
                "eligibility": "Small and marginal farmer families owning cultivable land up to 2 hectares.",
                "benefits": "₹6,000 per year in three equal installments of ₹2,000 each, directly transferred to farmer's bank account.",
                "how_to_apply": "Register through PM-KISAN portal or Common Service Centers. Land records, Aadhaar card, and bank account details required.",
                "official_url": "https://pmkisan.gov.in/",
                "source_website": "pmkisan.gov.in"
            },
            {
                "title": "Delhi Mukhyamantri Mahila Samman Yojana",
                "description": "Monthly financial assistance to women in Delhi to promote women empowerment and economic independence.",
                "category": "women",
                "target_audience": "women", 
                "location": "Delhi",
                "eligibility": "Women residents of Delhi, age 18-60 years, family income less than ₹3 lakh per annum.",
                "benefits": "₹1,000 per month direct cash transfer to women's bank accounts.",
                "how_to_apply": "Apply through Delhi government portal or designated centers. Submit identity proof, address proof, income certificate.",
                "official_url": "https://edistrict.delhigovt.nic.in/",
                "source_website": "delhi.gov.in"
            },
            {
                "title": "Startup India Scheme",
                "description": "Initiative to build a strong ecosystem for nurturing innovation and startups in the country.",
                "category": "business",
                "target_audience": "entrepreneur",
                "location": "all",
                "eligibility": "Entity should be incorporated as a private limited company or registered as a partnership firm or LLP. Should be up to 10 years old and annual turnover should not exceed ₹100 crore.",
                "benefits": "Self-certification, tax exemptions for 3 years, faster patent examination, access to government tenders, networking opportunities.",
                "how_to_apply": "Register on Startup India portal, get recognition certificate. Submit required documents including incorporation certificate, business plan.",
                "official_url": "https://www.startupindia.gov.in/",
                "source_website": "startupindia.gov.in"
            },
            {
                "title": "National Education Policy Implementation - Delhi",
                "description": "Implementation of NEP 2020 in Delhi schools with focus on foundational literacy, numeracy and skill development.",
                "category": "education",
                "target_audience": "student",
                "location": "Delhi",
                "eligibility": "Students enrolled in Delhi government schools and their parents/guardians.",
                "benefits": "Enhanced curriculum, vocational training, digital learning resources, teacher training programs.",
                "how_to_apply": "Automatic enrollment for government school students. Private school students can apply through education department.",
                "official_url": "https://www.edudel.nic.in/",
                "source_website": "edudel.nic.in"
            },
            {
                "title": "Ayushman Bharat - Health and Wellness Centres",
                "description": "Comprehensive primary healthcare services including preventive, curative, rehabilitative, and wellness services.",
                "category": "health",
                "target_audience": "all",
                "location": "all",
                "eligibility": "All citizens of India, with priority to economically vulnerable populations.",
                "benefits": "Free primary healthcare services, health screenings, basic medicines, referral services to higher facilities.",
                "how_to_apply": "Visit nearest Health and Wellness Centre. Aadhaar card recommended for registration.",
                "official_url": "https://ab-hwc.nhp.gov.in/",
                "source_website": "nhp.gov.in"
            }
        ]
        
        for scheme_data in sample_schemes:
            scheme = GovernmentScheme(**scheme_data)
            db.session.add(scheme)
        
        db.session.commit()
        print(f"[DB] Successfully populated {len(sample_schemes)} sample government schemes")
        return True
        
    except Exception as e:
        print(f"[DB] Error populating sample schemes: {str(e)}")
        db.session.rollback()
        return False