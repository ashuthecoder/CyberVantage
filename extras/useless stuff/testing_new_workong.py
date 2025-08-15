import flask
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
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
import markdown  # Added markdown library import
import re  # For regex pattern matching

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

# Configure Google Generative AI (Gemini) - AFTER loading env vars
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f"✓ API key loaded successfully: {GOOGLE_API_KEY[:4]}...{GOOGLE_API_KEY[-4:]}")
else:
    print("Warning: GOOGLE_API_KEY not found. AI features will be limited.")

# Check current date - warning for future dates
current_time = datetime.datetime.now()
if current_time.year > 2024:  # Adjust as needed
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

# Simulation Models - BEFORE app.run()
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
    
    # Relationship with User
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

# Token required decorator for protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        
        try:
            # Decode the token
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

# Helper functions for AI email generation and evaluation

def generate_ai_email(user_name, previous_responses):
    if not GOOGLE_API_KEY:
        # Fallback if API key is not configured
        return default_email()
    
    # Create a prompt based on user's performance
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
    
    # Safety settings as before
    try:
        # Generate the email
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt)
        
        # Debug: print response type and structure
        print(f"Response type: {type(response)}")
        print(f"Response dir: {dir(response)}")
        
        # Extract text from response based on its structure
        content = None
        
        # Method 1: Try accessing candidates if available
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                if parts and hasattr(parts[0], 'text'):
                    content = parts[0].text
                    print("Extracted text from response.candidates[0].content.parts[0].text")
        
        # Method 2: Try accessing parts directly if available
        if not content and hasattr(response, 'parts') and response.parts:
            parts = response.parts
            if parts and hasattr(parts[0], 'text'):
                content = parts[0].text
                print("Extracted text from response.parts[0].text")
        
        # Method 3: Try the text property as a last resort
        if not content and hasattr(response, 'text'):
            content = response.text
            print("Extracted text from response.text")
        
        # Method 4: Try __str__ method
        if not content:
            content = str(response)
            print("Extracted text using str(response)")
        
        if not content:
            raise ValueError("Could not extract content from response")
        
        print(f"Extracted content: {content[:100]}...")
        
        # Continue with parsing as before
        try:
            sender = content.split("Sender: ")[1].split("\n")[0].strip()
            subject = content.split("Subject: ")[1].split("\n")[0].strip()
            date = content.split("Date: ")[1].split("\n")[0].strip()
            email_content = content.split("Content: ")[1].split("Is_spam:")[0].strip()
            is_spam = "true" in content.split("Is_spam: ")[1].lower()
            
            return {
                "sender": sender,
                "subject": subject,
                "date": date,
                "content": email_content,
                "is_spam": is_spam
            }
        except Exception as parse_error:
            print(f"Parse error: {parse_error}")
            return default_email()
            
    except Exception as e:
        print(f"Generation error: {e}")
        return default_email()

def default_email():
    """Return a default email when generation fails"""
    templates = [
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
        }
    ]
    
    template = random.choice(templates)
    return {
        "sender": template["sender"],
        "subject": template["subject"],
        "date": datetime.datetime.now().strftime("%B %d, %Y"),
        "content": template["content"],
        "is_spam": template["is_spam"]
    }

def _fallback_email_from_error(reason):
    """
    Produce a deterministic but varied fallback email explaining the generation issue.
    """
    print(f"[AI EMAIL] Using fallback due to: {reason}")
    phishing = random.choice([True, False])
    if phishing:
        return {
            "sender": f"alert-{random.randint(100,999)}@secure-update-center.com",
            "subject": "Action Required: Verify Account Information",
            "date": datetime.datetime.now().strftime("%B %d, %Y"),
            "content": (
                "<p>This is a phishing training fallback email.</p>"
                "<p><strong>Reason AI generation failed:</strong> "
                f"{flask.escape(reason)}</p>"
                "<p>Red flags were intentionally added for training purposes.</p>"
            ),
            "is_spam": True
        }
    else:
        return {
            "sender": f"updates-{random.randint(100,999)}@legit-service.com",
            "subject": "Service Update Notification",
            "date": datetime.datetime.now().strftime("%B %d, %Y"),
            "content": (
                "<p>This is a legitimate training fallback email.</p>"
                "<p><strong>Reason AI generation failed:</strong> "
                f"{flask.escape(reason)}</p>"
                "<p>No phishing indicators are intentionally present.</p>"
            ),
            "is_spam": False
        }
def evaluate_explanation(email_content, is_spam, user_response, user_explanation):
    # Check for recent rate limit errors
    rate_limited = app.config.get('RATE_LIMITED', False)
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0)
    current_time = datetime.datetime.now().timestamp()
    
    # If we hit a rate limit in the last 10 minutes, use fallback
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"Using fallback due to recent rate limit ({int((current_time - rate_limit_time))} seconds ago)")
        correct = user_response == is_spam
        base_score = 8 if correct else 3
        return {
            "feedback": f"<p>The user's conclusion was {'correct' if correct else 'incorrect'}.</p><p>This is placeholder feedback because the Gemini API rate limit has been reached. Please try again in a few minutes.</p>",
            "score": base_score
        }
    
    if not GOOGLE_API_KEY:
        # Fallback if API key is not configured
        correct = user_response == is_spam
        base_score = 8 if correct else 3
        return {
            "feedback": f"<p>The user's conclusion was {'correct' if correct else 'incorrect'}.</p><p>This is placeholder feedback because the Gemini API is not configured.</p>",
            "score": base_score
        }
        
    # Create a prompt for evaluation
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
        # Generate the evaluation
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content(prompt)
        
        # Format the AI response with Markdown
        ai_text = response.text
        
        # Debug: Print the first 200 chars of raw response
        print(f"Raw AI response (first 200 chars): {ai_text[:200]}")
        
        # Pre-process text to ensure proper Markdown formatting
        # First, clean up any potential formatting issues
        ai_text = ai_text.strip()
        
        # Handle numbered sections - convert them to proper markdown headers if needed
        for i in range(1, 6):
            # Replace different variations of numbered items with consistent markdown headers
            ai_text = re.sub(r"^" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            ai_text = re.sub(r"^" + str(i) + r"\)\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            # If the AI already used headers but with wrong level, standardize them
            ai_text = re.sub(r"^#{1,5}\s+" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
        
        # Enhance formatting for bulletpoints and emphasis
        # Make sure bullets have proper spacing
        ai_text = re.sub(r"^\*\s*(?=\S)", "* ", ai_text, flags=re.MULTILINE)
        # Ensure double asterisks for bold text have proper spacing
        ai_text = re.sub(r"(?<!\*)\*\*(?=\S)", "** ", ai_text)
        ai_text = re.sub(r"(?<=\S)\*\*(?!\*)", " **", ai_text)
        
        # Add extra line breaks to ensure proper paragraph separation
        ai_text = re.sub(r"(?<=[.!?])\s+(?=[A-Z])", "\n\n", ai_text)
        
        # Ensure proper line breaks before headers
        ai_text = re.sub(r"(?<=[^\n])(?=^##)", "\n\n", ai_text, flags=re.MULTILINE)
        
        # Debug: Print the processed markdown
        print(f"Processed markdown text (first 200 chars): {ai_text[:200]}")
        
        # Convert Markdown to HTML with extensions for better formatting
        try:
            # Use markdown extensions for better HTML output
            # 'extra' includes tables, fenced_code, footnotes, and more
            formatted_html = markdown.markdown(ai_text, extensions=['extra'])
        except Exception as md_error:
            print(f"Markdown conversion error: {md_error}")
            # Fallback to basic conversion
            formatted_html = markdown.markdown(ai_text)
        
        # Additional HTML cleanup
        # Ensure proper spacing for list items
        formatted_html = formatted_html.replace("<li>", "<li style='margin-bottom: 8px;'>")
        # Add styling for headers
        formatted_html = formatted_html.replace("<h2>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
        formatted_html = formatted_html.replace("</h2>", "</h3>")
        # Make strong tags more prominent
        formatted_html = formatted_html.replace("<strong>", "<strong style='color: #2a3f54;'>")
        
        # Debug: Print the resulting HTML
        print(f"HTML output (first 200 chars): {formatted_html[:200]}")
        
        # Calculate a score
        if user_response == is_spam:
            base_score = 8  # Base score for correct conclusion
        else:
            base_score = 3  # Base score for incorrect conclusion
        
        # Extract the actual score from AI if possible
        try:
            ai_score_text = ai_text.split("scale of 1-10")[1].split("\n")[0]
            ai_score = int(''.join(filter(str.isdigit, ai_score_text)))
            if 1 <= ai_score <= 10:
                score = ai_score
            else:
                score = base_score
        except:
            score = base_score
        
        return {
            "feedback": formatted_html,
            "score": score
        }
    except Exception as e:
        error_str = str(e)
        print(f"Evaluation error: {error_str}")
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            # Record rate limit for future calls
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = current_time
            print(f"Rate limit detected: {error_str}")
        
        # Fallback if AI fails
        correct = user_response == is_spam
        base_score = 8 if correct else 3
        return {
            "feedback": f"<p>The user's conclusion was {'correct' if correct else 'incorrect'}.</p><p>Error in AI evaluation: {str(e)}</p>",
            "score": base_score
        }

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
        
        # Store token in session instead of returning it
        session['token'] = token
        session['user_name'] = user.name
        
        # Redirect to dashboard
        return redirect(url_for('dashboard'))

    return render_template("login.html")

# Dashboard route
@app.route('/dashboard')
@token_required
def dashboard(current_user):
    return render_template('dashboard.html', username=current_user.name)

# Learn section route
@app.route('/learn')
@token_required
def learn(current_user):
    return render_template('learn.html', username=current_user.name)

# Simulation routes
@app.route('/simulate', methods=['GET'])
@token_required
def simulate(current_user):
    # Initialize simulation if first time
    if 'simulation_phase' not in session:
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        
        # Store predefined emails in database if not already
        for email in predefined_emails:
            # Check if email already exists
            existing = SimulationEmail.query.filter_by(id=email['id']).first()
            if not existing:
                new_email = SimulationEmail(
                    id=email['id'],
                    sender=email['sender'],
                    subject=email['subject'],
                    date=email['date'],
                    content=email['content'],
                    is_spam=email['is_spam'],
                    is_predefined=True
                )
                db.session.add(new_email)
        db.session.commit()
    
    # Get current phase and email from session
    phase = session.get('simulation_phase', 1)
    current_email_id = session.get('current_email_id', 1)
    
    # Check if simulation is complete
    if (phase == 1 and current_email_id > 5) or (phase == 2 and current_email_id > 10):
        return render_template('simulate.html', phase='complete', username=current_user.name)
    
    # Get the appropriate email
    if phase == 1:
        # Use predefined emails for phase 1
        email = SimulationEmail.query.get(current_email_id)
        if not email:
            email_data = predefined_emails[current_email_id - 1]
            email = SimulationEmail(
                id=email_data['id'],
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
        # Phase 2: Get or generate AI email
        email = SimulationEmail.query.get(current_email_id)
        if not email:
            # Get performance from phase 1
            previous_responses = SimulationResponse.query.filter_by(
                user_id=current_user.id
            ).filter(SimulationResponse.email_id < 6).all()
            
            correct_count = sum(1 for r in previous_responses if r.user_response == r.is_spam_actual)
            performance_summary = f"The user correctly identified {correct_count} out of 5 emails in phase 1."
            
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
    
    return render_template(
        'simulate.html', 
        phase=phase, 
        current_email=current_email_id, 
        email=email,
        username=current_user.name,
        api_key_available=bool(GOOGLE_API_KEY)  # Add this for template messages
    )

@app.route('/submit_simulation', methods=['POST'])
@token_required
def submit_simulation(current_user):
    email_id = int(request.form.get('email_id'))
    phase = int(request.form.get('phase'))
    is_spam_response = request.form.get('is_spam') == 'true'
    explanation = request.form.get('explanation', '')
    
    # Get the email
    email = SimulationEmail.query.get(email_id)
    if not email:
        return redirect(url_for('simulate'))
    
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
        return redirect(url_for('simulation_feedback', email_id=email_id))
    
    # Update session for next email
    next_email_id = email_id + 1
    
    # Check if we need to move to the next phase
    if phase == 1 and next_email_id > 5:
        session['simulation_phase'] = 2
        session['current_email_id'] = 6
    else:
        session['current_email_id'] = next_email_id
    
    # If phase 2 is complete, redirect to results
    if phase == 2 and next_email_id > 10:
        return redirect(url_for('simulation_results'))
    
    return redirect(url_for('simulate'))

@app.route('/simulation_feedback/<int:email_id>')
@token_required
def simulation_feedback(current_user, email_id):
    # Get the user's response
    response = SimulationResponse.query.filter_by(
        user_id=current_user.id,
        email_id=email_id
    ).first()
    
    if not response:
        return redirect(url_for('simulate'))
    
    # Ensure the feedback is treated as HTML
    if response.ai_feedback:
        # Diagnostic check - look for HTML tags in the feedback
        if not response.ai_feedback.strip().startswith('<'):
            print(f"Warning: Feedback doesn't appear to be HTML: {response.ai_feedback[:50]}...")
            # Try to wrap plain text in paragraph tags
            response.ai_feedback = f"<p>{response.ai_feedback}</p>"
    
    return render_template(
        'simulation_feedback.html',
        response=response,
        username=current_user.name
    )

@app.route('/simulation_results')
@token_required
def simulation_results(current_user):
    # Get all responses for this user
    responses = SimulationResponse.query.filter_by(user_id=current_user.id).all()
    
    # Calculate statistics
    phase1_correct = sum(1 for r in responses if r.email_id <= 5 and r.user_response == r.is_spam_actual)
    phase2_correct = sum(1 for r in responses if r.email_id > 5 and r.user_response == r.is_spam_actual)
    
    phase2_scores = [r.score for r in responses if r.email_id > 5 and r.score is not None]
    avg_score = sum(phase2_scores) / len(phase2_scores) if phase2_scores else 0
    
    # Reset simulation for potential future attempts
    session.pop('simulation_phase', None)
    session.pop('current_email_id', None)
    
    return render_template(
        'simulation_results.html',
        phase1_correct=phase1_correct,
        phase1_total=5,
        phase2_correct=phase2_correct,
        phase2_total=5,
        avg_score=avg_score,
        responses=responses,
        username=current_user.name
    )

# Analysis section route
@app.route('/analysis')
@token_required
def analysis(current_user):
    return render_template('analysis.html', username=current_user.name)

# Logout route
@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('user_name', None)
    return redirect(url_for('login'))

# Utility route to encrypt sensitive data
@app.route('/encrypt/<string:data>')
def encrypt_data(data):
    encrypted = fernet.encrypt(data.encode())
    return {"encrypted": encrypted.decode()}

@app.route('/decrypt/<string:data>')
def decrypt_data(data):
    decrypted = fernet.decrypt(data.encode()).decode()
    return {"decrypted": decrypted}

@app.route('/restart_simulation')
@token_required
def restart_simulation(current_user):
    # Clear all simulation progress from the session
    session.pop('simulation_phase', None)
    session.pop('current_email_id', None)
    
    # Reset rate limit tracking
    app.config.pop('RATE_LIMITED', None)
    app.config.pop('RATE_LIMIT_TIME', None)
    
    # Optional: Delete previous simulation responses to start completely fresh
    # This will remove all prior responses for this user
    SimulationResponse.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    
    # Redirect to simulation page to start over
    return redirect(url_for('simulate'))

# Debug route to check environment and status
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
            "HarmCategory Keys": [attr for attr in dir(HarmCategory) if not attr.startswith('_')],
        }
    }
    
    return jsonify(info)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)