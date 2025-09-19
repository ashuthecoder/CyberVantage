"""
CyberVantage App Initialization.
"""
from flask import Flask, session, render_template
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import BadRequest, Forbidden
from flask_login import LoginManager
from app.models.user import User

def create_app(config_class=None):
    """
    Create and configure an instance of the Flask application.
    """
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Configure the app
    if config_class:
        app.config.from_object(config_class)
    else:
        # Load the default configuration
        from config import Config
        app.config.from_object(Config)
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'web.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf())
    
    # Handle CSRF errors
    @app.errorhandler(Forbidden)
    def handle_csrf_error(e):
        if 'CSRF' in str(e):
            return render_template('error.html', 
                                error="CSRF token validation failed. Please try again.",
                                title="Security Error"), 400
        return e
    
    # Register blueprints
    from app.routes import auth, learning, simulation, analysis, threats, web, web_simulation
    app.register_blueprint(auth.bp)
    app.register_blueprint(learning.bp)
    app.register_blueprint(simulation.bp)
    app.register_blueprint(analysis.bp)
    app.register_blueprint(threats.bp)
    app.register_blueprint(web.bp)
    app.register_blueprint(web_simulation.web_simulation_bp)
    
    return app