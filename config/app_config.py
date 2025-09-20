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
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
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
    
    # Config
    app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET", "dev_secret")
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET", "jwt_secret")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///users.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_SECRET_KEY'] = os.getenv("CSRF_SECRET", "csrf_secret")
    
    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    
    # Check current date warning
    current_time = datetime.datetime.now()
    if current_time.year > 2024:
        print(f"⚠️ WARNING: Your system date appears to be set to the future: {current_time}")
        print("   This may cause issues with authentication tokens and cookies.")
    
    # Encryption key for sensitive DB fields
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    
    if ENCRYPTION_KEY:
        # Validate the provided encryption key
        try:
            # Try to create Fernet instance with the provided key
            fernet_instance = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)
            app.config['FERNET'] = fernet_instance
            print("✓ Using ENCRYPTION_KEY from environment")
        except Exception as e:
            # If the provided key is invalid, generate a new one and warn the user
            print(f"⚠️  WARNING: Invalid ENCRYPTION_KEY in environment: {e}")
            print("⚠️  Generating a new encryption key. Please update your .env file with:")
            new_key = Fernet.generate_key()
            print(f"   ENCRYPTION_KEY={new_key.decode()}")
            app.config['FERNET'] = Fernet(new_key)
    else:
        # Generate a new key if none provided
        print("⚠️  No ENCRYPTION_KEY found in environment. Generating a new one.")
        print("   For production use, please add this to your .env file:")
        new_key = Fernet.generate_key()
        print(f"   ENCRYPTION_KEY={new_key.decode()}")
        app.config['FERNET'] = Fernet(new_key)
    
    return app