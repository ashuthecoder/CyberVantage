import flask
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import bcrypt
import jwt
import datetime
from email_validator import validate_email, EmailNotValidError
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from functools import wraps
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import random
import markdown
import re
import traceback
import uuid
import sqlite3

# Import functions from pyFunctions modules
from pyFunctions.email_generation import generate_ai_email, evaluate_explanation, get_fallback_evaluation
from pyFunctions.template_emails import get_template_email
from pyFunctions.simulation import generate_unique_simulation_email

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET", "dev_secret")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET", "jwt_secret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv("CSRF_SECRET", "csrf_secret")

# Init
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Configure Google Generative AI (Gemini)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f"✓ API key loaded successfully: {GOOGLE_API_KEY[:4]}...{GOOGLE_API_KEY[-4:]}")
else:
    print("Warning: GOOGLE_API_KEY not found. AI features will be limited.")

# Check current date
current_time = datetime.datetime.now()
if current_time.year > 2024:
    print(f"⚠️ WARNING: Your system date appears to be set to the future: {current_time}")
    print("   This may cause issues with authentication tokens and cookies.")

# Encryption key for sensitive DB fields
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)

# Database Models
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

# Update database schema if needed (safe)
def update_database_schema():
    """Add the simulation_id column to the SimulationEmail table if it exists and the column is missing."""
    try:
        # Connect directly to the SQLite database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
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

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))

        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))

        return f(current_user, *args, **kwargs)

    return decorated

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

# Enhanced template emails for when AI generation fails - with more variety
template_emails = [
    {
        "sender": "security@company-portal.net",
        "subject": "Password Reset Required",
        "content": """
            <p>Dear User,</p>
            <p>Our systems have detected that your password will expire in 24 hours.</p>
            <p>To reset your password, please click the link below:</p>
            <p><a href="https://company-portal.net/reset">Reset Password</a></p>
            <p>IT Department</p>
        """,
        "is_spam": True
    },
    {
        "sender": "newsletter@legitimate-news.com",
        "subject": "Weekly Technology Update",
        "content": """
            <p>Hello subscriber,</p>
            <p>This week's top tech stories:</p>
            <ul>
                <li>New advances in AI development</li>
                <li>Tech company quarterly results</li>
                <li>Upcoming product releases</li>
            </ul>
            <p>Read more on our <a href="https://legitimate-news.com">website</a>.</p>
        """,
        "is_spam": False
    },
    {
        "sender": "support@cloud-storage.com",
        "subject": "Action Required: Account Verification",
        "content": """
            <p>Dear Customer,</p>
            <p>We've noticed unusual login attempts on your account.</p>
            <p>To secure your account, please verify your identity by clicking the link below:</p>
            <p><a href="https://verification.cloud-storage.com/verify">Verify Account</a></p>
            <p>If you ignore this message, your account may be temporarily restricted.</p>
            <p>Cloud Storage Security Team</p>
        """,
        "is_spam": True
    },
    {
        "sender": "updates@spotify.com",
        "subject": "Your Weekly Music Recommendations",
        "content": """
            <p>Hey music lover!</p>
            <p>Based on your listening history, we think you might enjoy these tracks:</p>
            <ul>
                <li>"Summer Nights" by The Melodics</li>
                <li>"Distant Dreams" by Skywave</li>
                <li>"Rhythm & Soul" by Urban Collective</li>
            </ul>
            <p>Check out your personalized playlist on the Spotify app or <a href="https://spotify.com/recommendations">website</a>.</p>
            <p>The Spotify Team</p>
        """,
        "is_spam": False
    },
    {
        "sender": "alert@bank-secure.com",
        "subject": "Unusual Activity Detected on Your Account",
        "content": """
            <p>Dear Valued Customer,</p>
            <p>We have detected unusual activity on your bank account.</p>
            <p>Please verify your identity by clicking the link below and entering your account details:</p>
            <p><a href="https://bank-secure.com/verify">Verify Account</a></p>
            <p>If you don't recognize this activity, please contact us immediately.</p>
            <p>Bank Security Team</p>
        """,
        "is_spam": True
    },
    {
        "sender": "no-reply@github.com",
        "subject": "Security Alert: New Sign-in to GitHub",
        "content": """
            <p>Hello,</p>
            <p>We noticed a new sign-in to your GitHub account from a new device:</p>
            <p><strong>Time</strong>: August 14, 2025, 3:15 PM UTC<br>
            <strong>Device</strong>: Chrome on Windows<br>
            <strong>Location</strong>: San Francisco, CA, USA</p>
            <p>If this was you, you can ignore this email. If you didn't sign in recently, please <a href="https://github.com/settings/security">review your account security</a> and change your password.</p>
            <p>The GitHub Team</p>
        """,
        "is_spam": False
    },
    {
        "sender": "customer-service@amaz0n-support.net",
        "subject": "Your Amazon Order #7829345 has been Canceled",
        "content": """
            <p>Dear Amazon Customer,</p>
            <p>Unfortunately, your recent Amazon order (#7829345) has been canceled due to a problem with your payment method.</p>
            <p>To update your payment information and reprocess your order, please click the link below:</p>
            <p><a href="http://amaz0n-support.net/update-payment">Update Payment Information</a></p>
            <p>We apologize for any inconvenience.</p>
            <p>Amazon Customer Service</p>
        """,
        "is_spam": True
    },
    {
        "sender": "newsletter@medium.com",
        "subject": "Top 5 Stories This Week - Medium Digest",
        "content": """
            <p>Your Weekly Medium Digest</p>
            <h3>Top 5 Stories You Might Have Missed:</h3>
            <ul>
                <li>How I Built a Successful Tech Startup in 12 Months</li>
                <li>The Future of AI: Opportunities and Risks</li>
                <li>10 Productivity Hacks That Actually Work</li>
                <li>Understanding Web3: A Beginner's Guide</li>
                <li>Why Remote Work Is Here to Stay</li>
            </ul>
            <p>Read these stories and more on <a href="https://medium.com">Medium</a>.</p>
            <p>You're receiving this email because you're subscribed to Medium's weekly digest.</p>
        """,
        "is_spam": False
    }
]

# Helper functions for simulation_id column management
def get_simulation_id_for_email(email_id):
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

def set_simulation_id_for_email(email_id, simulation_id):
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

def get_emails_for_simulation(simulation_id):
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

# Routes
@app.route('/')
def welcome():
    return render_template("welcome.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get("name").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Email validation
        try:
            validate_email(email)
        except EmailNotValidError as e:
            return jsonify({"error": str(e)}), 400

        # Password match check
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # Password strength check
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        # Check if email exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        # Create user
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )

        # Store token in session
        session['token'] = token
        session['user_name'] = user.name

        # Redirect to dashboard
        return redirect(url_for('dashboard'))

    return render_template("login.html")

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    # Make sure database schema is updated
    update_database_schema()
    return render_template('dashboard.html', username=current_user.name)

@app.route('/learn')
@token_required
def learn(current_user):
    return render_template('learn.html', username=current_user.name)

@app.route('/simulate', methods=['GET'])
@token_required
def simulate(current_user):
    # Ensure tables exist and update schema safely
    with app.app_context():
        db.create_all()
    update_database_schema()

    try:
        print(f"[SIMULATE] Starting with session: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        # Initialize simulation if first time
        if 'simulation_phase' not in session:
            session['simulation_phase'] = 1
            session['current_email_id'] = 1
            session['simulation_id'] = str(uuid.uuid4())
            session['phase2_emails_completed'] = 0  # Initialize counter
            session.pop('active_phase2_email_id', None)
            session.modified = True
            print(f"[SIMULATE] Initialized new simulation with ID: {session.get('simulation_id')}")

        # Load predefined emails once (Phase 1)
        if session.get('simulation_phase') == 1:
            for predefined_email in predefined_emails:
                existing = SimulationEmail.query.filter_by(id=predefined_email['id']).first()
                if not existing:
                    new_email = SimulationEmail(
                        id=predefined_email['id'],
                        sender=predefined_email['sender'],
                        subject=predefined_email['subject'],
                        date=predefined_email['date'],
                        content=predefined_email['content'],
                        is_spam=predefined_email['is_spam'],
                        is_predefined=True
                    )
                    db.session.add(new_email)
            db.session.commit()

        # Read state
        phase = session.get('simulation_phase', 1)
        current_email_id = session.get('current_email_id', 1)
        simulation_id = session.get('simulation_id')
        phase2_completed = session.get('phase2_emails_completed', 0)
        active_phase2_email_id = session.get('active_phase2_email_id')

        print(f"[SIMULATE] Current phase: {phase}, Current email ID: {current_email_id}, "
              f"Simulation ID: {simulation_id}, Phase 2 completed: {phase2_completed}, "
              f"Active Phase2 Email ID: {active_phase2_email_id}")

        # Phase 1 -> Phase 2 transition
        if phase == 1 and current_email_id > 5:
            print("[SIMULATE] Phase 1 complete, moving to phase 2")
            session['simulation_phase'] = 2
            session['phase2_emails_completed'] = 0
            session.pop('active_phase2_email_id', None)
            session.modified = True
            phase = 2  # continue into Phase 2 logic

        # Completion logic (Phase 2 by counter only)
        if phase == 2 and phase2_completed >= 5:
            print("[SIMULATE] Simulation complete")
            return render_template('simulate.html', phase='complete', username=current_user.name)

        # Fetch email for current step
        email = None

        if phase == 1:
            # Phase 1: Get predefined email
            email = SimulationEmail.query.filter_by(id=current_email_id).first()
            if not email:
                if 0 < current_email_id <= len(predefined_emails):
                    email_data = predefined_emails[current_email_id - 1]
                    email = SimulationEmail(
                        id=current_email_id,
                        sender=email_data['sender'],
                        subject=email_data['subject'],
                        date=email_data['date'],
                        content=email_data['content'],
                        is_spam=email_data['is_spam'],
                        is_predefined=True
                    )
                    db.session.add(email)
                    db.session.commit()
                else:
                    # Reset to a valid state
                    session['simulation_phase'] = 1
                    session['current_email_id'] = 1
                    session['simulation_id'] = str(uuid.uuid4())
                    session['phase2_emails_completed'] = 0
                    session.pop('active_phase2_email_id', None)
                    session.modified = True
                    return redirect(url_for('simulate'))
        else:
            # Phase 2: Use active email if exists, otherwise generate a new one
            if active_phase2_email_id:
                email = SimulationEmail.query.get(active_phase2_email_id)

            if not email:
                # Build performance summary from Phase 1
                previous_responses = SimulationResponse.query.filter_by(
                    user_id=current_user.id
                ).filter(SimulationResponse.email_id < 6).all()
                correct_count = sum(1 for r in previous_responses if r.user_response == r.is_spam_actual)
                performance_summary = f"The user correctly identified {correct_count} out of 5 emails in phase 1."
                print(f"[SIMULATE] Performance summary: {performance_summary}")

                # Attempt AI generation; fallback to templates on error
                try:
                    email_data = generate_ai_email(current_user.name, performance_summary, GOOGLE_API_KEY, genai, app)
                except Exception as e:
                    print(f"[SIMULATE] Error generating AI email (will fallback to template): {e}")
                    email_data = get_template_email()

                # Create and persist the email
                email = SimulationEmail(
                    sender=email_data['sender'],
                    subject=email_data['subject'],
                    date=email_data.get('date', datetime.datetime.utcnow().strftime("%B %d, %Y")),
                    content=email_data['content'],
                    is_spam=email_data['is_spam'],
                    is_predefined=False
                )
                db.session.add(email)
                db.session.commit()

                # Tag email with this simulation_id if the column exists
                set_simulation_id_for_email(email.id, simulation_id)

                # Track active Phase 2 email ID
                session['active_phase2_email_id'] = email.id
                session.modified = True
                print(f"[SIMULATE] Created new Phase 2 email with ID {email.id} for simulation {simulation_id}")

        if not email:
            return render_template(
                'system_message.html',
                title="Error",
                message="Failed to load email. Please try restarting the simulation.",
                action_text="Restart Simulation",
                action_url=url_for('restart_simulation'),
                username=current_user.name
            )

        # Render appropriate view
        return render_template(
            'simulate.html',
            phase=phase,
            current_email=current_email_id if phase == 1 else session.get('active_phase2_email_id'),
            email=email,
            username=current_user.name,
            api_key_available=bool(GOOGLE_API_KEY)
        )

    except Exception as e:
        print(f"[SIMULATE] Exception in simulate route: {str(e)}")
        traceback.print_exc()
        # Emergency reset
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = str(uuid.uuid4())
        session['phase2_emails_completed'] = 0
        session.pop('active_phase2_email_id', None)
        session.modified = True
        return render_template(
            'system_message.html',
            title="Error",
            message=f"An error occurred: {str(e)}. The simulation has been reset.",
            action_text="Continue",
            action_url=url_for('simulate'),
            username=current_user.name
        )

@app.route('/submit_simulation', methods=['POST'])
@token_required
def submit_simulation(current_user):
    try:
        email_id = int(request.form.get('email_id'))
        phase = int(request.form.get('phase'))
        is_spam_response = request.form.get('is_spam') == 'true'
        explanation = request.form.get('explanation', '')

        print(f"[SUBMIT] Processing submission: phase={phase}, email_id={email_id}")
        print(f"[SUBMIT] Current session before: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        # Get the email
        email = SimulationEmail.query.get(email_id)
        if not email:
            print(f"[SUBMIT] Error: Email ID {email_id} not found in database")
            return redirect(url_for('reset_stuck_simulation'))

        # Process AI feedback for phase 2
        ai_feedback = None
        score = None
        if phase == 2:
            eval_result = evaluate_explanation(
                email.content,
                email.is_spam,
                is_spam_response,
                explanation,
                GOOGLE_API_KEY,
                genai,
                app
            )
            ai_feedback = eval_result["feedback"]
            score = eval_result["score"]

        # Save the response to database
        response = SimulationResponse(
            user_id=current_user.id,
            email_id=email_id,
            is_spam_actual=email.is_spam,
            user_response=is_spam_response,
            user_explanation=explanation,
            ai_feedback=ai_feedback,
            score=score
        )
        db.session.add(response)
        db.session.commit()

        # Phase 2: show feedback page (continuation handled in continue_after_feedback)
        if phase == 2:
            return redirect(url_for('simulation_feedback', email_id=email_id))

        # Phase 1: advance to next predefined email
        next_email_id = email_id + 1
        if phase == 1 and next_email_id > 5:
            session['simulation_phase'] = 2
            # Keep current_email_id untouched in Phase 2; Phase 2 flow uses active_phase2_email_id
            print(f"[SUBMIT] Advancing to phase 2")
        else:
            session['current_email_id'] = next_email_id
            print(f"[SUBMIT] Advancing to email {next_email_id} in phase {phase}")

        # Force session to save
        session.modified = True

        print(f"[SUBMIT] Session after update: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        return redirect(url_for('simulate'))

    except Exception as e:
        print(f"[SUBMIT] Exception in submit_simulation: {str(e)}")
        traceback.print_exc()
        # Emergency recovery
        return redirect(url_for('reset_stuck_simulation'))

@app.route('/simulation_feedback/<int:email_id>')
@token_required
def simulation_feedback(current_user, email_id):
    try:
        # Get the user's most recent response for this email
        response = SimulationResponse.query.filter_by(
            user_id=current_user.id,
            email_id=email_id
        ).order_by(SimulationResponse.created_at.desc()).first()

        if not response:
            print(f"[FEEDBACK] No response found for email {email_id}")
            return redirect(url_for('simulate'))

        # Ensure the feedback is treated as HTML
        if response.ai_feedback:
            if not response.ai_feedback.strip().startswith('<'):
                print(f"[FEEDBACK] Warning: Feedback doesn't appear to be HTML: {response.ai_feedback[:50]}...")
                response.ai_feedback = f"<p>{response.ai_feedback}</p>"

        return render_template(
            'simulation_feedback.html',
            response=response,
            username=current_user.name
        )
    except Exception as e:
        print(f"[FEEDBACK] Error in simulation_feedback: {e}")
        traceback.print_exc()
        return redirect(url_for('dashboard'))

# Continue after feedback (Phase 2 only)
@app.route('/continue_after_feedback/<int:email_id>')
@token_required
def continue_after_feedback(current_user, email_id):
    """Advance to the next email after viewing feedback (Phase 2)."""
    try:
        print(f"[CONTINUE] Processing continuation from email {email_id}")

        # Only Phase 2 uses this route; increment the counter and clear active email
        if session.get('simulation_phase') == 2:
            session['phase2_emails_completed'] = session.get('phase2_emails_completed', 0) + 1
            # Clear the active email so simulate() generates the next one
            session.pop('active_phase2_email_id', None)
            session.modified = True

        print(f"[CONTINUE] Updated session: phase={session.get('simulation_phase')}, "
              f"phase2_completed={session.get('phase2_emails_completed')}, "
              f"active_phase2_email_id={session.get('active_phase2_email_id')}, "
              f"simulation_id={session.get('simulation_id')}")

        # If 5 done, go to results
        if session.get('simulation_phase') == 2 and session.get('phase2_emails_completed', 0) >= 5:
            print(f"[CONTINUE] Phase 2 complete: {session.get('phase2_emails_completed')} emails completed")
            return redirect(url_for('simulation_results'))

        return redirect(url_for('simulate'))
    except Exception as e:
        print(f"[CONTINUE] Error in continue_after_feedback: {e}")
        traceback.print_exc()
        return redirect(url_for('reset_stuck_simulation'))

@app.route('/simulation_results')
@token_required
def simulation_results(current_user):
    try:
        simulation_id = session.get('simulation_id')
        print(f"[RESULTS] Getting results for simulation ID: {simulation_id}")

        # Phase 1 (predefined IDs are always 1..5)
        phase1_email_ids = list(range(1, 6))

        def most_recent_per_email(responses):
            seen = set()
            ordered = []
            for r in responses:
                if r.email_id not in seen:
                    seen.add(r.email_id)
                    ordered.append(r)
            return ordered

        # 1) Collect Phase 1 responses (newest first), then keep only most recent per email_id
        phase1_all = (SimulationResponse.query
                      .filter_by(user_id=current_user.id)
                      .filter(SimulationResponse.email_id.in_(phase1_email_ids))
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
        phase1_responses = most_recent_per_email(phase1_all)[:5]

        # 2) Try Phase 2 by simulation_id linkage (if column/value available)
        phase2_email_ids = []
        try:
            phase2_email_ids = get_emails_for_simulation(simulation_id) if simulation_id else []
        except Exception as e:
            print(f"[RESULTS] Error fetching emails for simulation via simulation_id: {e}")
            phase2_email_ids = []

        if phase2_email_ids:
            p2_all = (SimulationResponse.query
                      .filter_by(user_id=current_user.id)
                      .filter(SimulationResponse.email_id.in_(phase2_email_ids))
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
            phase2_responses = most_recent_per_email(p2_all)
        else:
            # 3) Fallback: last AI responses for this user by joining SimulationEmail (is_predefined == False)
            p2_all = (db.session.query(SimulationResponse)
                      .join(SimulationEmail, SimulationEmail.id == SimulationResponse.email_id)
                      .filter(SimulationResponse.user_id == current_user.id,
                              SimulationEmail.is_predefined == False)
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
            phase2_responses = most_recent_per_email(p2_all)

        phase2_responses = phase2_responses[:5]

        # 4) Stats
        phase1_correct = sum(1 for r in phase1_responses if r.user_response == r.is_spam_actual)
        phase2_correct = sum(1 for r in phase2_responses if r.user_response == r.is_spam_actual)
        phase2_scores = [r.score for r in phase2_responses if getattr(r, 'score', None) is not None]
        avg_score = (sum(phase2_scores) / len(phase2_scores)) if phase2_scores else 0

        print(f"[RESULTS] Phase 1: {phase1_correct}/{len(phase1_responses)}, Phase 2: {phase2_correct}/{len(phase2_responses)}")
        print(f"[RESULTS] Phase 2 scores: {phase2_scores}")

        # 5) Clear simulation state after calculating results
        session.pop('simulation_phase', None)
        session.pop('current_email_id', None)
        session.pop('simulation_id', None)
        session.pop('phase2_emails_completed', None)
        session.pop('active_phase2_email_id', None)
        session.modified = True

        # 6) Render
        all_responses = sorted(phase1_responses + phase2_responses, key=lambda x: x.email_id)

        return render_template(
            'simulation_results.html',
            phase1_correct=phase1_correct,
            phase1_total=len(phase1_responses),
            phase2_correct=phase2_correct,
            phase2_total=len(phase2_responses),
            avg_score=avg_score,
            responses=all_responses,
            phase1_responses=phase1_responses,
            phase2_responses=phase2_responses,
            username=current_user.name
        )
    except Exception as e:
        print(f"[RESULTS] Error in simulation_results: {e}")
        traceback.print_exc()
        # Show a friendly message instead of bouncing to dashboard silently
        return render_template(
            'system_message.html',
            title="Results Unavailable",
            message=f"Couldn't render your results due to an error: {e}",
            action_text="Return to Dashboard",
            action_url=url_for('dashboard'),
            username=current_user.name
        )
@app.route('/analysis')
@token_required
def analysis(current_user):
    return render_template('analysis.html', username=current_user.name)

@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('user_name', None)
    session.pop('simulation_phase', None)
    session.pop('current_email_id', None)
    session.pop('simulation_id', None)
    session.pop('phase2_emails_completed', None)
    session.pop('active_phase2_email_id', None)
    return redirect(url_for('login'))

@app.route('/restart_simulation')
@token_required
def restart_simulation(current_user):
    try:
        print("[RESTART] Restarting simulation")

        # Generate a new simulation ID
        new_simulation_id = str(uuid.uuid4())

        # Clear session completely and set new values
        session.clear()
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session['phase2_emails_completed'] = 0
        session.modified = True

        print(f"[RESTART] Created new simulation ID: {new_simulation_id}")

        # Reset rate limit tracking
        for k in ['RATE_LIMITED', 'RATE_LIMIT_TIME']:
            if k in app.config:
                app.config.pop(k, None)

        # Delete existing responses for this user
        SimulationResponse.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        print("[RESTART] Simulation reset complete")

        return redirect(url_for('simulate'))
    except Exception as e:
        print(f"[RESTART] Error in restart_simulation: {e}")
        db.session.rollback()
        return redirect(url_for('dashboard'))

@app.route('/reset_stuck_simulation')
@token_required
def reset_stuck_simulation(current_user):
    """Emergency route to fix stuck simulations"""
    try:
        # Generate a new simulation ID
        new_simulation_id = str(uuid.uuid4())

        # Clear session data and start fresh
        session.clear()
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session['phase2_emails_completed'] = 0
        session.modified = True

        print(f"[RESET] Created new simulation ID: {new_simulation_id}")

        # Reset rate limit tracking
        for k in ['RATE_LIMITED', 'RATE_LIMIT_TIME']:
            if k in app.config:
                app.config.pop(k, None)

        # Delete previous responses
        SimulationResponse.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        return render_template(
            'system_message.html',
            title="Simulation Reset",
            message="Your simulation has been reset due to a technical issue.",
            action_text="Continue to Simulation",
            action_url=url_for('simulate'),
            username=current_user.name
        )
    except Exception as e:
        print(f"[RESET] Exception in reset_stuck_simulation: {e}")
        return redirect(url_for('dashboard'))

@app.route('/check_threats')
@token_required
def check_threats(current_user):
    return render_template('check_threats.html', username=current_user.name)

@app.route('/debug_simulation')
@token_required
def debug_simulation(current_user):
    """Debug endpoint to see current simulation state"""
    # Get all emails and responses in the system
    emails = SimulationEmail.query.all()
    responses = SimulationResponse.query.filter_by(user_id=current_user.id).all()

    # Current session state
    session_info = {
        "phase": session.get('simulation_phase'),
        "current_email_id": session.get('current_email_id'),
        "simulation_id": session.get('simulation_id'),
        "phase2_emails_completed": session.get('phase2_emails_completed'),
        "active_phase2_email_id": session.get('active_phase2_email_id'),
    }

    # Format the data
    email_data = []
    for email in emails:
        sim_id = get_simulation_id_for_email(email.id)
        email_data.append({
            "id": email.id,
            "sender": email.sender,
            "subject": email.subject,
            "is_spam": email.is_spam,
            "is_predefined": email.is_predefined,
            "created_at": str(email.created_at),
            "simulation_id": sim_id
        })

    response_data = []
    for resp in responses:
        response_data.append({
            "id": resp.id,
            "email_id": resp.email_id,
            "is_spam_actual": resp.is_spam_actual,
            "user_response": resp.user_response,
            "score": resp.score,
            "created_at": str(resp.created_at)
        })

    # Database schema info
    db_schema = {
        "has_simulation_id_column": False
    }

    try:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        db_schema["has_simulation_id_column"] = 'simulation_id' in columns
        db_schema["all_columns"] = columns
        conn.close()
    except Exception as e:
        db_schema["error"] = str(e)

    return jsonify({
        "session": session_info,
        "emails": email_data,
        "responses": response_data,
        "schema": db_schema
    })

@app.route('/debug')
def debug_info():
    # Only allow this in debug mode
    if not app.debug:
        return "Debug information only available when debug=True"

    info = {
        "Environment Variables": {
            "GOOGLE_API_KEY": f"{os.getenv('GOOGLE_API_KEY')[:4]}...{os.getenv('GOOGLE_API_KEY')[-4:]}" if os.getenv('GOOGLE_API_KEY') else "Not set",
            "FLASK_SECRET": f"{os.getenv('FLASK_SECRET')[:4]}...{os.getenv('FLASK_SECRET')[-4:]}" if os.getenv('FLASK_SECRET') else "Using default",
        },
        "Session Data": {k: v for k, v in session.items() if k != 'token'},
        "Database Tables": [table for table in db.metadata.tables.keys() ],
        "System Time": str(datetime.datetime.now()),
        "API Status": {
            "Rate Limited": app.config.get('RATE_LIMITED', False),
            "Rate Limit Time": datetime.datetime.fromtimestamp(app.config.get('RATE_LIMIT_TIME', 0)).strftime('%Y-%m-%d %H:%M:%S') if app.config.get('RATE_LIMIT_TIME') else "N/A",
        },
        "Database Counts": {
            "Users": User.query.count(),
            "SimulationEmails": SimulationEmail.query.count(),
            "SimulationResponses": SimulationResponse.query.count()
        }
    }

    return jsonify(info)

# New route to add missing column to database
@app.route('/update_schema')
@token_required
def update_schema(current_user):
    """Add missing column to database"""
    try:
        success = update_database_schema()
        return jsonify({
            "success": success,
            "message": "Database schema updated successfully" if success else "Failed to update database schema"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating schema: {str(e)}"
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_database_schema()  # Ensure the schema is updated at startup
    # Disable the reloader to avoid double-execution side-effects in dev
    app.run(debug=True, use_reloader=False)