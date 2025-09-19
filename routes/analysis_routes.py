"""
Analysis and monitoring routes
"""
import os
import datetime
import sqlite3
from flask import Blueprint, render_template, jsonify, request
from routes.auth_routes import token_required
from models.database import User, SimulationEmail, SimulationResponse, get_simulation_id_for_email

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/learn')
@token_required
def learn(current_user):
    return render_template('learn.html', username=current_user.name)

@analysis_bp.route('/analysis')
@token_required
def analysis(current_user):
    return render_template('analysis.html', username=current_user.name)

@analysis_bp.route('/api_monitor')
@token_required
def api_monitor(current_user):
    """View API usage statistics - accessible to all authenticated users"""
    from pyFunctions.api_logging import get_api_stats
    
    # No user-specific check, all authenticated users can access
    return jsonify(get_api_stats())

@analysis_bp.route('/api_source_stats')
@token_required
def api_source_stats(current_user):
    """View detailed API statistics by source - accessible to all authenticated users"""
    from pyFunctions.api_logging import get_api_source_stats
    
    # Get query parameters
    source = request.args.get('source')  # Optional filter by API source (AZURE)
    hours = request.args.get('hours', 24, type=int)  # Time window in hours
    
    return jsonify(get_api_source_stats(source=source, time_window_hours=hours))

@analysis_bp.route('/view_api_logs')
@token_required
def view_api_logs(current_user):
    """View API logs - accessible to all authenticated users"""
    from pyFunctions.api_logging import LOG_FILE_PATH, parse_log_file
    
    # No user-specific check, all authenticated users can access
    log_analysis = parse_log_file()
    
    # Format as HTML
    log_html = "<h2>API Request Logs Analysis</h2>"
    
    if "error" in log_analysis:
        return f"<h2>Error</h2><p>{log_analysis['error']}</p>"
        
    success_rate = log_analysis["success_rate"]
    success_color = "green" if success_rate > 90 else "orange" if success_rate > 70 else "red"
    
    log_html += f"<p>Total log entries: <strong>{log_analysis['total_entries']}</strong></p>"
    log_html += f"<p>Success rate: <strong style='color:{success_color}'>{success_rate:.1f}%</strong></p>"
    
    log_html += "<h3>Requests by Function</h3>"
    log_html += "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
    log_html += "<tr><th>Function</th><th>Successful</th><th>Failed</th><th>Total</th><th>Success Rate</th></tr>"
    
    for func, stats in log_analysis["function_stats"].items():
        total = stats['success'] + stats['failure']
        success_rate = (stats['success'] / total) * 100 if total > 0 else 0
        row_color = "rgba(40, 167, 69, 0.1)" if success_rate > 90 else "rgba(255, 193, 7, 0.1)" if success_rate > 70 else "rgba(220, 53, 69, 0.1)"
        
        log_html += f"<tr style='background-color:{row_color}'><td>{func}</td><td>{stats['success']}</td><td>{stats['failure']}</td>"
        log_html += f"<td>{total}</td><td>{success_rate:.1f}%</td></tr>"
    
    log_html += "</table>"
    
    if log_analysis["recent_errors"]:
        log_html += "<h3>Recent Errors</h3>"
        log_html += "<pre style='background-color: #fff3cd; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;'>"
        log_html += "\n".join(log_analysis["recent_errors"])
        log_html += "</pre>"
    
    return log_html

@analysis_bp.route('/debug_simulation')
@token_required
def debug_simulation(current_user):
    """Debug endpoint to see current simulation state"""
    from flask import session, current_app
    
    # Get all emails and responses in the system
    emails = SimulationEmail.query.all()
    responses = SimulationResponse.query.filter_by(user_id=current_user.id).all()

    # Current session state
    session_info = {
        "phase": session.get('simulation_phase'),
        "current_email_id": session.get('current_email_id'),
        "simulation_id": session.get('simulation_id'),
        "phase2_emails_completed": session.get('phase2_emails_completed'),
        "active_phase2_email_id": session.get('active_phase2_email_id'),
    }

    # Format the data
    email_data = []
    for email in emails:
        sim_id = get_simulation_id_for_email(email.id, current_app)
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
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
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

@analysis_bp.route('/debug')
def debug_info():
    from flask import session, current_app
    # Only allow this in debug mode
    if not current_app.debug:
        return "Debug information only available when debug=True"

    info = {
        "Environment Variables": {
            "AZURE_OPENAI_KEY": f"{os.getenv('AZURE_OPENAI_KEY')[:4]}...{os.getenv('AZURE_OPENAI_KEY')[-4:]}" if os.getenv('AZURE_OPENAI_KEY') else "Not set",
            "FLASK_SECRET": f"{os.getenv('FLASK_SECRET')[:4]}...{os.getenv('FLASK_SECRET')[-4:]}" if os.getenv('FLASK_SECRET') else "Using default",
        },
        "Session Data": {k: v for k, v in session.items() if k != 'token'},
        "Database Tables": [table for table in current_app.extensions['sqlalchemy'].db.metadata.tables.keys()],
        "System Time": str(datetime.datetime.now()),
        "API Status": {
            "Rate Limited": current_app.config.get('RATE_LIMITED', False),
            "Rate Limit Time": datetime.datetime.fromtimestamp(current_app.config.get('RATE_LIMIT_TIME', 0)).strftime('%Y-%m-%d %H:%M:%S') if current_app.config.get('RATE_LIMIT_TIME') else "N/A",
        },
        "Database Counts": {
            "Users": User.query.count(),
            "SimulationEmails": SimulationEmail.query.count(),
            "SimulationResponses": SimulationResponse.query.count()
        }
    }

    return jsonify(info)

@analysis_bp.route('/update_schema')
@token_required
def update_schema(current_user):
    """Add missing column to database"""
    from flask import current_app
    from models.database import update_database_schema
    
    try:
        success = update_database_schema(current_app)
        return jsonify({
            "success": success,
            "message": "Database schema updated successfully" if success else "Failed to update database schema"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error updating schema: {str(e)}"
        })