"""
Simulation phase routes for CyberVantage.
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.utils.auth import token_required
from app.services.ai_service import get_simulation_scenario

bp = Blueprint('simulation', __name__, url_prefix='/api/simulation')

@bp.route('/scenarios', methods=['GET'])
@token_required
def get_scenarios():
    """
    Get available simulation scenarios.
    """
    scenarios = [
        {
            'id': 'phishing_email',
            'title': 'Phishing Email Detection',
            'description': 'Identify and respond to suspicious emails',
            'difficulty': 'beginner',
            'estimated_time': '10-15 minutes'
        },
        {
            'id': 'malware_analysis',
            'title': 'Malware Analysis',
            'description': 'Analyze suspicious files and identify threats',
            'difficulty': 'intermediate',
            'estimated_time': '15-20 minutes'
        },
        {
            'id': 'network_intrusion',
            'title': 'Network Intrusion Detection',
            'description': 'Identify and respond to network attacks',
            'difficulty': 'advanced',
            'estimated_time': '20-30 minutes'
        },
        {
            'id': 'social_engineering',
            'title': 'Social Engineering Defense',
            'description': 'Respond to social engineering attacks',
            'difficulty': 'intermediate',
            'estimated_time': '10-15 minutes'
        }
    ]
    return jsonify({'scenarios': scenarios}), 200

@bp.route('/start/<scenario_id>', methods=['POST'])
@token_required
def start_simulation(scenario_id):
    """
    Start a specific simulation scenario.
    """
    from app.services.ai_service import get_simulation_scenario
    import uuid
    
    # Generate simulation scenario using Azure OpenAI
    scenario_content = get_simulation_scenario(
        difficulty="medium", 
        category=scenario_id.replace('_', ' ')
    )
    
    if not scenario_content:
        return jsonify({'error': 'Failed to generate scenario'}), 500
    
    simulation_data = {
        'simulation_id': str(uuid.uuid4()),
        'scenario_id': scenario_id,
        'content': scenario_content,
        'started_at': str(datetime.utcnow()),
        'status': 'active'
    }
    
    return jsonify({'simulation': simulation_data, 'message': 'Simulation started'}), 200

@bp.route('/submit/<simulation_id>', methods=['POST'])
@token_required
def submit_simulation(simulation_id):
    """
    Submit user's actions in a simulation for evaluation.
    """
    from app.services.ai_service import get_analysis
    
    data = request.get_json()
    if not data or 'user_actions' not in data:
        return jsonify({'error': 'User actions required'}), 400
    
    user_actions = data['user_actions']
    scenario = data.get('scenario', 'cybersecurity scenario')
    
    # Get analysis from Azure OpenAI
    analysis_result = get_analysis(user_actions, scenario)
    
    if not analysis_result:
        return jsonify({'error': 'Failed to analyze submission'}), 500
    
    evaluation = {
        'simulation_id': simulation_id,
        'analysis': analysis_result,
        'submitted_at': str(datetime.utcnow()),
        'score': 75,  # Placeholder - could be extracted from AI analysis
        'recommendations': [
            'Review phishing indicators',
            'Practice incident response procedures'
        ]
    }
    
    return jsonify({'evaluation': evaluation, 'message': 'Simulation evaluated'}), 200