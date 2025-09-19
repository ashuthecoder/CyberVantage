"""
CyberVantage application entry point.
"""
import os
from app import create_app
from app.models.user import db
from config import config

# Get configuration from environment
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config[config_name])

# Initialize database with app context
with app.app_context():
    db.init_app(app)
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)