"""
CyberVantage - Main application entry point
Refactored to use modular structure with focused components
"""
from flask import render_template
from config.app_config import create_app, db
from config.ai_config import configure_azure_openai
from models.database import update_database_schema
from routes.auth_routes import auth_bp, token_required
from routes.simulation_routes import simulation_bp
from routes.analysis_routes import analysis_bp
from routes.threat_routes import threat_bp

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
def welcome():
    return render_template("welcome.html")

@app.route('/test')
def test():
    return "Routing test works!"

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    # Make sure database schema is updated
    update_database_schema(app)
    return render_template('dashboard.html', username=current_user.name)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        update_database_schema(app)  # Ensure the schema is updated at startup
    # Disable the reloader to avoid double-execution side-effects in dev
    app.run(debug=True, use_reloader=False)