"""
Analysis phase routes for CyberVantage.
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.utils.auth import token_required
from app.services.ai_service import get_analysis

bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@bp.route('/performance', methods=['GET'])
@token_required
def get_performance():
    """
    Get user's performance analytics.
    """
    from app.models.user import User
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Calculate performance metrics
    learning_progress = user.learning_progress or {}
    simulation_results = user.simulation_results or {}
    
    completed_modules = sum(1 for progress in learning_progress.values() if progress.get('completed', False))
    total_modules = 5  # Based on our learning modules
    
    avg_score = 0
    if learning_progress:
        scores = [progress.get('score', 0) for progress in learning_progress.values()]
        avg_score = sum(scores) / len(scores) if scores else 0
    
    performance = {
        'learning_progress': {
            'completed_modules': completed_modules,
            'total_modules': total_modules,
            'completion_percentage': (completed_modules / total_modules) * 100 if total_modules > 0 else 0,
            'average_score': round(avg_score, 2)
        },
        'simulation_progress': {
            'completed_simulations': len(simulation_results),
            'success_rate': 75,  # Placeholder
            'areas_of_strength': ['Phishing Detection', 'Risk Assessment'],
            'areas_for_improvement': ['Incident Response', 'Network Security']
        },
        'overall_metrics': {
            'total_time_spent': sum(progress.get('time_spent', 0) for progress in learning_progress.values()),
            'skill_level': 'Intermediate' if avg_score >= 70 else 'Beginner' if avg_score >= 50 else 'Novice',
            'last_activity': user.last_login.isoformat() if user.last_login else None
        }
    }
    
    return jsonify({'performance': performance}), 200

@bp.route('/recommendations', methods=['GET'])
@token_required
def get_recommendations():
    """
    Get personalized learning recommendations.
    """
    from app.models.user import User
    from app.services.ai_service import get_ai_response
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Generate AI-powered recommendations
    learning_data = user.learning_progress or {}
    prompt = f"Based on a cybersecurity student's learning progress: {learning_data}, provide 3-5 personalized recommendations for further learning and skill development."
    
    ai_recommendations = get_ai_response(prompt, max_tokens=300)
    
    # Fallback recommendations
    default_recommendations = [
        {
            'title': 'Advanced Phishing Detection',
            'description': 'Enhance your ability to identify sophisticated phishing attempts',
            'priority': 'high',
            'estimated_time': '20 minutes'
        },
        {
            'title': 'Incident Response Procedures',
            'description': 'Learn structured approaches to handling security incidents',
            'priority': 'medium',
            'estimated_time': '30 minutes'
        },
        {
            'title': 'Network Security Fundamentals',
            'description': 'Build understanding of network-based security controls',
            'priority': 'medium',
            'estimated_time': '25 minutes'
        }
    ]
    
    recommendations = {
        'ai_recommendations': ai_recommendations if ai_recommendations else "Focus on completing remaining learning modules and practice with simulation exercises.",
        'structured_recommendations': default_recommendations,
        'generated_at': str(datetime.utcnow())
    }
    
    return jsonify({'recommendations': recommendations}), 200

@bp.route('/certificate', methods=['POST'])
@token_required
def generate_certificate():
    """
    Generate completion certificate for the user.
    """
    from app.models.user import User
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has completed minimum requirements
    learning_progress = user.learning_progress or {}
    completed_modules = sum(1 for progress in learning_progress.values() if progress.get('completed', False))
    
    if completed_modules < 3:  # Minimum 3 modules required
        return jsonify({'error': 'Minimum 3 learning modules must be completed to generate certificate'}), 400
    
    # Generate certificate data
    certificate_data = {
        'certificate_id': f'CV-{user_id}-{int(datetime.utcnow().timestamp())}',
        'user_name': user.username,
        'completion_date': str(datetime.utcnow().date()),
        'modules_completed': completed_modules,
        'overall_score': 85,  # Placeholder calculation
        'certificate_type': 'Cybersecurity Fundamentals'
    }
    
    # In a real application, you would generate a PDF or image here
    certificate_url = f'/certificates/{certificate_data["certificate_id"]}.pdf'
    
    return jsonify({
        'certificate_url': certificate_url,
        'certificate_data': certificate_data,
        'message': 'Certificate generated successfully'
    }), 200