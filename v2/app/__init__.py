"""
CyberVantage App Initialization.
"""
from flask import Flask

def create_app(config_class=None):
    """
    Create and configure an instance of the Flask application.
    """
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Configure the app
    if config_class:
        app.config.from_object(config_class)
    
    # Register blueprints
    from app.routes import auth, learning, simulation, analysis, threats
    app.register_blueprint(auth.bp)
    app.register_blueprint(learning.bp)
    app.register_blueprint(simulation.bp)
    app.register_blueprint(analysis.bp)
    app.register_blueprint(threats.bp)
    
    # Add index route
    @app.route('/')
    def index():
        return """
        <html>
            <head>
                <title>CyberVantage</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
                    h1 { color: #2c3e50; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .api-list { text-align: left; background: #f8f9fa; padding: 15px; border-radius: 5px; }
                    .api-item { margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome to CyberVantage</h1>
                    <p>Cybersecurity Training and Simulation Platform</p>
                    <div class="api-list">
                        <h2>Available API Endpoints:</h2>
                        <div class="api-item">/api/auth - Authentication endpoints</div>
                        <div class="api-item">/api/learning - Learning phase endpoints</div>
                        <div class="api-item">/api/simulation - Simulation phase endpoints</div>
                        <div class="api-item">/api/analysis - Analysis phase endpoints</div>
                        <div class="api-item">/api/threats - Threat checking endpoints</div>
                    </div>
                </div>
            </body>
        </html>
        """
    
    return app