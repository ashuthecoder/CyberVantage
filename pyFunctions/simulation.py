import datetime
import random
import traceback

def generate_unique_simulation_email(db, current_user, current_email_id, simulation_id, 
                                    generate_ai_email, template_emails, set_simulation_id_for_email, 
                                    SimulationEmail, SimulationResponse):
    """
    Generate a unique email for the current simulation
    This function ensures we never reuse emails across simulation sessions
    """
    # Get performance from phase 1
    previous_responses = SimulationResponse.query.filter_by(
        user_id=current_user.id
    ).filter(SimulationResponse.email_id < 6).all()
    
    correct_count = sum(1 for r in previous_responses if r.user_response == r.is_spam_actual)
    performance_summary = f"The user correctly identified {correct_count} out of 5 emails in phase 1."
    print(f"[SIMULATE] Performance summary: {performance_summary}")
    
    try:
        # Generate AI email
        email_data = generate_ai_email(current_user.name, performance_summary)
        
        # Create a unique ID based on simulation ID and position
        # This ensures each simulation gets unique emails
        unique_id = f"{current_email_id}_{simulation_id[-8:]}"
        # Use hash function to convert the unique_id string to a number
        # Note: We use abs() to ensure positive number and modulo to keep it in range
        unique_id_num = abs(hash(unique_id)) % 1000000 + current_email_id
        
        # Find a free ID in the database
        while SimulationEmail.query.filter_by(id=unique_id_num).first():
            unique_id_num = (unique_id_num + 1) % 1000000 + current_email_id
        
        # Create a database entry for this AI email with the unique ID
        email = SimulationEmail(
            id=unique_id_num,
            sender=email_data['sender'],
            subject=email_data['subject'],
            date=email_data['date'],
            content=email_data['content'],
            is_spam=email_data['is_spam'],
            is_predefined=False
        )
        db.session.add(email)
        db.session.commit()
        
        # Now set the simulation ID for this email
        set_simulation_id_for_email(email.id, simulation_id)
        print(f"[SIMULATE] Created new email with ID {email.id} for simulation {simulation_id}")
        
        return email
        
    except Exception as e:
        print(f"[SIMULATE] Error generating email: {str(e)}")
        traceback.print_exc()
        
        # Use a fallback email with additional randomization
        template = random.choice(template_emails)
        
        # Add significant randomization
        random_phrases = [
            "Important update", "Please review", "Action required",
            "Notification", "Alert", "Update", "Information",
            "Confirmation", "Reminder", "News", "Your account",
            "Security notice", "Customer service"
        ]
        
        random_phrase = random.choice(random_phrases)
        random_id = random.randint(10000, 99999)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Create unique content by adding timestamp and reference
        content_with_uniqueness = template["content"].replace(
            "</p>", f" (Ref: {random_id}-{timestamp})</p>", 1
        )
        
        # Create a unique ID as above
        unique_id = f"{current_email_id}_{simulation_id[-8:]}"
        unique_id_num = abs(hash(unique_id)) % 1000000 + current_email_id
        
        while SimulationEmail.query.filter_by(id=unique_id_num).first():
            unique_id_num = (unique_id_num + 1) % 1000000 + current_email_id
        
        email = SimulationEmail(
            id=unique_id_num,
            sender=template["sender"],
            subject=f"{random_phrase}: {template['subject']} #{random_id}",
            date=datetime.datetime.now().strftime("%B %d, %Y"),
            content=content_with_uniqueness,
            is_spam=template["is_spam"],
            is_predefined=False
        )
        
        db.session.add(email)
        db.session.commit()
        
        # Set the simulation ID
        set_simulation_id_for_email(email.id, simulation_id)
        
        return email