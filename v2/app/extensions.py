"""
Flask extensions for CyberVantage.
"""
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Configure login manager
login_manager.login_view = 'web.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'