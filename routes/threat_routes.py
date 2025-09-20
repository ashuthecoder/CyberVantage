"""
Threat intelligence and security analysis routes
"""
import os
import traceback
from flask import Blueprint, render_template, request, jsonify
from routes.auth_routes import token_required
from pyFunctions.threat_intelligence import ThreatIntelligence
from pyFunctions.phishing_assignment import assign_phishing_creation, evaluate_phishing_creation
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

threat_bp = Blueprint('threat', __name__)

@threat_bp.route('/check_threats')
@token_required
def check_threats(current_user):
    # Get the VirusTotal API key from environment variables
    virustotal_api_key = os.getenv("VIRUS_TOTAL_KEY") or os.getenv("VIRUSTOTAL_API_KEY")
    return render_template('check_threats.html', username=current_user.name, virustotal_api_key=virustotal_api_key)

@threat_bp.route('/deep_search')
@token_required
def deep_search(current_user):
    """Deep search explanation and advanced scanning interface"""
    return render_template('deep_search.html', username=current_user.name)

@threat_bp.route('/api/threat_scan', methods=['POST'])
@token_required
def api_threat_scan(current_user):
    """API endpoint to scan a resource using VirusTotal"""
    try:
        data = request.json
        target = data.get('target', '').strip()
        scan_type = data.get('type', 'url')
        
        if not target:
            return jsonify({"error": "No target provided"}), 400
        
        # Check if VirusTotal API key is configured
        vt_api_key = os.getenv("VIRUSTOTAL_API_KEY")
        if not vt_api_key:
            return jsonify({
                "error": "VirusTotal API key not configured. Please add it to your .env file."
            }), 500
        
        # Initialize ThreatIntelligence with API key
        ti = ThreatIntelligence(vt_api_key)
        
        # Perform scan based on type
        if scan_type == 'url':
            result = ti.scan_url(target)
        elif scan_type == 'ip':
            result = ti.scan_ip(target)
        elif scan_type == 'file':
            result = ti.scan_file_hash(target)
        else:
            return jsonify({"error": f"Unsupported scan type: {scan_type}"}), 400
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[THREAT_SCAN] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500

@threat_bp.route('/api/deep_scan', methods=['POST'])
@token_required
def api_deep_scan(current_user):
    """API endpoint for deep scanning URLs with multi-hop analysis"""
    try:
        data = request.json
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Check if VirusTotal API key is configured
        vt_api_key = os.getenv("VIRUS_TOTAL_KEY") or os.getenv("VIRUSTOTAL_API_KEY")
        if not vt_api_key:
            return jsonify({
                "error": "VirusTotal API key not configured. Please add VIRUS_TOTAL_KEY to your .env file."
            }), 500
        
        # Initialize ThreatIntelligence with API key
        ti = ThreatIntelligence(vt_api_key)
        
        # Perform deep scan
        result = ti.deep_scan_url(url)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"[DEEP_SCAN] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Deep scan failed: {str(e)}"}), 500

@threat_bp.route('/api/threat_history', methods=['GET'])
@token_required
def api_threat_history(current_user):
    """API endpoint to get threat scan history"""
    try:
        # Check if VirusTotal API key is configured
        vt_api_key = os.getenv("VIRUS_TOTAL_KEY") or os.getenv("VIRUSTOTAL_API_KEY")
        if not vt_api_key:
            return jsonify([]), 200  # Return empty history if no API key
        
        # Get history from the ThreatIntelligence instance
        ti = ThreatIntelligence(vt_api_key)
        history = ti.get_history()
        
        return jsonify(history)
        
    except Exception as e:
        print(f"[THREAT_HISTORY] Error: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to fetch history: {str(e)}"}), 500

# Phishing Assignment Routes
@threat_bp.route('/phishing_assignment')
@token_required
def get_phishing_assignment(current_user):
    """Display the phishing email creation assignment"""
    try:
        from flask import current_app
        # Get assignment from the phishing assignment module
        # Note: Removed Gemini parameters as requested
        assignment_data = assign_phishing_creation(None, None, current_app)
        
        return render_template(
            'phishing_assignment.html',
            username=current_user.name,
            instructions=assignment_data.get('instructions', ''),
            rubric=assignment_data.get('rubric', [])
        )
    except Exception as e:
        print(f"[PHISHING_ASSIGNMENT] Error loading assignment: {e}")
        traceback.print_exc()
        return render_template(
            'system_message.html',
            title="Error",
            message="Unable to load the phishing assignment. Please try again later.",
            action_text="Return to Dashboard",
            action_url='main.dashboard',
            username=current_user.name
        )

@threat_bp.route('/evaluate_user_phishing', methods=['POST'])
@token_required
def evaluate_user_phishing(current_user):
    """Evaluate the user's phishing email creation"""
    try:
        phishing_email = request.form.get('phishing_email', '').strip()
        
        if not phishing_email:
            return render_template(
                'system_message.html',
                title="Error",
                message="Please provide a phishing email for evaluation.",
                action_text="Try Again",
                action_url='threat.get_phishing_assignment',
                username=current_user.name
            )
        
        from flask import current_app
        # Evaluate the phishing email
        # Note: Removed Gemini parameters as requested
        evaluation_result = evaluate_phishing_creation(phishing_email, None, None, current_app)
        
        return render_template(
            'phishing_evaluation.html',
            username=current_user.name,
            feedback=evaluation_result.get('feedback', 'No feedback available'),
            score=evaluation_result.get('score', 0),
            effectiveness=evaluation_result.get('effectiveness_rating', 'Unknown')
        )
    except Exception as e:
        print(f"[PHISHING_EVALUATION] Error evaluating submission: {e}")
        traceback.print_exc()
        return render_template(
            'system_message.html',
            title="Error", 
            message="Unable to evaluate your phishing email. Please try again later.",
            action_text="Try Again",
            action_url='threat.get_phishing_assignment',
            username=current_user.name
        )