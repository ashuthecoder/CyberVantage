"""
Simulation phase routes for CyberVantage.
"""
from flask import Blueprint, request, jsonify, session, current_app
from app.utils.auth import token_required
from app.models.user import User, db
from app.models.simulation import Simulation, SimulationResult
from app.services.ai_service import generate_simulation_email, evaluate_user_action
import datetime
import json
import random
import logging

bp = Blueprint('simulation', __name__, url_prefix='/api/simulation')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email templates for Phase 1 (pre-defined scenarios)
PHASE1_EMAILS = [
    {
        "subject": "Update your payment information",
        "sender": "accounts@amazon-payments.com",
        "content": "Dear customer, we've detected an issue with your payment method. Please update your information by clicking here: <a href='#'>Update Payment</a>",
        "is_phishing": True,
        "explanation": "This is a phishing email. The sender address uses a hyphenated domain (amazon-payments.com) which is not legitimate. The email creates urgency and contains a suspicious link."
    },
    {
        "subject": "Your Netflix subscription is on hold",
        "sender": "support@netflix.com",
        "content": "Your Netflix subscription has been put on hold due to a payment issue. To continue enjoying our service, please verify your payment information by logging into your account through our official website: <a href='https://netflix.com'>Netflix.com</a>",
        "is_phishing": False,
        "explanation": "This is a legitimate email. It directs you to the official Netflix website, doesn't create excessive urgency, and doesn't ask for personal information directly in the email."
    },
    {
        "subject": "Security Alert: Unusual sign-in attempt",
        "sender": "no-reply@accounts.google.com",
        "content": "We detected an unusual sign-in attempt to your Google Account on a Windows device in New York, USA. If this was you, you can safely ignore this email. If not, please secure your account here: <a href='#'>Secure Account</a>",
        "is_phishing": False,
        "explanation": "This is a legitimate security alert from Google. The sender address is correct, and while it contains a link, Google does send such security notifications when unusual activity is detected."
    },
    {
        "subject": "Your package is on its way",
        "sender": "shipping-notification@fedex-delivery.net",
        "content": "Your package #FDX42956781 is on its way. There's a problem with your delivery address. Please correct it immediately: <a href='#'>Update Address</a>",
        "is_phishing": True,
        "explanation": "This is a phishing email. The sender uses a suspicious domain (fedex-delivery.net instead of fedex.com). It creates urgency and contains a suspicious link."
    },
    {
        "subject": "IT Department: Urgent action required",
        "sender": "it-admin@company.com",
        "content": "URGENT: All employees must reset their passwords within 24 hours due to a potential security breach. Click here to reset: <a href='#'>Reset Password</a>. Failure to comply will result in account suspension.",
        "is_phishing": True,
        "explanation": "This is a phishing email. It creates a sense of urgency and fear. Legitimate IT departments typically don't threaten account suspension and would use an official company portal for password resets rather than an email link."
    }
]

@bp.route('/initialize', methods=['POST'])
@token_required
def initialize_simulation():
    """
    Initialize a new simulation for the user.
    """
    try:
        # Get user from environment
        user_id = request.environ.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Clear any existing simulation data
        user = User.query.get(user_id)
        
        # Create a new simulation record
        simulation = Simulation(
            user_id=user.id,
            start_time=datetime.datetime.now(),
            phase=1,
            completion_count=0,
            active_email=None,
            emails_generated=0,
            status="active"
        )
        
        db.session.add(simulation)
        db.session.commit()
        
        return jsonify({
            'simulation_id': simulation.id,
            'phase': simulation.phase,
            'message': 'Simulation initialized successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error initializing simulation: {str(e)}")
        return jsonify({'error': 'Failed to initialize simulation'}), 500

@bp.route('/current', methods=['GET'])
@token_required
def get_current_simulation():
    """
    Get the current active simulation for the user.
    """
    try:
        # Get user from environment
        user_id = request.environ.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        user = User.query.get(user_id)
        simulation = Simulation.query.filter_by(user_id=user.id, status="active").first()
        
        if not simulation:
            return jsonify({'message': 'No active simulation found'}), 404
        
        # If there's no active email, generate one
        if not simulation.active_email:
            if simulation.phase == 1:
                # Phase 1: Use pre-defined scenarios
                if simulation.completion_count < len(PHASE1_EMAILS):
                    email = PHASE1_EMAILS[simulation.completion_count]
                    simulation.active_email = json.dumps(email)
                    db.session.commit()
                else:
                    # Move to phase 2
                    simulation.phase = 2
                    simulation.completion_count = 0
                    simulation.active_email = None
                    db.session.commit()
                    return jsonify({
                        'simulation_id': simulation.id,
                        'phase': simulation.phase,
                        'message': 'Moving to Phase 2',
                        'email': None
                    }), 200
            
            elif simulation.phase == 2:
                # Phase 2: Generate AI email
                if simulation.completion_count < 5:
                    # Generate an AI email
                    try:
                        difficulty = "easy" if simulation.completion_count < 2 else "medium" if simulation.completion_count < 4 else "hard"
                        is_phishing = random.choice([True, False])
                        
                        email_data = generate_simulation_email(difficulty, is_phishing)
                        if email_data:
                            simulation.active_email = json.dumps(email_data)
                            simulation.emails_generated += 1
                            db.session.commit()
                        else:
                            return jsonify({'error': 'Failed to generate email'}), 500
                    except Exception as e:
                        logger.error(f"Error generating AI email: {str(e)}")
                        return jsonify({'error': 'Failed to generate email'}), 500
                else:
                    # Complete simulation
                    simulation.status = "completed"
                    simulation.end_time = datetime.datetime.now()
                    db.session.commit()
                    
                    # Create simulation results
                    results = SimulationResult.query.filter_by(simulation_id=simulation.id).all()
                    correct_answers = sum(1 for r in results if r.is_correct)
                    total_questions = len(results)
                    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
                    
                    return jsonify({
                        'simulation_id': simulation.id,
                        'phase': simulation.phase,
                        'status': 'completed',
                        'score': score,
                        'correct_answers': correct_answers,
                        'total_questions': total_questions,
                        'message': 'Simulation completed'
                    }), 200
        
        # Return the active email
        if simulation.active_email:
            email_data = json.loads(simulation.active_email)
            return jsonify({
                'simulation_id': simulation.id,
                'phase': simulation.phase,
                'email': email_data,
                'completion_count': simulation.completion_count
            }), 200
        else:
            return jsonify({
                'simulation_id': simulation.id,
                'phase': simulation.phase,
                'message': 'No email available',
                'email': None
            }), 200
            
    except Exception as e:
        logger.error(f"Error retrieving simulation: {str(e)}")
        return jsonify({'error': 'Failed to retrieve simulation'}), 500

@bp.route('/submit', methods=['POST'])
@token_required
def submit_simulation():
    """
    Submit user's assessment of an email (phishing or legitimate).
    """
    try:
        # Get user from environment
        user_id = request.environ.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        data = request.get_json()
        user_assessment = data.get('is_phishing')
        explanation = data.get('explanation', '')
        
        if user_assessment is None:
            return jsonify({'error': 'Assessment is required'}), 400
            
        user = User.query.get(user_id)
        simulation = Simulation.query.filter_by(user_id=user.id, status="active").first()
        
        if not simulation or not simulation.active_email:
            return jsonify({'error': 'No active simulation or email found'}), 404
            
        email_data = json.loads(simulation.active_email)
        actual_assessment = email_data.get('is_phishing')
        
        is_correct = (user_assessment == actual_assessment)
        
        # Evaluate the user's explanation if provided
        explanation_feedback = ""
        if explanation and simulation.phase == 2:
            explanation_feedback = evaluate_user_action(
                email_data, 
                user_assessment, 
                explanation
            )
        
        # Save the result
        result = SimulationResult(
            simulation_id=simulation.id,
            email_data=simulation.active_email,
            user_assessment=user_assessment,
            actual_assessment=actual_assessment,
            is_correct=is_correct,
            user_explanation=explanation,
            feedback=explanation_feedback,
            timestamp=datetime.datetime.now()
        )
        
        db.session.add(result)
        
        # Update simulation
        simulation.completion_count += 1
        simulation.active_email = None
        
        db.session.commit()
        
        return jsonify({
            'is_correct': is_correct,
            'actual_assessment': actual_assessment,
            'explanation': email_data.get('explanation', ''),
            'feedback': explanation_feedback,
            'simulation_id': simulation.id,
            'phase': simulation.phase,
            'completion_count': simulation.completion_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting simulation: {str(e)}")
        return jsonify({'error': f'Failed to submit simulation: {str(e)}'}), 500

@bp.route('/results/<int:simulation_id>', methods=['GET'])
@token_required
def get_simulation_results(simulation_id):
    """
    Get results for a completed simulation.
    """
    try:
        # Get user from environment
        user_id = request.environ.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        user = User.query.get(user_id)
        simulation = Simulation.query.filter_by(id=simulation_id, user_id=user.id).first()
        
        if not simulation:
            return jsonify({'error': 'Simulation not found'}), 404
            
        results = SimulationResult.query.filter_by(simulation_id=simulation.id).all()
        
        # Calculate statistics
        total_questions = len(results)
        correct_answers = sum(1 for r in results if r.is_correct)
        score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Format results
        formatted_results = []
        for result in results:
            email_data = json.loads(result.email_data)
            formatted_results.append({
                'id': result.id,
                'email': {
                    'subject': email_data.get('subject'),
                    'sender': email_data.get('sender'),
                    'is_phishing': email_data.get('is_phishing')
                },
                'user_assessment': result.user_assessment,
                'is_correct': result.is_correct,
                'feedback': result.feedback,
                'timestamp': result.timestamp.isoformat()
            })
            
        return jsonify({
            'simulation_id': simulation.id,
            'score': score,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'start_time': simulation.start_time.isoformat() if simulation.start_time else None,
            'end_time': simulation.end_time.isoformat() if simulation.end_time else None,
            'status': simulation.status,
            'results': formatted_results
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving simulation results: {str(e)}")
        return jsonify({'error': 'Failed to retrieve simulation results'}), 500

@bp.route('/skip', methods=['POST'])
@token_required
def skip_email():
    """
    Skip the current email in the simulation.
    """
    try:
        # Get user from environment
        user_id = request.environ.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        user = User.query.get(user_id)
        simulation = Simulation.query.filter_by(user_id=user.id, status="active").first()
        
        if not simulation:
            return jsonify({'error': 'No active simulation found'}), 404
            
        # Skip the current email
        simulation.completion_count += 1
        simulation.active_email = None
        
        # Check if we need to advance to the next phase
        if simulation.phase == 1 and simulation.completion_count >= len(PHASE1_EMAILS):
            simulation.phase = 2
            simulation.completion_count = 0
            
        # Check if simulation is complete
        if simulation.phase == 2 and simulation.completion_count >= 5:
            simulation.status = "completed"
            simulation.end_time = datetime.datetime.now()
            
        db.session.commit()
        
        return jsonify({
            'simulation_id': simulation.id,
            'phase': simulation.phase,
            'completion_count': simulation.completion_count,
            'status': simulation.status,
            'message': 'Email skipped successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error skipping email: {str(e)}")
        return jsonify({'error': 'Failed to skip email'}), 500