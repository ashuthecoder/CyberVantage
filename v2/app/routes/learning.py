"""
Learning phase routes for CyberVantage.
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.utils.auth import token_required
from app.services.ai_service import get_ai_response

bp = Blueprint('learning', __name__, url_prefix='/api/learning')

@bp.route('/modules', methods=['GET'])
@token_required
def get_modules():
    """
    Get available learning modules.
    """
    modules = [
        {
            'id': 'cybersecurity_basics',
            'title': 'Cybersecurity Fundamentals',
            'description': 'Learn the basics of cybersecurity, including common threats and defense strategies.',
            'duration': '30 minutes',
            'difficulty': 'beginner',
            'topics': ['Security Principles', 'Threat Landscape', 'Risk Assessment', 'Security Controls']
        },
        {
            'id': 'phishing_awareness',
            'title': 'Phishing Awareness',
            'description': 'Understand how to identify and respond to phishing attacks.',
            'duration': '25 minutes',
            'difficulty': 'beginner',
            'topics': ['Email Security', 'Social Engineering', 'Phishing Indicators', 'Response Procedures']
        },
        {
            'id': 'malware_analysis',
            'title': 'Malware Analysis',
            'description': 'Learn techniques for analyzing and understanding malicious software.',
            'duration': '45 minutes',
            'difficulty': 'intermediate',
            'topics': ['Malware Types', 'Analysis Tools', 'Behavioral Analysis', 'Mitigation Strategies']
        },
        {
            'id': 'network_security',
            'title': 'Network Security',
            'description': 'Explore network security concepts and protection mechanisms.',
            'duration': '40 minutes',
            'difficulty': 'intermediate',
            'topics': ['Network Protocols', 'Firewalls', 'Intrusion Detection', 'VPNs']
        },
        {
            'id': 'incident_response',
            'title': 'Incident Response',
            'description': 'Learn how to respond to and manage cybersecurity incidents.',
            'duration': '35 minutes',
            'difficulty': 'advanced',
            'topics': ['Incident Lifecycle', 'Containment', 'Forensics', 'Recovery Procedures']
        }
    ]
    return jsonify({'modules': modules, 'count': len(modules)}), 200

@bp.route('/content/<module_id>', methods=['GET'])
@token_required
def get_content(module_id):
    """
    Get content for a specific learning module.
    """
    from app.services.ai_service import get_ai_response
    
    # Generate learning content using Azure OpenAI
    prompt = f"Create comprehensive educational content for the cybersecurity topic: {module_id.replace('_', ' ')}. Include key concepts, examples, and practical tips."
    
    ai_content = get_ai_response(prompt, max_tokens=800)
    
    if not ai_content:
        # Fallback content
        ai_content = f"Educational content for {module_id.replace('_', ' ')} topic. This module covers essential concepts and practical applications in cybersecurity."
    
    content = {
        'module_id': module_id,
        'content': ai_content,
        'generated_at': str(datetime.utcnow()),
        'interactive_elements': [
            {'type': 'quiz', 'questions': 3},
            {'type': 'scenario', 'count': 2}
        ]
    }
    
    return jsonify({'content': content}), 200

@bp.route('/progress', methods=['POST'])
@token_required
def update_progress():
    """
    Update user's learning progress.
    """
    from app.models.user import User, db
    
    data = request.get_json()
    if not data or 'module_id' not in data:
        return jsonify({'error': 'Module ID is required'}), 400
    
    # Get user from session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Update progress
    module_id = data['module_id']
    progress_data = data.get('progress', {})
    
    if not user.learning_progress:
        user.learning_progress = {}
    
    user.learning_progress[module_id] = {
        'completed': progress_data.get('completed', False),
        'score': progress_data.get('score', 0),
        'time_spent': progress_data.get('time_spent', 0),
        'last_accessed': str(datetime.utcnow())
    }
    
    db.session.commit()
    
    return jsonify({'message': 'Progress updated successfully', 'progress': user.learning_progress}), 200