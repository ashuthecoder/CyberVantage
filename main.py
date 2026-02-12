"""
CyberVantage - Main application entry point
Refactored to use modular structure with focused components
"""
import os
from flask import render_template, redirect, url_for, session
from config.app_config import create_app, db
from config.ai_config import configure_azure_openai
from models.database import update_database_schema
from routes.auth_routes import auth_bp, token_required
from routes.simulation_routes import simulation_bp
from routes.analysis_routes import analysis_bp
from routes.threat_routes import threat_bp
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = create_app()

# Configure AI services (Azure OpenAI only - Gemini removed as requested)
configure_azure_openai(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(simulation_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(threat_bp)

# Main routes that don't fit into specific categories
@app.route('/')
def index():
    """Landing page - redirect to access code page for login flow"""
    # If user is already logged in, go to dashboard
    if session.get('token'):
        return redirect(url_for('dashboard'))
    # If access code already verified, go to login
    if session.get('access_code_verified'):
        return redirect(url_for('auth.login'))
    # Show landing page with button to continue to access code
    return render_template("index.html")

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    # Make sure database schema is updated
    update_database_schema(app)
    return render_template('dashboard.html', username=current_user.name, current_user=current_user)

# Initialize database for serverless environments
with app.app_context():
    try:
        db.create_all()
        update_database_schema(app)
    except Exception as e:
        print(f"Database initialization warning: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_database_schema(app)  # Ensure the schema is updated at startup
    
    # Check if we're in development mode
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    if debug_mode:
        print("🔧 Running in DEVELOPMENT mode with debugging enabled")
        print("   Set FLASK_ENV=production for production deployment")
    
    print(f"🚀 CyberVantage is starting...")
    print(f"📍 Server will be accessible at: http://{host}:{port}")
    print(f"🌐 If running locally, visit: http://localhost:{port}")
    if host != '127.0.0.1':
        print(f"🔗 Network access available at: http://{host}:{port}")
    
    # Disable the reloader to avoid double-execution side-effects in dev
    app.run(debug=debug_mode, host=host, port=port, use_reloader=False)