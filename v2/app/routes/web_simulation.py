"""
Web routes for phishing simulation functionality.
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required, current_user
import json
from app.models.simulation import Simulation, SimulationResult
from app.models.user import db
from app.services.ai_service import generate_simulation_email, evaluate_user_action
import random
import datetime

# Create blueprint
web_simulation_bp = Blueprint('web_simulation', __name__, url_prefix='/simulation')

@web_simulation_bp.route('/', methods=['GET'])
@login_required
def simulate():
    """
    Display the simulation setup page.
    """
    return render_template('simulation.html')

@web_simulation_bp.route('/start', methods=['POST'])
@login_required
def start_simulation():
    """
    Start a new simulation with the selected difficulty.
    """
    difficulty = request.form.get('difficulty', 'medium')
    
    # Randomly decide if this will be a phishing or legitimate email
    is_phishing = random.choice([True, False])
    
    # Generate email content using AI
    email_data = generate_simulation_email(difficulty, is_phishing)
    
    if not email_data:
        flash('Error generating simulation. Please try again.', 'danger')
        return redirect(url_for('web_simulation.simulate'))
    
    # Create simulation record
    try:
        # Store the email data
        simulation = Simulation(
            user_id=current_user.id,
            start_time=datetime.datetime.now(),
            phase=2,  # Use phase 2 for AI-generated emails
            completion_count=0,
            active_email=json.dumps(email_data),
            emails_generated=1,
            status="active"
        )
        
        db.session.add(simulation)
        db.session.commit()
        
        return redirect(url_for('web_simulation.view_simulation', simulation_id=simulation.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating simulation: {str(e)}', 'danger')
        return redirect(url_for('web_simulation.simulate'))

@web_simulation_bp.route('/<int:simulation_id>', methods=['GET'])
@login_required
def view_simulation(simulation_id):
    """
    View a simulation email.
    """
    simulation = Simulation.query.get_or_404(simulation_id)
    
    # Check if this simulation belongs to the current user
    if simulation.user_id != current_user.id:
        flash('You do not have permission to view this simulation.', 'danger')
        return redirect(url_for('web_simulation.simulate'))
    
    # Check if already completed
    if simulation.status == 'completed':
        flash('This simulation has already been completed.', 'warning')
        return redirect(url_for('web_simulation.simulate'))
    
    # Get email data from the active_email field
    if not simulation.active_email:
        flash('No active email found for this simulation.', 'warning')
        return redirect(url_for('web_simulation.simulate'))
        
    email_data = json.loads(simulation.active_email)
    
    return render_template('simulation_email.html', simulation=simulation, email=email_data)

@web_simulation_bp.route('/<int:simulation_id>/submit', methods=['POST'])
@login_required
def submit_assessment(simulation_id):
    """
    Submit an assessment for a simulation.
    """
    simulation = Simulation.query.get_or_404(simulation_id)
    
    # Check if this simulation belongs to the current user
    if simulation.user_id != current_user.id:
        flash('You do not have permission to submit this assessment.', 'danger')
        return redirect(url_for('web_simulation.simulate'))
    
    # Check if already completed
    if simulation.status == 'completed':
        flash('This simulation has already been completed.', 'warning')
        return redirect(url_for('web_simulation.simulate'))
    
    # Get form data
    user_assessment = request.form.get('is_phishing') == 'true'
    user_explanation = request.form.get('explanation', '')
    
    if not user_explanation:
        flash('Please provide an explanation for your assessment.', 'warning')
        return redirect(url_for('web_simulation.view_simulation', simulation_id=simulation_id))
    
    # Get email data
    if not simulation.active_email:
        flash('No active email found for this simulation.', 'warning')
        return redirect(url_for('web_simulation.simulate'))
        
    email_data = json.loads(simulation.active_email)
    
    # Check if assessment is correct
    actual_assessment = email_data.get('is_phishing')
    is_correct = user_assessment == actual_assessment
    
    # Get AI feedback on user's explanation
    feedback = evaluate_user_action(email_data, user_assessment, user_explanation)
    
    # Create result record
    try:
        result = SimulationResult(
            simulation_id=simulation.id,
            email_data=simulation.active_email,
            user_assessment=user_assessment,
            actual_assessment=actual_assessment,
            is_correct=is_correct,
            user_explanation=user_explanation,
            feedback=feedback
        )
        
        db.session.add(result)
        
        # Update simulation status
        simulation.status = 'completed'
        simulation.end_time = datetime.datetime.now()
        simulation.completion_count += 1
        
        db.session.commit()
        
        return redirect(url_for('web_simulation.view_results', simulation_id=simulation.id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting assessment: {str(e)}', 'danger')
        return redirect(url_for('web_simulation.view_simulation', simulation_id=simulation_id))

@web_simulation_bp.route('/<int:simulation_id>/results', methods=['GET'])
@login_required
def view_results(simulation_id):
    """
    View results of a completed simulation.
    """
    simulation = Simulation.query.get_or_404(simulation_id)
    
    # Check if this simulation belongs to the current user
    if simulation.user_id != current_user.id:
        flash('You do not have permission to view these results.', 'danger')
        return redirect(url_for('web_simulation.simulate'))
    
    # Check if completed
    if simulation.status != 'completed':
        flash('This simulation has not been completed yet.', 'warning')
        return redirect(url_for('web_simulation.view_simulation', simulation_id=simulation_id))
    
    # Get results
    result = SimulationResult.query.filter_by(simulation_id=simulation.id).first()
    
    if not result:
        flash('No results found for this simulation.', 'warning')
        return redirect(url_for('web_simulation.simulate'))
    
    # Get email data
    email_data = json.loads(result.email_data)
    
    return render_template('simulation_results.html', 
                          simulation=simulation, 
                          email=email_data, 
                          result=result,
                          assessment_was_phishing=result.user_assessment)