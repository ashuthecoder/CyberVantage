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
    email_id = db.Column(db.Integer, nullable=False)  # 1-5 for predefined, 6-10 for AI generated
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
    
    # We'll handle this column manually since it's causing issues
    # simulation_id = db.Column(db.String(36), nullable=True)  # Track which simulation run this email belongs to

# Update database schema if needed
def update_database_schema():
    """Add the simulation_id column to the SimulationEmail table if it doesn't exist"""
    try:
        # Connect directly to the SQLite database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column exists
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

def generate_ai_email(user_name, previous_responses):
    """Generate an AI email with robust error handling"""
    print(f"[GENERATE] Starting email generation for user: {user_name}")
    
    if not GOOGLE_API_KEY:
        print("[GENERATE] No API key - using template email")
        return get_template_email()
    
    # Create prompt
    prompt = f"""
    Generate a realistic phishing or legitimate email for a cybersecurity training simulation.
    
    User's name: {user_name}
    Previous performance: {previous_responses}
    
    The email should have the following format:
    - Sender: [email address]
    - Subject: [subject line]
    - Date: [current date]
    - Content: [HTML content of the email body]
    - Is_spam: [true/false] - whether this is a phishing email or legitimate
    
    If creating a phishing email, include subtle red flags that a cautious user might notice.
    If creating a legitimate email, make it realistic but free of phishing indicators.
    
    Make each email unique and different from the predefined examples.
    """
    
    try:
        # Generate the email with simpler configuration
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("[GENERATE] Sending request to Gemini API")
        response = model.generate_content(prompt)
        
        # Extract content from response
        content = None
        
        # Try multiple approaches to extract text
        if hasattr(response, 'text'):
            content = response.text
            print("[GENERATE] Successfully extracted text via .text property")
        elif hasattr(response, 'parts') and response.parts:
            content = response.parts[0].text
            print("[GENERATE] Successfully extracted text via .parts[0].text")
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                content = candidate.content.parts[0].text
                print("[GENERATE] Successfully extracted text via candidates structure")
        
        # If we still don't have content, try string representation
        if not content:
            content = str(response)
            print("[GENERATE] Using string representation as fallback")
            
        if not content:
            print("[GENERATE] Failed to extract content from response")
            return get_template_email()
            
        print(f"[GENERATE] Response content length: {len(content)}")
        print(f"[GENERATE] First 100 chars: {content[:100]}")
        
        # Parse the email components with better error handling
        try:
            if "Sender:" not in content or "Subject:" not in content:
                print("[GENERATE] Missing expected fields in response")
                return get_template_email()
                
            sender = content.split("Sender:")[1].split("\n")[0].strip()
            subject = content.split("Subject:")[1].split("\n")[0].strip()
            
            # Get date with fallback
            try:
                date = content.split("Date:")[1].split("\n")[0].strip()
            except:
                date = datetime.datetime.now().strftime("%B %d, %Y")
                
            # Extract email content between Content: and Is_spam:
            if "Content:" in content and "Is_spam:" in content:
                email_content = content.split("Content:")[1].split("Is_spam:")[0].strip()
            else:
                print("[GENERATE] Could not extract email content properly")
                email_content = f"<p>Training email content.</p><p>{content}</p>"
            
            # Determine if spam
            try:
                is_spam_section = content.split("Is_spam:")[1].lower().strip()
                is_spam = "true" in is_spam_section or "yes" in is_spam_section
            except:
                is_spam = random.choice([True, False])
            
            # Ensure email_content is proper HTML
            if not email_content.strip().startswith("<"):
                email_content = f"<p>{email_content.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
            
            return {
                "sender": sender,
                "subject": subject,
                "date": date,
                "content": email_content,
                "is_spam": is_spam
            }
        except Exception as parse_error:
            print(f"[GENERATE] Error parsing response: {parse_error}")
            traceback.print_exc()
            return get_template_email()
    except Exception as e:
        print(f"[GENERATE] Error in AI email generation: {e}")
        traceback.print_exc()
        
        # Check for rate limits
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = datetime.datetime.now().timestamp()
            print(f"[GENERATE] API rate limit detected: {error_str}")
        
        return get_template_email()

def get_template_email():
    """Return a random template email when AI generation fails"""
    # Generate a unique template for each position
    template = random.choice(template_emails)
    
    # Add randomness to ensure uniqueness
    return {
        "sender": template["sender"],
        "subject": f"{template['subject']} #{random.randint(1000, 9999)}",
        "date": datetime.datetime.now().strftime("%B %d, %Y"),
        "content": template["content"],
        "is_spam": template["is_spam"]
    }

def evaluate_explanation(email_content, is_spam, user_response, user_explanation):
    """Evaluate the user's explanation of why an email is phishing/legitimate"""
    print(f"[EVALUATE] Starting evaluation. Is spam: {is_spam}, User said: {user_response}")
    
    # Check for recent rate limit errors
    rate_limited = app.config.get('RATE_LIMITED', False)
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0)
    current_time = datetime.datetime.now().timestamp()
    
    # Use fallbacks if needed
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"[EVALUATE] Using fallback due to rate limit ({int(current_time - rate_limit_time)} seconds ago)")
        return get_fallback_evaluation(is_spam, user_response)
    
    if not GOOGLE_API_KEY:
        print("[EVALUATE] No API key - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
    
    # Create prompt for evaluation
    prompt = f"""
    Evaluate this user's analysis of a potential phishing email.
    
    THE EMAIL:
    {email_content}
    
    CORRECT ANSWER:
    This {'IS' if is_spam else 'IS NOT'} a phishing/spam email.
    
    USER'S RESPONSE:
    The user said this {'IS' if user_response else 'IS NOT'} a phishing/spam email.
    
    USER'S EXPLANATION:
    {user_explanation}
    
    Please evaluate:
    1. Is the user's conclusion correct? (Yes/No)
    2. What did the user get right in their analysis?
    3. What did the user miss or get wrong?
    4. On a scale of 1-10, rate the user's analysis quality.
    5. Provide constructive feedback to improve their phishing detection skills.
    
    Format your response with Markdown formatting. Use headers (##) for each numbered section, bold for emphasis, and paragraphs for readability.
    """
    
    try:
        # Generate evaluation
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("[EVALUATE] Sending evaluation request to Gemini API")
        response = model.generate_content(prompt)
        
        # Get response text
        ai_text = None
        try:
            # Try multiple ways to extract the text
            if hasattr(response, 'text'):
                ai_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                ai_text = response.parts[0].text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    ai_text = candidate.content.parts[0].text
            
            if not ai_text:
                ai_text = str(response)
                
            print(f"[EVALUATE] Successfully got AI text, length: {len(ai_text)}")
        except Exception as text_error:
            print(f"[EVALUATE] Error extracting text: {text_error}")
            return get_fallback_evaluation(is_spam, user_response)
        
        # Process text for better Markdown formatting
        ai_text = ai_text.strip()
        
        # Format numbered sections as headers
        for i in range(1, 6):
            ai_text = re.sub(r"^" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            ai_text = re.sub(r"^" + str(i) + r"\)\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            ai_text = re.sub(r"^#{1,5}\s+" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
        
        # Format bullet points and emphasis
        ai_text = re.sub(r"^\*\s*(?=\S)", "* ", ai_text, flags=re.MULTILINE)
        ai_text = re.sub(r"(?<!\*)\*\*(?=\S)", "** ", ai_text)
        ai_text = re.sub(r"(?<=\S)\*\*(?!\*)", " **", ai_text)
        
        # Add paragraph breaks
        ai_text = re.sub(r"(?<=[.!?])\s+(?=[A-Z])", "\n\n", ai_text)
        ai_text = re.sub(r"(?<=[^\n])(?=^##)", "\n\n", ai_text, flags=re.MULTILINE)
        
        # Convert markdown to HTML
        try:
            formatted_html = markdown.markdown(ai_text, extensions=['extra'])
            print("[EVALUATE] Successfully converted markdown to HTML")
        except Exception as md_error:
            print(f"[EVALUATE] Error in markdown conversion: {md_error}")
            formatted_html = f"<p>{ai_text.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
        
        # Add styling
        formatted_html = formatted_html.replace("<li>", "<li style='margin-bottom: 8px;'>")
        formatted_html = formatted_html.replace("<h2>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
        formatted_html = formatted_html.replace("</h2>", "</h3>")
        formatted_html = formatted_html.replace("<strong>", "<strong style='color: #2a3f54;'>")
        
        # Calculate score
        base_score = 8 if user_response == is_spam else 3
        
        try:
            # Extract score from text
            ai_score_text = ai_text.split("scale of 1-10")[1].split("\n")[0]
            ai_score = int(''.join(filter(str.isdigit, ai_score_text)))
            score = ai_score if 1 <= ai_score <= 10 else base_score
        except:
            score = base_score
        
        return {
            "feedback": formatted_html,
            "score": score
        }
    except Exception as e:
        print(f"[EVALUATE] Error in evaluation: {e}")
        traceback.print_exc()
        
        # Check for rate limits
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = current_time
            print(f"[EVALUATE] Rate limit detected: {error_str}")
        
        return get_fallback_evaluation(is_spam, user_response)

def get_fallback_evaluation(is_spam, user_response):
    """Generate a varied evaluation when AI isn't available"""
    correct = user_response == is_spam
    
    # Add more varied scoring
    if correct:
        base_score = random.randint(7, 9)  # Random score between 7-9
        
        # Choose from multiple feedback templates for variety
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Yes, the user's conclusion was correct.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>The user correctly identified whether this was a phishing email or not. They showed good judgment.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>While the conclusion was correct, a more detailed analysis would help strengthen phishing detection skills.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, the user's analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Good job identifying this email correctly! To improve further, practice identifying specific red flags in phishing emails and security features in legitimate emails.</p>
            """,
            
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Yes, your assessment was accurate.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>You correctly determined the nature of the email and demonstrated good security awareness.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>Your conclusion was correct, but including more specific details about what influenced your decision would strengthen your analysis.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, your analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Excellent work! In future analyses, try to point out specific elements like sender address anomalies, suspicious links, and urgency tactics.</p>
            """
        ]
        
        feedback = random.choice(templates).format(score=base_score)
    else:
        base_score = random.randint(2, 4)  # Random score between 2-4
        
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>No, the user's conclusion was incorrect.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>The user attempted to analyze the email, which is an important security practice.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>The user missed critical indicators that would have led to the correct classification of this email.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, the user's analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>For better results, carefully examine the sender's address, look for urgency cues in phishing emails, and check for suspicious links. With practice, your detection skills will improve.</p>
            """,
            
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Unfortunately, your assessment was not accurate.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>You engaged with the exercise and considered the email's content, which is a good security habit.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>You missed some key indicators that would have helped correctly identify this email's legitimacy.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, your analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Remember to check for inconsistencies in the domain name, generic greetings, poor grammar, and requests for sensitive information. These common indicators can help you make more accurate assessments.</p>
            """
        ]
        
        feedback = random.choice(templates).format(score=base_score)
    
    return {
        "feedback": feedback,
        "score": base_score
    }

# Helper function for storing and retrieving simulation ID for advanced emails
def get_simulation_id_for_email(email_id):
    """Get the simulation ID for a specific email"""
    try:
        # Connect directly to the database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if simulation_id column exists
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'simulation_id' in columns:
            cursor.execute("SELECT simulation_id FROM simulation_email WHERE id=?", (email_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        else:
            conn.close()
            return None
    except Exception as e:
        print(f"[DB] Error getting simulation_id: {str(e)}")
        return None

def set_simulation_id_for_email(email_id, simulation_id):
    """Set the simulation ID for a specific email"""
    try:
        # Connect directly to the database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if simulation_id column exists
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'simulation_id' in columns:
            cursor.execute("UPDATE simulation_email SET simulation_id=? WHERE id=?", (simulation_id, email_id))
            conn.commit()
            conn.close()
            return True
        else:
            conn.close()
            return False
    except Exception as e:
        print(f"[DB] Error setting simulation_id: {str(e)}")
        return False

def get_emails_for_simulation(simulation_id):
    """Get all emails for a specific simulation"""
    try:
        # Connect directly to the database
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if simulation_id column exists
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'simulation_id' in columns:
            cursor.execute("SELECT id FROM simulation_email WHERE simulation_id=?", (simulation_id,))
            emails = cursor.fetchall()
            conn.close()
            return [email[0] for email in emails]
        else:
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
    # Make sure database schema is updated
    update_database_schema()
    
    try:
        print(f"[SIMULATE] Starting with session: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")
        
        # Initialize simulation if first time
        if 'simulation_phase' not in session:
            session['simulation_phase'] = 1
            session['current_email_id'] = 1
            session['simulation_id'] = str(uuid.uuid4())
            session.modified = True
            print(f"[SIMULATE] Initialized new simulation with ID: {session.get('simulation_id')}")
            
        # Load predefined emails
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
        
        # Get current phase and email
        phase = session.get('simulation_phase', 1)
        current_email_id = session.get('current_email_id', 1)
        simulation_id = session.get('simulation_id')
        
        print(f"[SIMULATE] Current phase: {phase}, Current email ID: {current_email_id}, Simulation ID: {simulation_id}")
        
        # Check if simulation is complete
        if (phase == 1 and current_email_id > 5) or (phase == 2 and current_email_id > 10):
            print("[SIMULATE] Simulation complete")
            return render_template('simulate.html', phase='complete', username=current_user.name)
        
        # Get the email for this stage
        email = None
        
        if phase == 1:
            # Phase 1: Get predefined email
            email = SimulationEmail.query.filter_by(id=current_email_id).first()
            if not email:
                if 0 < current_email_id <= len(predefined_emails):
                    # Create predefined email
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
                    session.modified = True
                    return redirect(url_for('simulate'))
        else:
            # Phase 2: Get or create AI-generated email
            # First check if there's an existing email with matching ID
            email = SimulationEmail.query.filter_by(id=current_email_id).first()
            existing_sim_id = None
            
            # Try to get the simulation ID for this email
            if email:
                existing_sim_id = get_simulation_id_for_email(current_email_id)
                print(f"[SIMULATE] Found email ID {current_email_id} with simulation_id: {existing_sim_id}")
            
            # If email exists but belongs to a different simulation, or doesn't exist at all,
            # we need to generate a new one
            if not email or (existing_sim_id != simulation_id and existing_sim_id is not None):
                # Get performance from phase 1
                previous_responses = SimulationResponse.query.filter_by(
                    user_id=current_user.id
                ).filter(SimulationResponse.email_id < 6).all()
                
                correct_count = sum(1 for r in previous_responses if r.user_response == r.is_spam_actual)
                performance_summary = f"The user correctly identified {correct_count} out of 5 emails in phase 1."
                print(f"[SIMULATE] Performance summary: {performance_summary}")
                
                try:
                    # Generate AI email
                    email_data = generate_ai_email(current_user.name, performance_summary)
                    
                    # Create a database entry for this AI email
                    email = SimulationEmail(
                        id=current_email_id,
                        sender=email_data['sender'],
                        subject=email_data['subject'],
                        date=email_data['date'],
                        content=email_data['content'],
                        is_spam=email_data['is_spam'],
                        is_predefined=False
                    )
                    db.session.add(email)
                    db.session.commit()
                    
                    # Now set the simulation ID for this email
                    set_simulation_id_for_email(current_email_id, simulation_id)
                    print(f"[SIMULATE] Created new email {current_email_id} for simulation {simulation_id}")
                    
                except Exception as e:
                    print(f"[SIMULATE] Error generating email: {str(e)}")
                    # Use a fallback email
                    template = random.choice(template_emails)
                    email = SimulationEmail(
                        id=current_email_id,
                        sender=template["sender"],
                        subject=f"{template['subject']} #{random.randint(1000, 9999)}",
                        date=datetime.datetime.now().strftime("%B %d, %Y"),
                        content=template["content"],
                        is_spam=template["is_spam"],
                        is_predefined=False
                    )
                    db.session.add(email)
                    db.session.commit()
                    
                    # Set the simulation ID
                    set_simulation_id_for_email(current_email_id, simulation_id)
            else:
                # If we're using an existing email from a previous simulation, update its simulation ID
                if existing_sim_id is None:
                    set_simulation_id_for_email(current_email_id, simulation_id)
        
        if not email:
            return render_template(
                'system_message.html',
                title="Error",
                message="Failed to load email. Please try restarting the simulation.",
                action_text="Restart Simulation",
                action_url=url_for('restart_simulation'),
                username=current_user.name
            )
        
        return render_template(
            'simulate.html', 
            phase=phase, 
            current_email=current_email_id, 
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
                explanation
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
        
        # If we're in phase 2, show feedback
        if phase == 2:
            # For phase 2, we'll update the session in the continue_after_feedback route
            return redirect(url_for('simulation_feedback', email_id=email_id))
        
        # Update session for next email (Phase 1 only)
        next_email_id = email_id + 1
        
        # Check if we need to move to the next phase
        if phase == 1 and next_email_id > 5:
            session['simulation_phase'] = 2
            session['current_email_id'] = 6
            print(f"[SUBMIT] Advancing to phase 2, email 6")
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
            # Diagnostic check - look for HTML tags in the feedback
            if not response.ai_feedback.strip().startswith('<'):
                print(f"[FEEDBACK] Warning: Feedback doesn't appear to be HTML: {response.ai_feedback[:50]}...")
                # Try to wrap plain text in paragraph tags
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

# NEW ROUTE: Continue after feedback
@app.route('/continue_after_feedback/<int:email_id>')
@token_required
def continue_after_feedback(current_user, email_id):
    """Advance to the next email after viewing feedback"""
    try:
        print(f"[CONTINUE] Processing continuation from email {email_id}")
        
        # Calculate next email ID
        next_email_id = email_id + 1
        
        # Update session for phase 2
        session['current_email_id'] = next_email_id
        session.modified = True
        
        print(f"[CONTINUE] Updated session: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")
        
        # Check if phase 2 is complete
        if next_email_id > 10:
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
        # Get all responses for this user
        all_responses = SimulationResponse.query.filter_by(
            user_id=current_user.id
        ).order_by(SimulationResponse.created_at.desc()).all()
        
        # Filter to get only the most recent response for each email_id
        # This ensures we don't double-count responses from multiple simulation attempts
        email_ids_seen = set()
        filtered_responses = []
        
        for response in all_responses:
            if response.email_id not in email_ids_seen:
                email_ids_seen.add(response.email_id)
                filtered_responses.append(response)
        
        # Separate Phase 1 and Phase 2 responses
        phase1_responses = [r for r in filtered_responses if 1 <= r.email_id <= 5][:5]
        phase2_responses = [r for r in filtered_responses if 6 <= r.email_id <= 10][:5]
        
        # Calculate statistics correctly
        phase1_correct = sum(1 for r in phase1_responses if r.user_response == r.is_spam_actual)
        phase2_correct = sum(1 for r in phase2_responses if r.user_response == r.is_spam_actual)
        
        phase2_scores = [r.score for r in phase2_responses if r.score is not None]
        avg_score = sum(phase2_scores) / len(phase2_scores) if phase2_scores else 0
        
        print(f"[RESULTS] Phase 1: {phase1_correct}/{len(phase1_responses)}, Phase 2: {phase2_correct}/{len(phase2_responses)}")
        
        # Reset simulation for potential future attempts
        session.pop('simulation_phase', None)
        session.pop('current_email_id', None)
        session.pop('simulation_id', None)  # Clear simulation ID
        session.modified = True
        
        # For the results page, only include the responses we're actually counting
        all_responses = sorted(phase1_responses + phase2_responses, key=lambda x: x.email_id)
        
        return render_template(
            'simulation_results.html',
            phase1_correct=phase1_correct,
            phase1_total=len(phase1_responses),
            phase2_correct=phase2_correct,
            phase2_total=len(phase2_responses),
            avg_score=avg_score,
            responses=all_responses,
            username=current_user.name
        )
    except Exception as e:
        print(f"[RESULTS] Error in simulation_results: {e}")
        traceback.print_exc()
        return redirect(url_for('dashboard'))

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
    return redirect(url_for('login'))

@app.route('/restart_simulation')
@token_required
def restart_simulation(current_user):
    try:
        print("[RESTART] Restarting simulation")
        
        # Generate a new simulation ID
        new_simulation_id = str(uuid.uuid4())
        
        # Clear session
        session.pop('simulation_phase', None)
        session.pop('current_email_id', None)
        session.pop('simulation_id', None)
        
        # Explicitly set new values
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session.modified = True
        
        print(f"[RESTART] Created new simulation ID: {new_simulation_id}")
        
        # Reset rate limit tracking
        if 'RATE_LIMITED' in app.config:
            app.config.pop('RATE_LIMITED')
        if 'RATE_LIMIT_TIME' in app.config:
            app.config.pop('RATE_LIMIT_TIME')
        
        # Delete existing responses
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
        
        # Clear session data
        session.pop('simulation_phase', None)
        session.pop('current_email_id', None)
        session.pop('simulation_id', None)
        
        # Start fresh
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session.modified = True
        
        print(f"[RESET] Created new simulation ID: {new_simulation_id}")
        
        # Reset rate limit tracking
        if 'RATE_LIMITED' in app.config:
            app.config.pop('RATE_LIMITED')
        if 'RATE_LIMIT_TIME' in app.config:
            app.config.pop('RATE_LIMIT_TIME')
        
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
        "simulation_id": session.get('simulation_id')
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
        "Database Tables": [table for table in db.metadata.tables.keys()],
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
    app.run(debug=True)