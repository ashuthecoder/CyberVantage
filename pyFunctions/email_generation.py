"""
Email Generation Module - Azure OpenAI Only (Gemini removed as requested)

This module handles AI-powered email generation for security training simulations
and evaluation of user explanations about phishing emails.
"""

import random
import traceback
import datetime
import re
import markdown
import json
import os
import time

# =============================================================================
# INITIALIZATION AND IMPORTS
# =============================================================================

# Import API logging functions with fallback
try:
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"

# Import Azure OpenAI helper functions with fallback
try:
    from .azure_openai_helper import (
        azure_openai_completion, test_azure_openai_connection, 
        extract_text_from_response, call_azure_openai_with_retry
    )
    AZURE_HELPERS_AVAILABLE = True
except ImportError:
    AZURE_HELPERS_AVAILABLE = False
    def azure_openai_completion(*args, **kwargs): return None, "IMPORT_ERROR"
    def test_azure_openai_connection(*args, **kwargs): return {"status": "IMPORT_ERROR"}
    def extract_text_from_response(*args, **kwargs): return ""
    def call_azure_openai_with_retry(*args, **kwargs): return None, "IMPORT_ERROR"

# Import template email fallback
try:
    from .template_emails import get_template_email
except ImportError:
    def get_template_email():
        return {
            "sender": "security@company.com",
            "subject": "Security Training Email",
            "content": "<p>This is a template email for training purposes.</p>",
            "is_spam": False
        }

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_api_key_info(app, call_count):
    """Log API key information for diagnostic purposes"""
    try:
        print(f"[GENERATE] Call #{call_count} API key check")
        
        azure_key = None
        azure_endpoint = None
        
        if app:
            azure_key = app.config.get('AZURE_OPENAI_KEY')
            azure_endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
        
        azure_status = "Available" if azure_key and azure_endpoint else "Not configured"
        
        print(f"[GENERATE] Azure OpenAI API key status: {azure_status}")
        
        # Log status to debug file
        with open('logs/api_key_debug.log', 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - Call #{call_count} - Azure: {azure_status}\n")
            
    except Exception as e:
        print(f"[GENERATE] Error logging API key info: {e}")

def result_has_valid_content(result):
    """Check if a result has valid content"""
    if not result:
        return False
    
    if isinstance(result, dict):
        content = result.get('content', '')
        sender = result.get('sender', '')
        subject = result.get('subject', '')
        
        return bool(content and content.strip() and sender and subject)
    
    return False

# =============================================================================
# EMAIL GENERATION ENTRY POINTS
# =============================================================================

def generate_ai_email(user_name, previous_responses, GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an AI email with robust error handling - Azure OpenAI only"""
    call_count = getattr(generate_ai_email, 'call_count', 0) + 1
    generate_ai_email.call_count = call_count
    
    print(f"[GENERATE] Starting email generation (call #{call_count})")
    log_api_key_info(app, call_count)
    
    # Try Azure OpenAI first
    if AZURE_HELPERS_AVAILABLE:
        try:
            print("[GENERATE] Attempting Azure OpenAI generation")
            result = multi_approach_generation_azure(user_name, previous_responses, app)
            if result_has_valid_content(result):
                print("[GENERATE] Azure OpenAI generation succeeded")
                return result
            else:
                print("[GENERATE] Azure OpenAI generation failed, falling back to template")
        except Exception as e:
            print(f"[GENERATE] Azure OpenAI error: {e}")
            log_api_request("generate_ai_email", 0, False, error=str(e), api_source="AZURE")
    
    # Fallback to template email
    print("[GENERATE] Using template email fallback")
    return get_template_email()

def evaluate_explanation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY=None, genai=None, app=None):
    """Evaluate the user's explanation of why an email is phishing/legitimate - Azure OpenAI only"""
    try:
        print("[EVALUATE] Starting explanation evaluation")
        
        # Try Azure OpenAI first
        if AZURE_HELPERS_AVAILABLE:
            try:
                result = evaluate_with_azure(email_content, is_spam, user_response, user_explanation, app)
                if result:
                    return result
            except Exception as e:
                print(f"[EVALUATE] Azure OpenAI error: {e}")
                log_api_request("evaluate_explanation", 0, False, error=str(e), api_source="AZURE")
        
        # Fallback evaluation
        print("[EVALUATE] Using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
        
    except Exception as e:
        print(f"[EVALUATE] Error in evaluate_explanation: {e}")
        traceback.print_exc()
        return get_fallback_evaluation(is_spam, user_response)

# =============================================================================
# AZURE OPENAI IMPLEMENTATION
# =============================================================================

def multi_approach_generation_azure(user_name, previous_responses, app):
    """Generate email using Azure OpenAI with multiple prompt approaches"""
    print("[AZURE] Starting multi-approach generation")
    
    approaches = [
        "Generate a realistic training email (either phishing or legitimate) for cybersecurity education.",
        "Create a simulated email for security awareness training purposes.",
        "Produce an educational email example for phishing detection training."
    ]
    
    for i, base_prompt in enumerate(approaches):
        try:
            print(f"[AZURE] Trying approach {i+1}: {base_prompt[:50]}...")
            
            # Build full prompt
            prompt = build_generation_prompt(base_prompt, user_name, previous_responses)
            
            # Call Azure OpenAI
            response, status = call_azure_openai_with_retry(
                messages=[{"role": "user", "content": prompt}],
                app=app,
                max_tokens=512,
                temperature=0.7
            )
            
            if response and status == "SUCCESS":
                # Extract and parse response
                text_content = extract_text_from_response(response)
                if text_content:
                    parsed = parse_email_response(text_content)
                    if parsed and result_has_valid_content(parsed):
                        print(f"[AZURE] Success with approach {i+1}")
                        return parsed
            
            print(f"[AZURE] Approach {i+1} failed")
            
        except Exception as e:
            print(f"[AZURE] Error with approach {i+1}: {e}")
            continue
    
    print("[AZURE] All approaches failed")
    return None

def evaluate_with_azure(email_content, is_spam, user_response, user_explanation, app):
    """Evaluate user explanation using Azure OpenAI"""
    try:
        print("[AZURE] Starting evaluation")
        
        # Build evaluation prompt
        correct_answer = "phishing" if is_spam else "legitimate"
        user_answer = "phishing" if user_response else "legitimate"
        
        prompt = f"""You are a cybersecurity expert evaluating a student's analysis of an email for phishing detection training.

Email Content: {email_content[:500]}...

Correct Classification: {correct_answer}
User Classification: {user_answer}
User Explanation: {user_explanation}

Evaluate the student's explanation considering these factors:

1. **Accuracy (40%)**: Did they correctly identify the email type?
2. **Analysis Quality (30%)**: How well did they explain their reasoning?
3. **Security Awareness (20%)**: Did they identify relevant security indicators?
4. **Learning Progress (10%)**: Evidence of cybersecurity understanding

Score calculation:
- Base score starts at 5/10
- Correct classification: +2-3 points
- Good reasoning/explanation: +1-2 points  
- Identification of specific indicators: +1-2 points
- Demonstration of security knowledge: +0-1 points
- Incorrect classification but good reasoning: partial credit possible

Provide detailed, constructive feedback that helps them improve their phishing detection skills.

Format as JSON: {{"feedback": "detailed HTML feedback with specific recommendations", "score": 7}}"""
        
        # Call Azure OpenAI
        response, status = call_azure_openai_with_retry(
            messages=[{"role": "user", "content": prompt}],
            app=app,
            max_tokens=1024,  # Increased from 256 to prevent feedback truncation
            temperature=0.3
        )
        
        if response and status == "SUCCESS":
            text_content = extract_text_from_response(response)
            if text_content:
                try:
                    # Try to parse JSON response
                    result = json.loads(text_content.strip())
                    if "feedback" in result and "score" in result:
                        return result
                except json.JSONDecodeError:
                    # Fallback parsing
                    return {
                        "feedback": text_content,
                        "score": 7
                    }
        
        return None
        
    except Exception as e:
        print(f"[AZURE] Evaluation error: {e}")
        return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_generation_prompt(base_prompt, user_name, previous_responses):
    """Build a complete prompt for email generation"""
    import random
    
    # Add randomization to ensure uniqueness
    random_id = random.randint(10000, 99999)
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    
    prompt = f"""{base_prompt}

Requirements:
- Create ONE realistic email (either phishing or legitimate)
- Include sender, subject, date, and content
- Make it appropriate for cybersecurity training
- Performance context: {previous_responses}
- Format as JSON with keys: sender, subject, date, content, is_spam
- Content should be HTML formatted
- Vary topics to keep training interesting
- Do NOT use personal user information in email content
- Use generic terms like "user", "customer", "subscriber" instead of specific names
- Include unique reference ID {random_id}-{timestamp} for variety
- Ensure content is unique and not repetitive

Generate the email now:"""
    
    return prompt

def parse_email_response(text_content):
    """Parse email response from AI"""
    try:
        # Try to find JSON in the response
        json_start = text_content.find('{')
        json_end = text_content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text_content[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['sender', 'subject', 'content', 'is_spam']
            if all(field in parsed for field in required_fields):
                # Ensure date field
                if 'date' not in parsed:
                    parsed['date'] = datetime.datetime.now().strftime("%B %d, %Y")
                return parsed
        
        return None
        
    except Exception as e:
        print(f"[PARSE] Error parsing response: {e}")
        return None

def get_fallback_evaluation(is_spam, user_response):
    """Generate a dynamic evaluation when AI isn't available"""
    correct = (user_response == is_spam)
    
    # Base scoring - more nuanced than just 8 or 3
    if correct:
        # Correct answers get scores between 6-9 with some randomness for variety
        base_score = 7 + random.randint(0, 2)  # 7-9 range
        feedback = "<p>✓ <strong>Correct identification!</strong> You properly identified this email.</p>"
    else:
        # Incorrect answers get scores between 2-5 with some variation
        base_score = 3 + random.randint(0, 2)  # 3-5 range  
        feedback = "<p>✗ <strong>Incorrect identification.</strong> Review the email characteristics more carefully.</p>"
    
    # Add additional feedback based on email type
    if is_spam:
        if correct:
            feedback += """
            <p><strong>Good catch!</strong> This was indeed a phishing/spam email. Key indicators to look for in such emails include:</p>
            <ul>
                <li>Suspicious sender domains or mismatched addresses</li>
                <li>Urgency tactics or threats</li>
                <li>Requests for personal information or credentials</li>
                <li>Poor grammar or formatting</li>
                <li>Unexpected attachments or links</li>
            </ul>
            """
        else:
            feedback += """
            <p><strong>This was actually a phishing email.</strong> Here are some warning signs you might have missed:</p>
            <ul>
                <li>Check the sender's email address carefully</li>
                <li>Look for urgent language designed to make you act quickly</li>
                <li>Be suspicious of unexpected requests for information</li>
                <li>Verify independently before clicking any links</li>
            </ul>
            """
    else:
        if correct:
            feedback += """
            <p><strong>Well done!</strong> This was a legitimate email. Good signs that indicated authenticity might include:</p>
            <ul>
                <li>Sender from a recognized, legitimate domain</li>
                <li>Professional formatting and tone</li>
                <li>Reasonable requests appropriate to the context</li>
                <li>No urgent pressure tactics</li>
            </ul>
            """
        else:
            feedback += """
            <p><strong>This was actually a legitimate email.</strong> Consider these factors when evaluating emails:</p>
            <ul>
                <li>Verify the sender's domain and identity</li>
                <li>Consider if the request makes sense in context</li>
                <li>Look for signs of authenticity vs. deception</li>
                <li>When in doubt, verify through alternative means</li>
            </ul>
            """
    
    # Add general security tips
    feedback += """
    <p><strong>Remember:</strong> When in doubt about an email's authenticity, it's always better to verify through independent means before taking any action.</p>
    """
    
    return {
        "feedback": feedback,
        "score": base_score
    }