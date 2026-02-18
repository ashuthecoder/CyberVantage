"""
Simulation routes - phishing simulation functionality
"""
import datetime
import traceback
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session
from routes.auth_routes import token_required
from models.database import (
    SimulationEmail, SimulationResponse, predefined_emails, db,
    update_database_schema, reset_sequence_for_table, get_simulation_id_for_email, 
    set_simulation_id_for_email, get_emails_for_simulation
)
from pyFunctions.email_generation import generate_ai_email, evaluate_explanation
from pyFunctions.template_emails import get_template_email

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/simulate', methods=['GET'])
@token_required
def simulate(current_user):
    # Ensure tables exist and update schema safely
    from flask import current_app
    with current_app.app_context():
        db.create_all()
    update_database_schema(current_app)

    try:
        print(f"[SIMULATE] Starting with session: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        # Initialize simulation if first time
        if 'simulation_phase' not in session:
            session['simulation_phase'] = 1
            session['current_email_id'] = 1
            session['simulation_id'] = str(uuid.uuid4())
            session['phase2_emails_completed'] = 0  # Initialize counter
            session.pop('active_phase2_email_id', None)
            session.modified = True
            print(f"[SIMULATE] Initialized new simulation with ID: {session.get('simulation_id')}")
            
            # Log simulation start
            from models.database import log_simulation_event
            log_simulation_event(
                current_user.id, 
                current_user.name, 
                'started', 
                session.get('simulation_id'),
                f"New simulation started - Phase 1"
            )

        # Load predefined emails once (Phase 1)
        if session.get('simulation_phase') == 1:
            for predefined_email in predefined_emails:
                existing = SimulationEmail.query.filter_by(id=predefined_email['id']).first()
                if not existing:
                    new_email = SimulationEmail(
                        id=predefined_email['id'],
                        sender=predefined_email['sender'],
                        subject=predefined_email['subject'],
                        date=predefined_email['date'],
                        content=predefined_email['content'],
                        is_spam=predefined_email['is_spam'],
                        is_predefined=True
                    )
                    db.session.add(new_email)
            db.session.commit()
            
            # Reset sequence after inserting predefined emails with explicit IDs
            # This prevents duplicate key errors in PostgreSQL
            reset_sequence_for_table('simulation_email', current_app)

        # Read state
        phase = session.get('simulation_phase', 1)
        current_email_id = session.get('current_email_id', 1)
        simulation_id = session.get('simulation_id')
        phase2_completed = session.get('phase2_emails_completed', 0)
        active_phase2_email_id = session.get('active_phase2_email_id')

        print(f"[SIMULATE] Current phase: {phase}, Current email ID: {current_email_id}, "
              f"Simulation ID: {simulation_id}, Phase 2 completed: {phase2_completed}, "
              f"Active Phase2 Email ID: {active_phase2_email_id}")

        # Phase 1 -> Phase 2 transition
        if phase == 1 and current_email_id > 5:
            print("[SIMULATE] Phase 1 complete, moving to phase 2")
            session['simulation_phase'] = 2
            session['phase2_emails_completed'] = 0
            session.pop('active_phase2_email_id', None)
            session.modified = True
            phase = 2  # continue into Phase 2 logic
            
            # Log phase 1 completion
            from models.database import log_simulation_event
            log_simulation_event(
                current_user.id,
                current_user.name,
                'phase1_completed',
                session.get('simulation_id'),
                "Phase 1 completed, moving to Phase 2"
            )

        # Completion logic (Phase 2 by counter only)
        if phase == 2 and phase2_completed >= 5:
            print("[SIMULATE] Simulation complete")
            
            # Log simulation completion
            from models.database import log_simulation_event
            log_simulation_event(
                current_user.id,
                current_user.name,
                'completed',
                session.get('simulation_id'),
                "Full simulation completed - Phase 1 & 2"
            )
            
            return render_template('simulate.html', phase='complete', username=current_user.name)

        # Fetch email for current step
        email = None

        if phase == 1:
            # Phase 1: Get predefined email
            email = SimulationEmail.query.filter_by(id=current_email_id).first()
            if not email:
                if 0 < current_email_id <= len(predefined_emails):
                    email_data = predefined_emails[current_email_id - 1]
                    email = SimulationEmail(
                        id=current_email_id,
                        sender=email_data['sender'],
                        subject=email_data['subject'],
                        date=email_data['date'],
                        content=email_data['content'],
                        is_spam=email_data['is_spam'],
                        is_predefined=True
                    )
                    db.session.add(email)
                    db.session.commit()
                else:
                    # Reset to a valid state
                    session['simulation_phase'] = 1
                    session['current_email_id'] = 1
                    session['simulation_id'] = str(uuid.uuid4())
                    session['phase2_emails_completed'] = 0
                    session.pop('active_phase2_email_id', None)
                    session.modified = True
                    return redirect(url_for('simulation.simulate'))
        else:
            # Phase 2: Use active email if exists, otherwise generate a new one
            if active_phase2_email_id:
                email = SimulationEmail.query.get(active_phase2_email_id)

            if not email:
                # Build performance summary from Phase 1
                previous_responses = SimulationResponse.query.filter_by(
                    user_id=current_user.id
                ).filter(SimulationResponse.email_id < 6).all()
                correct_count = sum(1 for r in previous_responses if r.user_response == r.is_spam_actual)
                performance_summary = f"The user correctly identified {correct_count} out of 5 emails in phase 1."
                print(f"[SIMULATE] Performance summary: {performance_summary}")

                # Attempt AI generation; fallback to templates on error
                try:
                    email_data = generate_ai_email(current_user.name, performance_summary, None, None, current_app)
                except Exception as e:
                    print(f"[SIMULATE] Error generating AI email (will fallback to template): {e}")
                    email_data = get_template_email()

                # Create and persist the email
                try:
                    email = SimulationEmail(
                        sender=email_data['sender'],
                        subject=email_data['subject'],
                        date=email_data.get('date', datetime.datetime.utcnow().strftime("%B %d, %Y")),
                        content=email_data['content'],
                        is_spam=email_data['is_spam'],
                        is_predefined=False
                    )
                    db.session.add(email)
                    db.session.commit()

                    # Tag email with this simulation_id if the column exists
                    set_simulation_id_for_email(email.id, simulation_id, current_app)

                    # Track active Phase 2 email ID
                    session['active_phase2_email_id'] = email.id
                    session.modified = True
                    print(f"[SIMULATE] Created new Phase 2 email with ID {email.id} for simulation {simulation_id}")
                except Exception as db_error:
                    # Rollback on database error to prevent pending transaction issues
                    db.session.rollback()
                    print(f"[SIMULATE] Database error creating Phase 2 email: {str(db_error)}")
                    traceback.print_exc()
                    # Return error message to user
                    return render_template(
                        'system_message.html',
                        title="Error",
                        message="Unable to generate a new email. Please try again.",
                        action_text="Try Again",
                        action_url=url_for('simulation.simulate'),
                        username=current_user.name
                    )

        if not email:
            return render_template(
                'system_message.html',
                title="Error",
                message="Failed to load email. Please try restarting the simulation.",
                action_text="Restart Simulation",
                action_url=url_for('simulation.restart_simulation'),
                username=current_user.name
            )

        # Render appropriate view - Note: api_key_available set to False since we removed Gemini
        return render_template(
            'simulate.html',
            phase=phase,
            current_email=current_email_id if phase == 1 else session.get('active_phase2_email_id'),
            email=email,
            username=current_user.name,
            api_key_available=False  # Removed Gemini logic as requested
        )

    except Exception as e:
        print(f"[SIMULATE] Exception in simulate route: {str(e)}")
        traceback.print_exc()
        # Rollback any pending database transaction
        try:
            db.session.rollback()
        except Exception:
            pass
        # Emergency reset
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = str(uuid.uuid4())
        session['phase2_emails_completed'] = 0
        session.pop('active_phase2_email_id', None)
        session.modified = True
        return render_template(
            'system_message.html',
            title="Error",
            message=f"An error occurred: {str(e)}. The simulation has been reset.",
            action_text="Continue",
            action_url=url_for('simulation.simulate'),
            username=current_user.name
        )

@simulation_bp.route('/submit_simulation', methods=['POST'])
@token_required
def submit_simulation(current_user):
    try:
        email_id = int(request.form.get('email_id'))
        phase = int(request.form.get('phase'))
        is_spam_response = request.form.get('is_spam') == 'true'
        explanation = request.form.get('explanation', '')

        print(f"[SUBMIT] Processing submission: phase={phase}, email_id={email_id}")
        print(f"[SUBMIT] Current session before: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        # Get the email
        email = SimulationEmail.query.get(email_id)
        if not email:
            print(f"[SUBMIT] Error: Email ID {email_id} not found in database")
            return redirect(url_for('simulation.reset_stuck_simulation'))

        # Process AI feedback for phase 2
        ai_feedback = None
        score = None
        if phase == 2:
            from flask import current_app
            eval_result = evaluate_explanation(
                email.content,
                email.is_spam,
                is_spam_response,
                explanation,
                None,  # No Gemini key - removed as requested
                None,  # No genai module - removed as requested
                current_app
            )
            ai_feedback = eval_result["feedback"]
            score = eval_result["score"]

        # Save the response to database
        response = SimulationResponse(
            user_id=current_user.id,
            email_id=email_id,
            is_spam_actual=email.is_spam,
            user_response=is_spam_response,
            user_explanation=explanation,
            ai_feedback=ai_feedback,
            score=score
        )
        db.session.add(response)
        db.session.commit()

        # Phase 2: show feedback page (continuation handled in continue_after_feedback)
        if phase == 2:
            return redirect(url_for('simulation.simulation_feedback', email_id=email_id))

        # Phase 1: advance to next predefined email
        next_email_id = email_id + 1
        if phase == 1 and next_email_id > 5:
            session['simulation_phase'] = 2
            # Keep current_email_id untouched in Phase 2; Phase 2 flow uses active_phase2_email_id
            print(f"[SUBMIT] Advancing to phase 2")
        else:
            session['current_email_id'] = next_email_id
            print(f"[SUBMIT] Advancing to email {next_email_id} in phase {phase}")

        # Force session to save
        session.modified = True

        print(f"[SUBMIT] Session after update: phase={session.get('simulation_phase')}, email_id={session.get('current_email_id')}")

        return redirect(url_for('simulation.simulate'))

    except Exception as e:
        print(f"[SUBMIT] Exception in submit_simulation: {str(e)}")
        traceback.print_exc()
        # Emergency recovery
        return redirect(url_for('simulation.reset_stuck_simulation'))

@simulation_bp.route('/simulation_feedback/<int:email_id>')
@token_required
def simulation_feedback(current_user, email_id):
    try:
        # Get the user's most recent response for this email
        response = SimulationResponse.query.filter_by(
            user_id=current_user.id,
            email_id=email_id
        ).order_by(SimulationResponse.created_at.desc()).first()

        if not response:
            print(f"[FEEDBACK] No response found for email {email_id}")
            return redirect(url_for('simulation.simulate'))

        # Ensure the feedback is treated as HTML
        if response.ai_feedback:
            if not response.ai_feedback.strip().startswith('<'):
                print(f"[FEEDBACK] Warning: Feedback doesn't appear to be HTML: {response.ai_feedback[:50]}...")
                response.ai_feedback = f"<p>{response.ai_feedback}</p>"

        return render_template(
            'simulation_feedback.html',
            response=response,
            username=current_user.name
        )
    except Exception as e:
        print(f"[FEEDBACK] Error in simulation_feedback: {e}")
        traceback.print_exc()
        return redirect(url_for('dashboard'))

@simulation_bp.route('/continue_after_feedback/<int:email_id>')
@token_required
def continue_after_feedback(current_user, email_id):
    """Advance to the next email after viewing feedback (Phase 2)."""
    try:
        print(f"[CONTINUE] Processing continuation from email {email_id}")

        # Only Phase 2 uses this route; increment the counter and clear active email
        if session.get('simulation_phase') == 2:
            session['phase2_emails_completed'] = session.get('phase2_emails_completed', 0) + 1
            # Clear the active email so simulate() generates the next one
            session.pop('active_phase2_email_id', None)
            session.modified = True

        print(f"[CONTINUE] Updated session: phase={session.get('simulation_phase')}, "
              f"phase2_completed={session.get('phase2_emails_completed')}, "
              f"active_phase2_email_id={session.get('active_phase2_email_id')}, "
              f"simulation_id={session.get('simulation_id')}")

        # If 5 done, go to results
        if session.get('simulation_phase') == 2 and session.get('phase2_emails_completed', 0) >= 5:
            print(f"[CONTINUE] Phase 2 complete: {session.get('phase2_emails_completed')} emails completed")
            
            # Log phase 2 completion
            from models.database import log_simulation_event
            log_simulation_event(
                current_user.id,
                current_user.name,
                'phase2_completed',
                session.get('simulation_id'),
                f"Phase 2 completed with {session.get('phase2_emails_completed')} emails"
            )
            
            return redirect(url_for('simulation.simulation_results'))

        return redirect(url_for('simulation.simulate'))
    except Exception as e:
        print(f"[CONTINUE] Error in continue_after_feedback: {e}")
        traceback.print_exc()
        return redirect(url_for('simulation.reset_stuck_simulation'))

@simulation_bp.route('/skip_email')
@token_required
def skip_email(current_user):
    """Skip the current email during testing"""
    try:
        phase = session.get('simulation_phase', 1)
        
        if phase == 1:
            # For Phase 1, just advance to the next email
            current_email_id = session.get('current_email_id', 1)
            next_email_id = current_email_id + 1
            
            # If we're at the end of Phase 1, move to Phase 2
            if next_email_id > 5:
                session['simulation_phase'] = 2
                print(f"[SKIP] Advancing from Phase 1 to Phase 2")
            else:
                session['current_email_id'] = next_email_id
                print(f"[SKIP] Advancing to email {next_email_id} in Phase 1")
                
            session.modified = True
            
        elif phase == 2:
            # For Phase 2, increment the completion counter and clear active email
            session['phase2_emails_completed'] = session.get('phase2_emails_completed', 0) + 1
            session.pop('active_phase2_email_id', None)
            session.modified = True
            
            print(f"[SKIP] Phase 2 email skipped. Completed: {session.get('phase2_emails_completed')}")
            
            # If 5 done, go to results
            if session.get('phase2_emails_completed', 0) >= 5:
                print(f"[SKIP] Phase 2 complete after skip: {session.get('phase2_emails_completed')} emails completed")
                return redirect(url_for('simulation.simulation_results'))
        
        return redirect(url_for('simulation.simulate'))
    except Exception as e:
        print(f"[SKIP] Error in skip_email: {e}")
        traceback.print_exc()
        return redirect(url_for('simulation.reset_stuck_simulation'))

@simulation_bp.route('/simulation_results')
@token_required
def simulation_results(current_user):
    try:
        from flask import current_app
        simulation_id = session.get('simulation_id')
        print(f"[RESULTS] Getting results for simulation ID: {simulation_id}")

        # Phase 1 (predefined IDs are always 1..5)
        phase1_email_ids = list(range(1, 6))

        def most_recent_per_email(responses):
            seen = set()
            ordered = []
            for r in responses:
                if r.email_id not in seen:
                    seen.add(r.email_id)
                    ordered.append(r)
            return ordered

        # 1) Collect Phase 1 responses (newest first), then keep only most recent per email_id
        phase1_all = (SimulationResponse.query
                      .filter_by(user_id=current_user.id)
                      .filter(SimulationResponse.email_id.in_(phase1_email_ids))
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
        phase1_responses = most_recent_per_email(phase1_all)[:5]

        # 2) Try Phase 2 by simulation_id linkage (if column/value available)
        phase2_email_ids = []
        try:
            phase2_email_ids = get_emails_for_simulation(simulation_id, current_app) if simulation_id else []
        except Exception as e:
            print(f"[RESULTS] Error fetching emails for simulation via simulation_id: {e}")
            phase2_email_ids = []

        if phase2_email_ids:
            p2_all = (SimulationResponse.query
                      .filter_by(user_id=current_user.id)
                      .filter(SimulationResponse.email_id.in_(phase2_email_ids))
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
            phase2_responses = most_recent_per_email(p2_all)
        else:
            # 3) Fallback: last AI responses for this user by joining SimulationEmail (is_predefined == False)
            p2_all = (db.session.query(SimulationResponse)
                      .join(SimulationEmail, SimulationEmail.id == SimulationResponse.email_id)
                      .filter(SimulationResponse.user_id == current_user.id,
                              SimulationEmail.is_predefined == False)
                      .order_by(SimulationResponse.created_at.desc())
                      .all())
            phase2_responses = most_recent_per_email(p2_all)

        phase2_responses = phase2_responses[:5]

        # 4) Stats
        phase1_correct = sum(1 for r in phase1_responses if r.user_response == r.is_spam_actual)
        phase2_correct = sum(1 for r in phase2_responses if r.user_response == r.is_spam_actual)
        phase2_scores = [r.score for r in phase2_responses if getattr(r, 'score', None) is not None]
        avg_score = (sum(phase2_scores) / len(phase2_scores)) if phase2_scores else 0

        print(f"[RESULTS] Phase 1: {phase1_correct}/{len(phase1_responses)}, Phase 2: {phase2_correct}/{len(phase2_responses)}")
        print(f"[RESULTS] Phase 2 scores: {phase2_scores}")

        # 5) Clear simulation state after calculating results
        session.pop('simulation_phase', None)
        session.pop('current_email_id', None)
        session.pop('simulation_id', None)
        session.pop('phase2_emails_completed', None)
        session.pop('active_phase2_email_id', None)
        session.modified = True

        # 6) Render
        all_responses = sorted(phase1_responses + phase2_responses, key=lambda x: x.email_id)

        return render_template(
            'simulation_results.html',
            phase1_correct=phase1_correct,
            phase1_total=len(phase1_responses),
            phase2_correct=phase2_correct,
            phase2_total=len(phase2_responses),
            avg_score=avg_score,
            responses=all_responses,
            phase1_responses=phase1_responses,
            phase2_responses=phase2_responses,
            username=current_user.name
        )
    except Exception as e:
        print(f"[RESULTS] Error in simulation_results: {e}")
        traceback.print_exc()
        # Show a friendly message instead of bouncing to dashboard silently
        return render_template(
            'system_message.html',
            title="Results Unavailable",
            message=f"Couldn't render your results due to an error: {e}",
            action_text="Return to Dashboard",
            action_url=url_for('dashboard'),
            username=current_user.name
        )

@simulation_bp.route('/restart_simulation')
@token_required
def restart_simulation(current_user):
    try:
        print("[RESTART] Restarting simulation")

        # Generate a new simulation ID
        new_simulation_id = str(uuid.uuid4())

        # Clear only simulation-related session data, preserve authentication
        simulation_keys = ['simulation_phase', 'current_email_id', 'simulation_id', 
                         'phase2_emails_completed', 'active_phase2_email_id']
        for key in simulation_keys:
            session.pop(key, None)
        
        # Set new simulation values
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session['phase2_emails_completed'] = 0
        session.modified = True

        print(f"[RESTART] Created new simulation ID: {new_simulation_id}")

        # Reset rate limit tracking
        from flask import current_app
        for k in ['RATE_LIMITED', 'RATE_LIMIT_TIME']:
            if k in current_app.config:
                current_app.config.pop(k, None)

        # Delete existing responses for this user
        SimulationResponse.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        print("[RESTART] Simulation reset complete")

        return redirect(url_for('simulation.simulate'))
    except Exception as e:
        print(f"[RESTART] Error in restart_simulation: {e}")
        db.session.rollback()
        # Instead of going to dashboard, try to recover and go to simulation
        try:
            # Reset session to safe state (preserve authentication)
            simulation_keys = ['simulation_phase', 'current_email_id', 'simulation_id', 
                             'phase2_emails_completed', 'active_phase2_email_id']
            for key in simulation_keys:
                session.pop(key, None)
            session['simulation_phase'] = 1
            session['current_email_id'] = 1
            session['simulation_id'] = str(uuid.uuid4())
            session['phase2_emails_completed'] = 0
            session.modified = True
            return redirect(url_for('simulation.simulate'))
        except:
            # If all else fails, then go to dashboard
            return redirect(url_for('dashboard'))

@simulation_bp.route('/reset_stuck_simulation')
@token_required
def reset_stuck_simulation(current_user):
    """Emergency route to fix stuck simulations"""
    try:
        # Generate a new simulation ID
        new_simulation_id = str(uuid.uuid4())

        # Clear only simulation-related session data, preserve authentication
        simulation_keys = ['simulation_phase', 'current_email_id', 'simulation_id', 
                         'phase2_emails_completed', 'active_phase2_email_id']
        for key in simulation_keys:
            session.pop(key, None)
        
        # Set new simulation values
        session['simulation_phase'] = 1
        session['current_email_id'] = 1
        session['simulation_id'] = new_simulation_id
        session['phase2_emails_completed'] = 0
        session.modified = True

        print(f"[RESET] Created new simulation ID: {new_simulation_id}")

        # Reset rate limit tracking
        from flask import current_app
        for k in ['RATE_LIMITED', 'RATE_LIMIT_TIME']:
            if k in current_app.config:
                current_app.config.pop(k, None)

        # Delete previous responses
        SimulationResponse.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        return render_template(
            'system_message.html',
            title="Simulation Reset",
            message="Your simulation has been reset due to a technical issue.",
            action_text="Continue to Simulation",
            action_url=url_for('simulation.simulate'),
            username=current_user.name
        )
    except Exception as e:
        print(f"[RESET] Exception in reset_stuck_simulation: {e}")
        return redirect(url_for('dashboard'))