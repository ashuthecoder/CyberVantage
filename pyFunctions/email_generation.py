import random
import traceback
import datetime
import re
import markdown

def generate_ai_email(user_name, previous_responses, GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an AI email with robust error handling"""
    print(f"[GENERATE] Starting email generation for user: {user_name}")
    
    # Get template_email function from the template_emails module
    from .template_emails import get_template_email
    
    if not GOOGLE_API_KEY or not genai:
        print("[GENERATE] No API key or genai module - using template email")
        return get_template_email()
    
    # Create prompt
    prompt = f"""
    Generate a completely new and unique phishing or legitimate email for a cybersecurity training simulation.
    
    User's name: {user_name}
    Previous performance: {previous_responses}
    
    IMPORTANT: Make this email COMPLETELY DIFFERENT from any previous emails. Use new themes, new senders, and unique content.
    
    The email should have the following format:
    - Sender: [email address]
    - Subject: [subject line]
    - Date: [current date]
    - Content: [HTML content of the email body]
    - Is_spam: [true/false] - whether this is a phishing email or legitimate
    
    If creating a phishing email, include subtle red flags that a cautious user might notice.
    If creating a legitimate email, make it realistic but free of phishing indicators.
    
    Make each email unique and different from the predefined examples.
    
    Current time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    try:
        # Generate the email with simpler configuration
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("[GENERATE] Sending request to Gemini API")
        response = model.generate_content(prompt)
        
        # Extract content from response
        content = None
        
        # Try multiple approaches to extract text
        if hasattr(response, 'text'):
            content = response.text
            print("[GENERATE] Successfully extracted text via .text property")
        elif hasattr(response, 'parts') and response.parts:
            content = response.parts[0].text
            print("[GENERATE] Successfully extracted text via .parts[0].text")
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                content = candidate.content.parts[0].text
                print("[GENERATE] Successfully extracted text via candidates structure")
        
        # If we still don't have content, try string representation
        if not content:
            content = str(response)
            print("[GENERATE] Using string representation as fallback")
            
        if not content:
            print("[GENERATE] Failed to extract content from response")
            return get_template_email()
            
        print(f"[GENERATE] Response content length: {len(content)}")
        print(f"[GENERATE] First 100 chars: {content[:100]}")
        
        # Parse the email components with better error handling
        try:
            if "Sender:" not in content or "Subject:" not in content:
                print("[GENERATE] Missing expected fields in response")
                return get_template_email()
                
            sender = content.split("Sender:")[1].split("\n")[0].strip()
            subject = content.split("Subject:")[1].split("\n")[0].strip()
            
            # Get date with fallback
            try:
                date = content.split("Date:")[1].split("\n")[0].strip()
            except:
                date = datetime.datetime.now().strftime("%B %d, %Y")
                
            # Extract email content between Content: and Is_spam:
            if "Content:" in content and "Is_spam:" in content:
                email_content = content.split("Content:")[1].split("Is_spam:")[0].strip()
            else:
                print("[GENERATE] Could not extract email content properly")
                email_content = f"<p>Training email content.</p><p>{content}</p>"
            
            # Determine if spam
            try:
                is_spam_section = content.split("Is_spam:")[1].lower().strip()
                is_spam = "true" in is_spam_section or "yes" in is_spam_section
            except:
                is_spam = random.choice([True, False])
            
            # Ensure email_content is proper HTML
            if not email_content.strip().startswith("<"):
                email_content = f"<p>{email_content.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
            
            # Add a unique timestamp signature to the content to ensure uniqueness
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            email_content = email_content.replace('</body>', f'<!-- gen_id: {timestamp} --></body>')
            if '</body>' not in email_content:
                email_content += f'<!-- gen_id: {timestamp} -->'
                
            # Add subtle randomization to sender domain to ensure uniqueness if needed
            if random.random() < 0.3:
                sender_parts = sender.split('@')
                if len(sender_parts) == 2:
                    domain_parts = sender_parts[1].split('.')
                    if len(domain_parts) >= 2:
                        domain_parts[0] += str(random.randint(1, 999))
                        sender = f"{sender_parts[0]}@{'.'.join(domain_parts)}"
            
            return {
                "sender": sender,
                "subject": subject,
                "date": date,
                "content": email_content,
                "is_spam": is_spam
            }
        except Exception as parse_error:
            print(f"[GENERATE] Error parsing response: {parse_error}")
            traceback.print_exc()
            return get_template_email()
    except Exception as e:
        print(f"[GENERATE] Error in AI email generation: {e}")
        traceback.print_exc()
        
        # Check for rate limits
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            if app:
                app.config['RATE_LIMITED'] = True
                app.config['RATE_LIMIT_TIME'] = datetime.datetime.now().timestamp()
            print(f"[GENERATE] API rate limit detected: {error_str}")
        
        return get_template_email()

def evaluate_explanation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY=None, genai=None, app=None):
    """Evaluate the user's explanation of why an email is phishing/legitimate"""
    print(f"[EVALUATE] Starting evaluation. Is spam: {is_spam}, User said: {user_response}")
    
    # Check for recent rate limit errors
    rate_limited = app.config.get('RATE_LIMITED', False) if app else False
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0) if app else 0
    current_time = datetime.datetime.now().timestamp()
    
    # Use fallbacks if needed
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"[EVALUATE] Using fallback due to rate limit ({int(current_time - rate_limit_time)} seconds ago)")
        return get_fallback_evaluation(is_spam, user_response)
    
    if not GOOGLE_API_KEY or not genai:
        print("[EVALUATE] No API key - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
    
    # Create prompt for evaluation
    prompt = f"""
    Evaluate this user's analysis of a potential phishing email.
    
    THE EMAIL:
    {email_content}
    
    CORRECT ANSWER:
    This {'IS' if is_spam else 'IS NOT'} a phishing/spam email.
    
    USER'S RESPONSE:
    The user said this {'IS' if user_response else 'IS NOT'} a phishing/spam email.
    
    USER'S EXPLANATION:
    {user_explanation}
    
    Please evaluate:
    1. Is the user's conclusion correct? (Yes/No)
    2. What did the user get right in their analysis?
    3. What did the user miss or get wrong?
    4. On a scale of 1-10, rate the user's analysis quality.
    5. Provide constructive feedback to improve their phishing detection skills.
    
    Format your response with Markdown formatting. Use headers (##) for each numbered section, bold for emphasis, and paragraphs for readability.
    """
    
    try:
        # Generate evaluation
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("[EVALUATE] Sending evaluation request to Gemini API")
        response = model.generate_content(prompt)
        
        # Get response text
        ai_text = None
        try:
            # Try multiple ways to extract the text
            if hasattr(response, 'text'):
                ai_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                ai_text = response.parts[0].text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    ai_text = candidate.content.parts[0].text
            
            if not ai_text:
                ai_text = str(response)
                
            print(f"[EVALUATE] Successfully got AI text, length: {len(ai_text)}")
        except Exception as text_error:
            print(f"[EVALUATE] Error extracting text: {text_error}")
            return get_fallback_evaluation(is_spam, user_response)
        
        # Process text for better Markdown formatting
        ai_text = ai_text.strip()
        
        # Format numbered sections as headers
        for i in range(1, 6):
            ai_text = re.sub(r"^" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            ai_text = re.sub(r"^" + str(i) + r"\)\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
            ai_text = re.sub(r"^#{1,5}\s+" + str(i) + r"\.\s+(.+)$", r"## " + str(i) + r". \1", ai_text, flags=re.MULTILINE)
        
        # Format bullet points and emphasis
        ai_text = re.sub(r"^\*\s*(?=\S)", "* ", ai_text, flags=re.MULTILINE)
        ai_text = re.sub(r"(?<!\*)\*\*(?=\S)", "** ", ai_text)
        ai_text = re.sub(r"(?<=\S)\*\*(?!\*)", " **", ai_text)
        
        # Add paragraph breaks
        ai_text = re.sub(r"(?<=[.!?])\s+(?=[A-Z])", "\n\n", ai_text)
        ai_text = re.sub(r"(?<=[^\n])(?=^##)", "\n\n", ai_text, flags=re.MULTILINE)
        
        # Convert markdown to HTML
        try:
            formatted_html = markdown.markdown(ai_text, extensions=['extra'])
            print("[EVALUATE] Successfully converted markdown to HTML")
        except Exception as md_error:
            print(f"[EVALUATE] Error in markdown conversion: {md_error}")
            formatted_html = f"<p>{ai_text.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
        
        # Add styling
        formatted_html = formatted_html.replace("<li>", "<li style='margin-bottom: 8px;'>")
        formatted_html = formatted_html.replace("<h2>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
        formatted_html = formatted_html.replace("</h2>", "</h3>")
        formatted_html = formatted_html.replace("<strong>", "<strong style='color: #2a3f54;'>")
        
        # Calculate score
        base_score = 8 if user_response == is_spam else 3
        
        try:
            # Extract score from text
            ai_score_text = ai_text.split("scale of 1-10")[1].split("\n")[0]
            ai_score = int(''.join(filter(str.isdigit, ai_score_text)))
            score = ai_score if 1 <= ai_score <= 10 else base_score
        except:
            score = base_score
        
        return {
            "feedback": formatted_html,
            "score": score
        }
    except Exception as e:
        print(f"[EVALUATE] Error in evaluation: {e}")
        traceback.print_exc()
        
        # Check for rate limits
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            if app:
                app.config['RATE_LIMITED'] = True
                app.config['RATE_LIMIT_TIME'] = current_time
            print(f"[EVALUATE] Rate limit detected: {error_str}")
        
        return get_fallback_evaluation(is_spam, user_response)

def get_fallback_evaluation(is_spam, user_response):
    """Generate a varied evaluation when AI isn't available"""
    correct = user_response == is_spam
    
    # Add more varied scoring
    if correct:
        base_score = random.randint(7, 9)  # Random score between 7-9
        
        # Choose from multiple feedback templates for variety
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Yes, the user's conclusion was correct.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>The user correctly identified whether this was a phishing email or not. They showed good judgment.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>While the conclusion was correct, a more detailed analysis would help strengthen phishing detection skills.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, the user's analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Good job identifying this email correctly! To improve further, practice identifying specific red flags in phishing emails and security features in legitimate emails.</p>
            """,
            
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Yes, your assessment was accurate.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>You correctly determined the nature of the email and demonstrated good security awareness.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>Your conclusion was correct, but including more specific details about what influenced your decision would strengthen your analysis.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, your analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Excellent work! In future analyses, try to point out specific elements like sender address anomalies, suspicious links, and urgency tactics.</p>
            """
        ]
        
        feedback = random.choice(templates).format(score=base_score)
    else:
        base_score = random.randint(2, 4)  # Random score between 2-4
        
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>No, the user's conclusion was incorrect.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>The user attempted to analyze the email, which is an important security practice.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>The user missed critical indicators that would have led to the correct classification of this email.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, the user's analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>For better results, carefully examine the sender's address, look for urgency cues in phishing emails, and check for suspicious links. With practice, your detection skills will improve.</p>
            """,
            
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Is the user's conclusion correct?</h3>
            <p>Unfortunately, your assessment was not accurate.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What did the user get right in their analysis?</h3>
            <p>You engaged with the exercise and considered the email's content, which is a good security habit.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What did the user miss or get wrong?</h3>
            <p>You missed some key indicators that would have helped correctly identify this email's legitimacy.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Score</h3>
            <p>On a scale of 1-10, your analysis rates a {score}.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Constructive feedback</h3>
            <p>Remember to check for inconsistencies in the domain name, generic greetings, poor grammar, and requests for sensitive information. These common indicators can help you make more accurate assessments.</p>
            """
        ]
        
        feedback = random.choice(templates).format(score=base_score)
    
    return {
        "feedback": feedback,
        "score": base_score
    }