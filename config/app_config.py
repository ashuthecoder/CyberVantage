"""
Flask app configuration and initialization
"""
import os
import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
    """Create and configure Flask app"""
    # Ensure logs directory exists (fallback to /tmp on serverless)
    try:
        os.makedirs('logs', exist_ok=True)
        app_log_dir = 'logs'
    except Exception:
        try:
            os.makedirs('/tmp/logs', exist_ok=True)
            app_log_dir = '/tmp/logs'
        except Exception:
            app_log_dir = None
    
    # Load environment variables
    load_dotenv()
    
    # Create Flask app with correct paths
    # Get the absolute path to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_path = os.path.join(project_root, 'templates')
    static_path = os.path.join(project_root, 'static')
    
    app = Flask('main', 
                template_folder=templates_path, 
                static_folder=static_path)
    
    # Config - Security hardened
    # Generate secure random secrets if not provided via environment
    import secrets
    
    flask_secret = os.getenv("FLASK_SECRET")
    if not flask_secret or flask_secret == "dev_secret":
        flask_secret = secrets.token_urlsafe(32)
        if not os.getenv("FLASK_SECRET"):
            print("⚠️  WARNING: FLASK_SECRET not set. Using generated secret. Set FLASK_SECRET environment variable for production.")
    
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or jwt_secret == "jwt_secret":
        jwt_secret = secrets.token_urlsafe(32)
        if not os.getenv("JWT_SECRET"):
            print("⚠️  WARNING: JWT_SECRET not set. Using generated secret. Set JWT_SECRET environment variable for production.")
    
    csrf_secret = os.getenv("CSRF_SECRET")
    if not csrf_secret or csrf_secret == "csrf_secret":
        csrf_secret = secrets.token_urlsafe(32)
        if not os.getenv("CSRF_SECRET"):
            print("⚠️  WARNING: CSRF_SECRET not set. Using generated secret. Set CSRF_SECRET environment variable for production.")
    
    app.config['SECRET_KEY'] = flask_secret
    app.config['JWT_SECRET_KEY'] = jwt_secret
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///users.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_SECRET_KEY'] = csrf_secret
    
    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Enable XSS filtering
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Only send Referrer header to same origin
        response.headers['Referrer-Policy'] = 'same-origin'
        # Strict transport security (uncomment for HTTPS)
        # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Check current date warning
    current_time = datetime.datetime.now()
    if current_time.year > 2024:
        print(f"⚠️ WARNING: Your system date appears to be set to the future: {current_time}")
        print("   This may cause issues with authentication tokens and cookies.")
    
    # Encryption key for sensitive DB fields - Security hardened
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    if not ENCRYPTION_KEY:
        # Generate a new key and warn user to save it for production
        ENCRYPTION_KEY = Fernet.generate_key()
        print("⚠️  WARNING: ENCRYPTION_KEY not set. Generated new key for this session.")
        print(f"   For production, set ENCRYPTION_KEY={ENCRYPTION_KEY.decode()} in your environment.")
        print("   Without this key, previously encrypted data cannot be decrypted!")
    elif isinstance(ENCRYPTION_KEY, str):
        ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
    
    app.config['FERNET'] = Fernet(ENCRYPTION_KEY)
    
    return app