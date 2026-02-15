"""
Email Generation Module - Gemini primary, Azure OpenAI fallback

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
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key, get_log_dir
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"
    def get_log_dir(): return None

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

# Import Google Generative AI (Gemini) with fallback
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

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

# Determine writable log directory (may be None on serverless)
LOG_DIR = get_log_dir()

# Gemini model configuration
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-1.5-pro").split(",")
    if m.strip()
]

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
        
        # Log status to debug file if available
        if LOG_DIR:
            log_path = os.path.join(LOG_DIR, 'api_key_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
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
    """Generate an AI email with robust error handling - Gemini primary, Azure fallback"""
    call_count = getattr(generate_ai_email, 'call_count', 0) + 1
    generate_ai_email.call_count = call_count
    
    print(f"[GENERATE] Starting email generation (call #{call_count})")
    log_api_key_info(app, call_count)
    
    # ── 1. Try Gemini (primary) ──────────────────────────────────────────
    gemini_key = GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key and GEMINI_AVAILABLE:
        try:
            print("[GENERATE] Attempting Gemini generation (primary)")
            result = multi_approach_generation_gemini(user_name, previous_responses, gemini_key)
            if result_has_valid_content(result):
                print("[GENERATE] Gemini generation succeeded")
                return result
            else:
                print("[GENERATE] Gemini generation returned empty result, falling back")
        except Exception as e:
            print(f"[GENERATE] Gemini error: {e}")
            log_api_request("generate_ai_email", 0, False, error=str(e), api_source="GEMINI")
    else:
        if not gemini_key:
            print("[GENERATE] No Gemini API key configured, skipping Gemini")
        if not GEMINI_AVAILABLE:
            print("[GENERATE] google-generativeai package not installed, skipping Gemini")

    # ── 2. Try Azure OpenAI (fallback) ───────────────────────────────────
    if AZURE_HELPERS_AVAILABLE:
        try:
            print("[GENERATE] Attempting Azure OpenAI generation (fallback)")
            result = multi_approach_generation_azure(user_name, previous_responses, app)
            if result_has_valid_content(result):
                print("[GENERATE] Azure OpenAI generation succeeded")
                return result
            else:
                print("[GENERATE] Azure OpenAI generation failed, falling back to template")
        except Exception as e:
            print(f"[GENERATE] Azure OpenAI error: {e}")
            log_api_request("generate_ai_email", 0, False, error=str(e), api_source="AZURE")
    
    # ── 3. Fallback to template email ────────────────────────────────────
    print("[GENERATE] Using template email fallback")
    return get_template_email()

def evaluate_explanation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY=None, genai=None, app=None):
    """Evaluate the user's explanation of why an email is phishing/legitimate - Gemini primary, Azure fallback"""
    try:
        print("[EVALUATE] Starting explanation evaluation")
        
        # ── 1. Try Gemini (primary) ──────────────────────────────────────
        gemini_key = GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key and GEMINI_AVAILABLE:
            try:
                result = evaluate_with_gemini(email_content, is_spam, user_response, user_explanation, gemini_key)
                if result:
                    return result
            except Exception as e:
                print(f"[EVALUATE] Gemini error: {e}")
                log_api_request("evaluate_explanation", 0, False, error=str(e), api_source="GEMINI")

        # ── 2. Try Azure OpenAI (fallback) ───────────────────────────────
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
# GEMINI IMPLEMENTATION
# =============================================================================

def _configure_gemini(api_key):
    """Configure the Gemini SDK with the provided API key."""
    import google.generativeai as _genai
    _genai.configure(api_key=api_key)
    return _genai

def _call_gemini_with_retry(api_key, prompt, max_attempts=3, initial_delay=0.5):
    """Call Gemini API with retry logic and model fallback."""
    _genai = _configure_gemini(api_key)

    models_to_try = [DEFAULT_GEMINI_MODEL] + DEFAULT_GEMINI_FALLBACK_MODELS

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    for model_name in models_to_try:
        for attempt in range(max_attempts):
            try:
                print(f"[GEMINI] Attempt {attempt + 1}/{max_attempts} with {model_name}")
                model = _genai.GenerativeModel(model_name, safety_settings=safety_settings)
                response = model.generate_content(prompt)

                if hasattr(response, 'text') and response.text and response.text.strip():
                    print(f"[GEMINI] Success with {model_name}")
                    return response.text
            except Exception as e:
                print(f"[GEMINI] Error with {model_name} attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(initial_delay * (2 ** attempt))

    return None


def multi_approach_generation_gemini(user_name, previous_responses, api_key):
    """Generate email using Gemini with multiple prompt approaches."""
    print("[GEMINI] Starting multi-approach generation")

    approaches = [
        "Generate a realistic training email (either phishing or legitimate) for cybersecurity education.",
        "Create a simulated email for security awareness training purposes.",
        "Produce an educational email example for phishing detection training."
    ]

    for i, base_prompt in enumerate(approaches):
        try:
            prompt = build_generation_prompt(base_prompt, user_name, previous_responses)
            text = _call_gemini_with_retry(api_key, prompt)
            if text:
                parsed = parse_email_response(text)
                if parsed and result_has_valid_content(parsed):
                    print(f"[GEMINI] Success with approach {i + 1}")
                    return parsed
        except Exception as e:
            print(f"[GEMINI] Error with approach {i + 1}: {e}")
            continue

    print("[GEMINI] All approaches failed")
    return None


def evaluate_with_gemini(email_content, is_spam, user_response, user_explanation, api_key):
    """Evaluate user explanation using Gemini."""
    correct_answer = "phishing" if is_spam else "legitimate"
    user_answer = "phishing" if user_response else "legitimate"

    prompt = f"""You are a cybersecurity expert evaluating a student's analysis of an email for phishing detection training.

Email Content: {email_content[:500]}...

Correct Classification: {correct_answer}
User Classification: {user_answer}
User Explanation: {user_explanation}

Evaluate the student's explanation considering:
1. Accuracy (40%): Did they correctly identify the email type?
2. Analysis Quality (30%): How well did they explain their reasoning?
3. Security Awareness (20%): Did they identify relevant security indicators?
4. Learning Progress (10%): Evidence of cybersecurity understanding

Provide detailed, constructive feedback.

Format as JSON: {{"feedback": "detailed HTML feedback", "score": 7}}"""

    text = _call_gemini_with_retry(api_key, prompt)
    if text:
        text = clean_html_code_blocks(text)
        try:
            result = json.loads(text.strip())
            if "feedback" in result and "score" in result:
                result["feedback"] = clean_html_code_blocks(result["feedback"])
                return result
        except json.JSONDecodeError:
            extracted_score = extract_score_from_feedback(text, is_spam, user_response)
            return {"feedback": text, "score": extracted_score}

    return None

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

def extract_score_from_feedback(feedback_text, is_spam, user_response):
    """Extract the actual score from AI feedback text that contains point breakdowns"""
    try:
        import re
        
        # Look for point patterns like "+3 points", "+0 points", etc.
        point_pattern = r'\(\+(\d+)\s+points?\)'
        matches = re.findall(point_pattern, feedback_text)
        
        if matches:
            # Sum all the points found
            total_points = sum(int(match) for match in matches)
            print(f"[EXTRACT_SCORE] Found point breakdown: {matches}, total: {total_points}")
            return total_points
        
        # Alternative pattern: look for "X points" without parentheses  
        alt_pattern = r'\+(\d+)\s+points?'
        alt_matches = re.findall(alt_pattern, feedback_text)
        
        if alt_matches:
            total_points = sum(int(match) for match in alt_matches)
            print(f"[EXTRACT_SCORE] Found alternative point breakdown: {alt_matches}, total: {total_points}")
            return total_points
        
        # Look for direct score mentions like "score: 7" or "Score: 7"
        score_pattern = r'score[:\s]+(\d+)'
        score_match = re.search(score_pattern, feedback_text, re.IGNORECASE)
        
        if score_match:
            score = int(score_match.group(1))
            print(f"[EXTRACT_SCORE] Found direct score mention: {score}")
            return score
        
        # Look for "X/10" pattern
        fraction_pattern = r'(\d+)/10'
        fraction_match = re.search(fraction_pattern, feedback_text)
        
        if fraction_match:
            score = int(fraction_match.group(1))
            print(f"[EXTRACT_SCORE] Found fraction score: {score}")
            return score
        
        # If no score found, use fallback logic
        print("[EXTRACT_SCORE] No score pattern found, using fallback logic")
        return 7 if user_response == is_spam else 3
        
    except Exception as e:
        print(f"[EXTRACT_SCORE] Error extracting score: {e}")
        # Return fallback score
        return 7 if user_response == is_spam else 3

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
                # Clean HTML code blocks from AI response
                text_content = clean_html_code_blocks(text_content)
                
                try:
                    # Try to parse JSON response
                    result = json.loads(text_content.strip())
                    if "feedback" in result and "score" in result:
                        # Clean HTML code blocks from feedback if it exists
                        if "feedback" in result:
                            result["feedback"] = clean_html_code_blocks(result["feedback"])
                        return result
                except json.JSONDecodeError:
                    # Fallback parsing - extract score from text content
                    extracted_score = extract_score_from_feedback(text_content, is_spam, user_response)
                    return {
                        "feedback": text_content,
                        "score": extracted_score
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

def clean_html_code_blocks(text):
    """
    Remove markdown code blocks (```html) from AI responses.
    This fixes the issue where AI returns HTML wrapped in markdown code blocks.
    """
    if not text:
        return text
    
    import re
    
    # Step 1: Handle complete text that is just a code block
    # Check for ```html ... ``` patterns that span the entire text
    html_block_pattern = r'^```html\s*\n?(.*?)\n?```\s*$'
    html_match = re.search(html_block_pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # Check for generic code blocks that span the entire text
    generic_block_pattern = r'^```\s*\n?(.*?)\n?```\s*$'
    generic_match = re.search(generic_block_pattern, text, flags=re.DOTALL)
    if generic_match:
        content = generic_match.group(1).strip()
        # Only remove code blocks if content clearly looks like HTML
        if (content.startswith('<') and content.endswith('>') and
            ('<h' in content.lower() or '<p' in content.lower() or '<div' in content.lower() or 
             '<strong' in content.lower() or '<ul' in content.lower() or '<li' in content.lower())):
            return content
    
    # Step 2: Handle embedded code blocks within text
    def is_html_content(content):
        """Check if content looks like HTML"""
        content = content.strip()
        return (content.startswith('<') and content.endswith('>') and
                ('<h' in content.lower() or '<p' in content.lower() or '<div' in content.lower() or 
                 '<strong' in content.lower() or '<ul' in content.lower() or '<li' in content.lower()))
    
    # Find and replace all ```html blocks (with proper closing)
    def replace_html_block(match):
        content = match.group(1).strip()
        if is_html_content(content):
            return content
        return match.group(0)  # Return original if not HTML
    
    # Pattern for ```html ... ``` anywhere in text
    text = re.sub(r'```html\s*\n?(.*?)\n?```', replace_html_block, text, flags=re.IGNORECASE | re.DOTALL)
    
    # Step 3: Handle malformed blocks (missing closing ```)
    def replace_malformed_block(match):
        content = match.group(1).strip()
        if is_html_content(content):
            return content
        return match.group(0)  # Return original if not HTML
    
    # Look for ```html at start of line or after whitespace, followed by HTML content
    # Stop at double newline, start of new sentence, or end of string
    text = re.sub(r'```html\s*\n?(.*?)(?=\n\s*\n|\n[A-Z]|$)', replace_malformed_block, text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()

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