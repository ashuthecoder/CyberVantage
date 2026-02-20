"""
Email Generation Module

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

# No longer using Gemini - removed all Google AI imports as requested

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
    def extract_text_from_response(*args, **kwargs): return None
    def call_azure_openai_with_retry(*args, **kwargs): return None, "IMPORT_ERROR"

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# =============================================================================
# AI RETRY HELPERS AND CONFIGURATION
# =============================================================================

# Model configuration from environment variables
DEFAULT_PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
DEFAULT_FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-pro,gemini-2.0-flash").split(",") if m.strip()]

# Legacy fallback list for backward compatibility (stable, non-deprecated models)
DEFAULT_MODEL_FALLBACK_LIST = ["gemini-2.5-pro", "gemini-2.0-flash"]

def call_gemini_with_retry(model_name, prompt, generation_config, max_attempts=3, 
                          fallback_models=None, initial_delay=0.5):
    """
    Call Gemini API with retry logic and exponential backoff.
    
    Args:
        model_name: Primary model to try
        prompt: The prompt to send
        generation_config: Generation configuration
        max_attempts: Maximum retry attempts per model
        fallback_models: List of fallback models to try
        initial_delay: Initial delay between retries in seconds
    
    Returns:
        tuple: (response, successful_model_name) or (None, None) if all fail
    """
    import google.generativeai as genai
    
    models_to_try = [model_name]
    if fallback_models:
        models_to_try.extend(fallback_models)
    
    for model_name_to_try in models_to_try:
        print(f"[RETRY] Trying model: {model_name_to_try}")
        
        for attempt in range(max_attempts):
            try:
                # Create model with safety settings
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
                }
                
                model = genai.GenerativeModel(model_name_to_try, safety_settings=safety_settings)
                
                print(f"[RETRY] Attempt {attempt + 1}/{max_attempts} with {model_name_to_try}")
                response = model.generate_content(prompt, generation_config=generation_config)
                
                # Check if response has usable text parts
                if has_usable_text_parts(response):
                    print(f"[RETRY] Success with {model_name_to_try} on attempt {attempt + 1}")
                    return response, model_name_to_try
                else:
                    print(f"[RETRY] Response from {model_name_to_try} has no usable text parts")
                    if attempt < max_attempts - 1:
                        delay = initial_delay * (2 ** attempt)  # Exponential backoff
                        print(f"[RETRY] Waiting {delay}s before retry...")
                        time.sleep(delay)
                    
            except InternalServerError as e:
                print(f"[RETRY] InternalServerError on attempt {attempt + 1} with {model_name_to_try}: {e}")
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)  # Exponential backoff
                    print(f"[RETRY] Waiting {delay}s before retry...")
                    time.sleep(delay)
                else:
                    print(f"[RETRY] Max attempts reached for {model_name_to_try}")
                    
            except Exception as e:
                error_str = str(e)
                print(f"[RETRY] Other error on attempt {attempt + 1} with {model_name_to_try}: {e}")
                
                # Check for 400 response_mime_type error specifically
                if "400" in error_str and "response_mime_type" in error_str:
                    print(f"[RETRY] Detected invalid generation_config error: {e}")
                    # Log the error to API logs
                    try:
                        log_api_request("call_gemini_with_retry", 0, False, 
                                       error=f"Invalid generation_config: {error_str}", 
                                       fallback_reason="invalid_generation_config")
                    except:
                        pass  # Don't let logging errors break the flow
                
                # For non-retryable errors, break out of retry loop for this model
                break
    
    print("[RETRY] All models and attempts failed")
    return None, None

def has_usable_text_parts(response):
    """Check if response contains usable text parts"""
    try:
        # Try the most common access pattern first
        if hasattr(response, 'text') and response.text and response.text.strip():
            return True
            
        # Check candidates structure
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text and part.text.strip():
                            return True
        
        return False
    except Exception as e:
        print(f"[RETRY] Error checking text parts: {e}")
        return False

# =============================================================================
# EMAIL GENERATION ENTRY POINTS
# =============================================================================

def generate_ai_email(user_name, previous_responses, GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an AI email with robust error handling"""
    print(f"[GENERATE] Starting email generation for user: {user_name}")
    
    # Add debugging information about call count
    if not hasattr(generate_ai_email, 'call_count'):
        generate_ai_email.call_count = 0
    generate_ai_email.call_count += 1
    
    print(f"[GENERATE] This is call #{generate_ai_email.call_count} to generate_ai_email")
    
    # Log API key info
    log_api_key_info(app, generate_ai_email.call_count)

    # Import here to avoid circular imports
    from .template_emails import get_template_email

    # Try Azure OpenAI first if available
    if app and app.config.get('AZURE_OPENAI_KEY') and app.config.get('AZURE_OPENAI_ENDPOINT') and AZURE_HELPERS_AVAILABLE:
        print("[GENERATE] Attempting to use Azure OpenAI")
        result = multi_approach_generation_azure(user_name, previous_responses, app)
        
        if result_has_valid_content(result):
            print("[GENERATE] Azure OpenAI generation succeeded")
            return result
        else:
            print("[GENERATE] Azure OpenAI generation failed, falling back to Gemini")
    
    # Early returns for missing prerequisites
    if not GOOGLE_API_KEY or not genai:
        log_api_request("generate_ai_email", 0, False, error="No API key or genai module", api_source="GEMINI")
        print("[GENERATE] No API key or genai module - using template email")
        return get_template_email()

    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("generate_ai_email", 0, False, error="Rate limit reached", api_source="GEMINI")
        print("[GENERATE] Rate limit reached - using template email")
        return get_template_email()

    # Try multiple generation approaches to work around content filtering
    result = multi_approach_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app)
    
    # Fall back to template if all approaches fail
    if not result_has_valid_content(result):
        print("[GENERATE] All generation approaches failed - using template")
        return get_template_email()
        
    return result

def evaluate_explanation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY=None, genai=None, app=None):
    """Evaluate the user's explanation of why an email is phishing/legitimate"""
    print(f"[EVALUATE] Starting evaluation. Is spam: {is_spam}, User said: {user_response}")

    # Early return conditions
    if should_use_fallback(app):
        log_api_request("evaluate_explanation", 0, False, error="Using fallback due to rate limit", fallback_reason="rate_limited", api_source="GEMINI")
        return get_fallback_evaluation(is_spam, user_response, fallback_reason="rate_limited")

    # Try Azure OpenAI first if available
    if app and app.config.get('AZURE_OPENAI_KEY') and app.config.get('AZURE_OPENAI_ENDPOINT') and AZURE_HELPERS_AVAILABLE:
        print("[EVALUATE] Attempting to use Azure OpenAI")
        result = execute_evaluation_azure(email_content, is_spam, user_response, user_explanation, app)
        
        if result and 'feedback' in result and result['feedback']:
            print("[EVALUATE] Azure OpenAI evaluation succeeded")
            return result
        else:
            print("[EVALUATE] Azure OpenAI evaluation failed, falling back to Gemini")

    if not GOOGLE_API_KEY or not genai:
        log_api_request("evaluate_explanation", 0, False, error="No API key or genai module", fallback_reason="missing_api_key", api_source="GEMINI")
        print("[EVALUATE] No API key - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response, fallback_reason="missing_api_key")

    # Use caching if we have a user explanation
    if user_explanation:
        cache_key = create_cache_key("eval", f"{is_spam}_{user_response}_{user_explanation[:500]}")
        
        def perform_evaluation():
            return execute_evaluation(email_content, is_spam, user_response, user_explanation, 
                                    GOOGLE_API_KEY, genai, app)
        
        return get_cached_or_generate(cache_key, perform_evaluation)
    else:
        # If no explanation, execute directly
        return execute_evaluation(email_content, is_spam, user_response, user_explanation, 
                                GOOGLE_API_KEY, genai, app)

# =============================================================================
# AZURE OPENAI IMPLEMENTATION
# =============================================================================

def multi_approach_generation_azure(user_name, previous_responses, app):
    """Try multiple generation approaches with Azure OpenAI with fallbacks"""
    # For detailed logging
    log_request_with_timestamp("Starting multi-approach Azure generation")
    
    # Try each approach in sequence, returning the first one that works
    approaches = [
        ("standard", lambda: try_standard_generation_azure(user_name, previous_responses, app)),
        ("neutral", lambda: try_neutral_generation_azure(user_name, previous_responses, app)),
        ("structured", lambda: try_structured_generation_azure(user_name, previous_responses, app)),
        ("basic", lambda: try_basic_generation_azure(user_name, app))
    ]
    
    for name, approach_func in approaches:
        try:
            print(f"[GENERATE] Trying Azure {name} generation approach")
            result = approach_func()
            if result_has_valid_content(result):
                print(f"[GENERATE] Azure {name.capitalize()} generation succeeded")
                return result
            print(f"[GENERATE] Azure {name.capitalize()} generation returned invalid content")
        except Exception as e:
            print(f"[GENERATE] Azure {name.capitalize()} generation failed with error: {e}")
    
    return None

def try_standard_generation_azure(user_name, previous_responses, app):
    """Try standard generation approach with Azure OpenAI"""
    system_prompt = """You are a cybersecurity training email generator. Create ONE realistic email for a phishing simulation tailored to the user's performance."""
    
    user_prompt = f"""
User performance summary: {previous_responses}

Output strictly in EXACTLY the following format (no extra commentary, no code fences):

Sender: <single email address>
Subject: <concise subject>
Date: {datetime.datetime.now().strftime("%B %d, %Y")}
Content:
<html><body>
<!-- Provide the email body as HTML paragraphs and links; no external CSS -->
</body></html>
Is_spam: <true|false>

Guidelines:
- If phishing (Is_spam: true): include subtle but identifiable red flags (lookalike domains, mismatched link text vs href, urgency, credential/payment requests).
- If legitimate (Is_spam: false): realistic tone with legitimate cues; avoid phishing indicators (no lookalike domains, no urgent threats, no requests for credentials).
- Use generic terms like "customer", "user", "subscriber" instead of specific names
- Do NOT include personal user information in email content
- Ensure email content is unique with timestamp or reference numbers"""
- Vary topics; do not reuse predefined examples; avoid the words "phishing" or "simulation".
- All links must be plausible; for phishing, use lookalike domains; for legitimate, use real domains.
- Do NOT include any fields other than Sender, Subject, Date, Content, Is_spam in that exact order.
"""
    
    # Log API request
    log_api_request("azure_standard_generation", user_prompt, True, 
                   system_prompt=system_prompt, api_source="AZURE")
    
    # Call Azure OpenAI
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.7,
        app=app
    )
    
    if not text or status != "SUCCESS":
        print(f"[GENERATE] Azure standard generation failed with status: {status}")
        return None
    
    # Process and format result
    return process_email_text(text)

def try_neutral_generation_azure(user_name, previous_responses, app):
    """Try neutral generation approach with Azure OpenAI"""
    system_prompt = """You are an email template creator for training scenarios. Your task is to create realistic sample emails."""
    
    user_prompt = f"""
Create a sample email that could be used for training purposes. It can be either legitimate or phishing.

Email details:
- Should be realistic and appropriate for a training scenario
- If you decide to make it a phishing email, include subtle red flags
- If you decide to make it legitimate, ensure it has typical legitimate email characteristics
- Use generic terms like "customer", "user", "subscriber" instead of specific names
- Do NOT include personal user information in email content

Output format:
Sender: <email address>
Subject: <concise subject>
Date: {datetime.datetime.now().strftime("%B %d, %Y")}
Content:
<html><body>
<!-- Provide the email body as HTML paragraphs and links -->
</body></html>
Is_spam: <true|false>
"""
    
    # Log API request
    log_api_request("azure_neutral_generation", user_prompt, True, 
                   system_prompt=system_prompt, api_source="AZURE")
    
    # Call Azure OpenAI
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.7,
        app=app
    )
    
    if not text or status != "SUCCESS":
        print(f"[GENERATE] Azure neutral generation failed with status: {status}")
        return None
    
    # Process and format result
    return process_email_text(text)

def try_structured_generation_azure(user_name, previous_responses, app):
    """Try structured generation approach with Azure OpenAI"""
    system_prompt = """You are a data structure generator that creates JSON objects representing emails for a training system."""
    
    user_prompt = f"""
Generate a JSON structure representing an email. This can be either legitimate or phishing.

Requirements:
- Include sender, subject, date, content (HTML), and is_spam fields
- If phishing, include subtle red flags
- If legitimate, ensure it appears authentic
- Use generic terms like "customer", "user", "subscriber" 
- Do NOT include personal user information in content

Example structure:
{{
  "sender": "example@company.com",
  "subject": "Your Account Information",
  "date": "{datetime.datetime.now().strftime("%B %d, %Y")}",
  "content": "<html><body><p>Email content goes here</p></body></html>",
  "is_spam": true or false
}}

IMPORTANT: Your output should be ONLY the JSON object, nothing else.
"""
    
    # Log API request
    log_api_request("azure_structured_generation", user_prompt, True, 
                   system_prompt=system_prompt, api_source="AZURE")
    
    # Call Azure OpenAI
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.7,
        app=app
    )
    
    if not text or status != "SUCCESS":
        print(f"[GENERATE] Azure structured generation failed with status: {status}")
        return None
    
    # Process JSON result
    try:
        email_json = json.loads(text)
        
        # Convert to standard format
        email_text = f"""Sender: {email_json.get('sender', 'unknown@example.com')}
Subject: {email_json.get('subject', 'No Subject')}
Date: {email_json.get('date', datetime.datetime.now().strftime("%B %d, %Y"))}
Content: {email_json.get('content', '<html><body><p>No content available</p></body></html>')}
Is_spam: {str(email_json.get('is_spam', False)).lower()}"""
        
        return process_email_text(email_text)
    except Exception as e:
        print(f"[GENERATE] Error processing JSON from Azure structured generation: {e}")
        return None

def try_basic_generation_azure(user_name, app):
    """Try basic generation approach with Azure OpenAI"""
    system_prompt = """You will create a simple email for training purposes."""
    
    user_prompt = f"""
Create a simple email for cybersecurity training. Decide if it should be phishing or legitimate.
Use generic addressing and do NOT include personal user information.

Format your response exactly as:
Sender: [email]
Subject: [subject]
Date: {datetime.datetime.now().strftime("%B %d, %Y")}
Content: [HTML content]
Is_spam: [true/false]
"""
    
    # Log API request
    log_api_request("azure_basic_generation", user_prompt, True, 
                   system_prompt=system_prompt, api_source="AZURE")
    
    # Call Azure OpenAI
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=512,
        temperature=0.7,
        app=app
    )
    
    if not text or status != "SUCCESS":
        print(f"[GENERATE] Azure basic generation failed with status: {status}")
        return None
    
    # Process and format result
    return process_email_text(text)

def execute_evaluation_azure(email_content, is_spam, user_response, user_explanation, app):
    """Execute evaluation using Azure OpenAI"""
    correctness = "correctly" if user_response == is_spam else "incorrectly"
    action = "identified it as phishing" if user_response else "identified it as legitimate"
    correct_label = "phishing" if is_spam else "legitimate"
    
    system_prompt = """You are an expert cybersecurity educator evaluating a student's ability to identify phishing emails."""
    
    user_prompt = f"""
Evaluate this user's explanation for why they identified an email as phishing or legitimate.

Email content:
{email_content}

Facts:
- This email is actually {correct_label}.
- The user {correctness} {action}.
- Their explanation: "{user_explanation}"

Provide detailed feedback about:
1. The accuracy of their threat assessment
2. The quality of their explanation
3. What security indicators they correctly identified
4. What they missed or incorrectly identified
5. How they could improve their analysis

Also assign a score from 0-100 based on their understanding and explanation.

Format your response as HTML with appropriate headings and paragraphs.
"""
    
    # Use caching if we have a user explanation
    if user_explanation:
        cache_key = create_cache_key("azure_eval", f"{is_spam}_{user_response}_{user_explanation[:500]}")
        
        def perform_azure_evaluation():
            return _execute_azure_evaluation(email_content, is_spam, user_response, user_explanation, 
                                          system_prompt, user_prompt, app)
        
        return get_cached_or_generate(cache_key, perform_azure_evaluation)
    else:
        # If no explanation, execute directly
        return _execute_azure_evaluation(email_content, is_spam, user_response, user_explanation,
                                      system_prompt, user_prompt, app)

def _execute_azure_evaluation(email_content, is_spam, user_response, user_explanation, 
                           system_prompt, user_prompt, app):
    """Internal function to execute Azure OpenAI evaluation"""
    # Log API request
    log_api_request("azure_evaluation", user_prompt, True, 
                   system_prompt=system_prompt, api_source="AZURE")
    
    # Call Azure OpenAI
    text, status = azure_openai_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1024,
        temperature=0.7,
        app=app
    )
    
    if not text or status != "SUCCESS":
        print(f"[EVALUATE] Azure evaluation failed with status: {status}")
        return get_fallback_evaluation(is_spam, user_response, fallback_reason="azure_api_error")
    
    # Extract score using regex patterns
    score = 70  # Default score
    score_pattern = r"score[:\s]+(\d+)"
    score_matches = re.findall(score_pattern, text.lower())
    if score_matches:
        try:
            score = int(score_matches[0])
            # Ensure score is within bounds
            score = max(0, min(score, 100))
        except ValueError:
            pass
    
    return {
        'feedback': text,
        'score': score,
        'correct_identification': user_response == is_spam
    }

# =============================================================================
# EMAIL GENERATION IMPLEMENTATION
# =============================================================================

def multi_approach_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app):
    """Try multiple generation approaches with fallbacks"""
    # For detailed logging
    log_request_with_timestamp("Starting multi-approach generation")
    
    # Try each approach in sequence, returning the first one that works
    approaches = [
        ("standard", lambda: try_standard_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app)),
        ("neutral", lambda: try_neutral_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app)),
        ("structured", lambda: try_structured_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app)),
        ("basic", lambda: try_basic_generation(user_name, GOOGLE_API_KEY, genai, app))
    ]
    
    for name, approach_func in approaches:
        try:
            print(f"[GENERATE] Trying {name} generation approach")
            result = approach_func()
            if result_has_valid_content(result):
                print(f"[GENERATE] {name.capitalize()} generation succeeded")
                return result
            print(f"[GENERATE] {name.capitalize()} generation returned invalid content")
        except Exception as e:
            print(f"[GENERATE] {name.capitalize()} generation failed with error: {e}")
    
    return None

def try_standard_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app):
    """Try standard generation approach"""
    prompt = f"""
You are a cybersecurity training email generator. Create ONE realistic email for a phishing simulation tailored to the user's performance.

User name: {user_name}
Performance summary: {previous_responses}

Output strictly in EXACTLY the following format (no extra commentary, no code fences):

Sender: <single email address>
Subject: <concise subject>
Date: {datetime.datetime.now().strftime("%B %d, %Y")}
Content:
<html><body>
<!-- Provide the email body as HTML paragraphs and links; no external CSS -->
</body></html>
Is_spam: <true|false>

Guidelines:
- If phishing (Is_spam: true): include subtle but identifiable red flags (lookalike domains, mismatched link text vs href, urgency, credential/payment requests).
- If legitimate (Is_spam: false): realistic tone with legitimate cues; avoid phishing indicators (no lookalike domains, no urgent threats, no requests for credentials).
- Vary topics; do not reuse predefined examples; avoid the words "phishing" or "simulation".
- All links must be plausible; for phishing, use lookalike domains; for legitimate, use real domains.
- Do NOT include any fields other than Sender, Subject, Date, Content, Is_spam in that exact order.
"""
    
    # Configure API key
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    
    # Use generation config without response_mime_type
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    # Use retry mechanism with fallback models
    response, used_model = call_gemini_with_retry(
        model_name=DEFAULT_PRIMARY_MODEL,
        prompt=prompt,
        generation_config=generation_config,
        max_attempts=3,
        fallback_models=DEFAULT_FALLBACK_MODELS,
        initial_delay=0.5
    )
    
    if response is None:
        print("[GENERATE] Standard generation failed - no response from any model")
        return None
        
    # Extract content from response
    content = extract_content_from_response(response)
    if not content:
        print("[GENERATE] Standard generation failed - could not extract content")
        return None
        
    # Check if content contains fallback markers
    if ("Sender: training@securityawareness.com" in content and 
        "Subject: Security Training Email" in content):
        print("[GENERATE] Standard generation returned fallback content, treating as failure")
        return None
        
    # Parse email components
    try:
        email_data = parse_email_components(content)
        if email_data:
            print(f"[GENERATE] Standard generation succeeded with model: {used_model}")
            return email_data
        else:
            print("[GENERATE] Standard generation failed - could not parse email components")
            return None
    except Exception as e:
        print(f"[GENERATE] Standard generation failed - parsing error: {e}")
        return None

def try_neutral_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app):
    """Try with a more neutral prompt that might avoid content filters"""
    prompt = f"""
Create an email sample for educational purposes. Format:

Sender: (email address)
Subject: (brief subject line)
Date: {datetime.datetime.now().strftime("%B %d, %Y")}
Content:
<html><body>
<p>Email content here</p>
</body></html>
Is_spam: true or false

Make the email either legitimate (Is_spam: false) or suspicious (Is_spam: true). 
If suspicious, include subtle issues like slightly misspelled domains or links that don't match display text.
If legitimate, use proper formatting and realistic business content.
"""
    
    # Configure API key
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    
    # Use generation config without response_mime_type
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    # Use retry mechanism with fallback models
    response, used_model = call_gemini_with_retry(
        model_name=DEFAULT_PRIMARY_MODEL,
        prompt=prompt,
        generation_config=generation_config,
        max_attempts=3,
        fallback_models=DEFAULT_FALLBACK_MODELS,
        initial_delay=0.5
    )
    
    if response is None:
        print("[GENERATE] Neutral generation failed - no response from any model")
        return None
        
    # Extract content from response
    content = extract_content_from_response(response)
    if not content:
        print("[GENERATE] Neutral generation failed - could not extract content")
        return None
        
    # Check if content contains fallback markers
    if ("Sender: training@securityawareness.com" in content and 
        "Subject: Security Training Email" in content):
        print("[GENERATE] Neutral generation returned fallback content, treating as failure")
        return None
        
    # Parse email components
    try:
        email_data = parse_email_components(content)
        if email_data:
            print(f"[GENERATE] Neutral generation succeeded with model: {used_model}")
            return email_data
        else:
            print("[GENERATE] Neutral generation failed - could not parse email components")
            return None
    except Exception as e:
        print(f"[GENERATE] Neutral generation failed - parsing error: {e}")
        return None

def try_structured_generation(user_name, previous_responses, GOOGLE_API_KEY, genai, app):
    """Try a structured approach that generates parts separately"""
    # Generate just an email subject and sender
    subject_prompt = f"""
Generate ONLY a subject line and sender for an email. No other text.
Format exactly as:
Sender: name@example.com
Subject: Subject line here

Make it {"business-related" if random.random() > 0.5 else "personal"}.
"""
    
    # Configure API key
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    
    # Use generation config without response_mime_type
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    try:
        # Generate sender and subject using retry mechanism
        response, used_model = call_gemini_with_retry(
            model_name=DEFAULT_PRIMARY_MODEL,
            prompt=subject_prompt,
            generation_config=generation_config,
            max_attempts=3,
            fallback_models=DEFAULT_FALLBACK_MODELS,
            initial_delay=0.5
        )
        
        if response is None:
            print("[GENERATE] Structured generation failed - no response for subject/sender")
            return None
            
        subject_text = extract_content_from_response(response)
        if not subject_text:
            print("[GENERATE] Structured generation failed - could not extract subject/sender")
            return None
        
        # Parse sender and subject
        sender, subject = parse_sender_subject(subject_text)
        
        # Generate email body separately
        is_spam = random.choice([True, False])
        body_prompt = f"""
Write a short email body in HTML format. The email should be {"suspicious with subtle red flags" if is_spam else "legitimate and professional"}.
Include only the HTML content, nothing else.
"""
        
        # Generate body using retry mechanism
        body_response, used_model_body = call_gemini_with_retry(
            model_name=DEFAULT_PRIMARY_MODEL,
            prompt=body_prompt,
            generation_config=generation_config,
            max_attempts=3,
            fallback_models=DEFAULT_FALLBACK_MODELS,
            initial_delay=0.5
        )
        
        if body_response is None:
            print("[GENERATE] Structured generation failed - no response for body")
            return None
            
        body_text = extract_content_from_response(body_response)
        if not body_text:
            print("[GENERATE] Structured generation failed - could not extract body")
            return None
        
        # Clean up body text and format email
        body_text = clean_body_text(body_text)
        email_content = format_email_content(body_text)
        
        # Randomize sender domain for uniqueness
        sender = randomize_sender_domain(sender)
        
        result = {
            "sender": sender,
            "subject": subject,
            "date": datetime.datetime.now().strftime("%B %d, %Y"),
            "content": email_content,
            "is_spam": is_spam
        }
        
        print(f"[GENERATE] Structured generation succeeded with model: {used_model}")
        return result
        
    except Exception as e:
        print(f"[GENERATE] Error in structured generation: {e}")
        return None

def try_basic_generation(user_name, GOOGLE_API_KEY, genai, app):
    """Fallback to very basic generation approach"""
    # For when all else fails, create a super simple prompt
    is_spam = random.choice([True, False])
    email_type = "suspicious" if is_spam else "normal business"
    
    prompt = f"Write a short {email_type} email from a company to a customer."
    
    # Configure API key
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    
    # Use generation config without response_mime_type
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }
    
    try:
        # Use retry mechanism with fallback models
        response, used_model = call_gemini_with_retry(
            model_name=DEFAULT_PRIMARY_MODEL,
            prompt=prompt,
            generation_config=generation_config,
            max_attempts=3,
            fallback_models=DEFAULT_FALLBACK_MODELS,
            initial_delay=0.5
        )
        
        if response is None:
            print("[GENERATE] Basic generation failed - no response from any model")
            return None
        
        # Extract whatever we can get
        content = extract_content_from_response(response)
        
        # Check if content contains fallback markers
        if content and ("Sender: training@securityawareness.com" in content and 
                       "Subject: Security Training Email" in content):
            print("[GENERATE] Basic generation returned fallback content, treating as failure")
            return None
        
        if content:
            # Create our own metadata
            sender = f"service@{random_company_domain()}"
            subject = random_subject(is_spam)
            
            # Wrap the content in HTML
            email_content = f"<html><body><p>{content.replace('. ', '.</p><p>')}</p></body></html>"
            
            # Add a marker for uniqueness
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            email_content = email_content.replace('</body>', f'<!-- gen_id: {timestamp} --></body>')
            
            result = {
                "sender": sender,
                "subject": subject,
                "date": datetime.datetime.now().strftime("%B %d, %Y"),
                "content": email_content,
                "is_spam": is_spam
            }
            
            print(f"[GENERATE] Basic generation succeeded with model: {used_model}")
            return result
    except Exception as e:
        print(f"[GENERATE] Error in basic generation: {e}")
    
    return None

def execute_generation(prompt, GOOGLE_API_KEY, genai, app):
    """Execute the generation with the given prompt"""
    try:
        # Create model with safety settings off
        model = create_model(GOOGLE_API_KEY, genai)
        print("[GENERATE] Sending request to Gemini API with safety settings")
        
        # Log the API request attempt
        prompt_length = len(prompt)
        
        # Use generation config for more consistent results
        generation_config = {
            "temperature": 0.7,  # Some creativity for varied emails
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Debug the raw response
        debug_response_object(response, "EMAIL_GENERATION_RESPONSE")
        
        # Log successful API call
        log_api_request("generate_ai_email", prompt_length, True, 
                       len(str(response)) if response else 0,
                       api_source="GEMINI")

        # Check for empty content in response
        if is_empty_response(response):
            print("[GENERATE] Detected empty content with role only")
            return None

        # Extract content from response
        content = extract_content_from_response(response)
        
        if not content:
            log_api_request("generate_ai_email", prompt_length, False, 
                           error="Failed to extract content from response")
            print("[GENERATE] Failed to extract content from response")
            return None

        print(f"[GENERATE] Response content length: {len(content)}")
        print(f"[GENERATE] First 100 chars: {content[:100]}")

        # Parse email components
        try:
            email_data = parse_email_components(content)
            if not email_data:
                print("[GENERATE] Could not parse email components")
                return None
                
            return email_data
            
        except Exception as parse_error:
            log_api_request("generate_ai_email", prompt_length, False, 
                           error=f"Error parsing response: {parse_error}")
            print(f"[GENERATE] Error parsing response: {parse_error}")
            traceback.print_exc()
            return None
    except Exception as e:
        # Log failed API call
        log_api_request("generate_ai_email", len(prompt), False, error=e)
        print(f"[GENERATE] Error in AI email generation: {e}")
        traceback.print_exc()

        # Rate limit tracking
        handle_rate_limit_error(str(e), app)

        return None

def result_has_valid_content(result):
    """Check if the result has valid content"""
    if not result:
        return False
    if not isinstance(result, dict):
        return False
    if 'sender' not in result or 'subject' not in result or 'content' not in result:
        return False
    if not result['content'] or len(result['content']) < 20:
        return False
    
    # Reject static fallback content
    if (result.get('sender') == "training@securityawareness.com" or 
        result.get('subject') == "Security Training Email"):
        print("[GENERATE] Rejecting static fallback content")
        return False
    
    return True

# =============================================================================
# EVALUATION IMPLEMENTATION
# =============================================================================

def execute_evaluation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY, genai, app):
    """Execute the evaluation with the Gemini API"""
    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("evaluate_explanation", 0, False, error="Rate limit reached", fallback_reason="rate_limited")
        print("[EVALUATE] Rate limit reached - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response, fallback_reason="rate_limited")
        
    # Check for missing API key
    if not GOOGLE_API_KEY:
        log_api_request("evaluate_explanation", 0, False, error="Missing API key", fallback_reason="missing_api_key")
        print("[EVALUATE] Missing API key - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response, fallback_reason="missing_api_key")
        
    # Prepare evaluation prompt
    prompt = get_evaluation_prompt(email_content, is_spam, user_response, user_explanation)
    prompt_length = len(prompt)
    
    try:
        print("[EVALUATE] Sending evaluation request to Gemini API with retry logic")
        
        # Generation config for evaluation (removed response_mime_type to avoid 400 errors)
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048
        }
        
        # Configure API with key
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Use retry helper to call Gemini with environment-configured models
        response, successful_model = call_gemini_with_retry(
            model_name=DEFAULT_PRIMARY_MODEL,
            prompt=prompt,
            generation_config=generation_config,
            max_attempts=3,
            fallback_models=DEFAULT_FALLBACK_MODELS
        )
        
        if not response:
            log_api_request("evaluate_explanation", prompt_length, False, 
                           error="All retry attempts failed", fallback_reason="api_500")
            print("[EVALUATE] All retry attempts failed - using fallback evaluation")
            return get_fallback_evaluation(is_spam, user_response, fallback_reason="api_500")
        
        # Debug the raw response object before extraction
        debug_response_object(response, "EVALUATE_RESPONSE")
        
        # Extract text with improved robustness
        ai_text = extract_ai_text(response)
        
        if not ai_text:
            log_api_request("evaluate_explanation", prompt_length, False, 
                           error="Failed to extract AI text from response", fallback_reason="empty_parts")
            print("[EVALUATE] Failed to extract AI text - using fallback evaluation")
            return get_fallback_evaluation(is_spam, user_response, fallback_reason="empty_parts")

        # Only log SUCCESS after successful text extraction
        log_api_request("evaluate_explanation", prompt_length, True, 
                       len(ai_text), model_used=successful_model,
                       api_source="GEMINI" if "gemini" in (successful_model or "").lower() else "AZURE")

        # Debug the extracted text
        with open('logs/debug_text.log', 'a') as f:
            f.write(f"\n\n[{datetime.datetime.now()}] === EXTRACTED TEXT ===\n")
            f.write(f"Model used: {successful_model}\n")
            f.write(ai_text[:1000] + "...(truncated if longer)\n")
        
        print(f"[EVALUATE] Successfully extracted {len(ai_text)} chars using {successful_model}")
        print(f"[EVALUATE] AI response first 100 chars: {ai_text[:100]}")

        # Process Markdown and convert to HTML
        processed_html, score = process_ai_text_to_html(ai_text, user_response, is_spam)
        
        return {
            "feedback": processed_html,
            "score": score
        }
        
    except Exception as e:
        # Determine fallback reason based on exception type
        fallback_reason = "exception"
        if "safety" in str(e).lower() or "block" in str(e).lower():
            fallback_reason = "safety_block"
        elif "500" in str(e) or "internal" in str(e).lower():
            fallback_reason = "api_500"
        
        # Log failed API call with fallback reason
        log_api_request("evaluate_explanation", prompt_length, False, error=str(e), fallback_reason=fallback_reason)
        print(f"[EVALUATE] Error in evaluation: {e}")
        traceback.print_exc()
        handle_rate_limit_error(str(e), app)
        return get_fallback_evaluation(is_spam, user_response, fallback_reason=fallback_reason)

def get_evaluation_prompt(email_content, is_spam, user_response, user_explanation):
    """Generate the evaluation prompt"""
    return f"""
You are a rigorous security trainer. Evaluate the user's analysis of a potential phishing email. Be firm, specific, and constructive. Do not invent details not present in the email.

EMAIL (verbatim HTML/text):
{email_content}

Ground truth:
This {'IS' if is_spam else 'IS NOT'} a phishing/spam email.

User's verdict:
The user said this {'IS' if user_response else 'IS NOT'} a phishing/spam email.

User's explanation (verbatim):
{user_explanation}

Write feedback in Markdown with these exact sections and headings:

## 1. Verdict
State whether the user's verdict is Correct or Incorrect, and a one-sentence reason anchored to the email content.

## 2. What we expected to see
List the key signals a strong analysis should mention for this email. Include at least 3 specific indicators (sender/domain, URLs, urgency, grammar, requests for credentials, mismatch of display vs actual link, DKIM/DMARC cues if visible, etc.). For each, add a short why-it-matters.

## 3. What you did well
Bullet points, citing any correct observations from the user's explanation.

## 4. Where you went wrong
Bullet points, each describing one miss or mistake. For each item:
- What the user said (quote or paraphrase briefly)
- What the evidence in the email shows instead
- Why this matters

## 5. Evidence from the email
Quote or paraphrase 2–4 exact snippets from the email that support the correct verdict. Use blockquotes or inline code.

## 6. How to improve next time
3 concrete, actionable tips tailored to this case.

## 7. Score (1–10)
Give a score with a one-line justification referencing the bullets above.

Rules:
- Be concise but specific. Prefer bullet points over paragraphs.
- Never claim facts outside the email. If information is missing, say so.
- If the user got the verdict right but reasoning was weak, say that explicitly.
"""

def process_ai_text_to_html(ai_text, user_response, is_spam):
    """Process AI text into formatted HTML and extract score"""
    # Clean and standardize the text
    ai_text = ai_text.strip()
    
    # Debug pre-processing state
    print("[EVALUATE] Beginning markdown processing")
    
    # Fix common formatting issues specific to Gemini 2.5
    ai_text = fix_gemini_formatting(ai_text)
    
    # Debug post-processing state
    print(f"[EVALUATE] Processed markdown first 100 chars: {ai_text[:100]}")
    
    # Convert to HTML with robust error handling
    try:
        # Add extra extensions for better markdown support
        formatted_html = markdown.markdown(ai_text, extensions=['extra', 'tables', 'sane_lists'])
        print("[EVALUATE] Successfully converted markdown to HTML")
    except Exception as md_error:
        print(f"[EVALUATE] Error in markdown conversion: {md_error}")
        # Fallback to basic HTML conversion
        formatted_html = convert_to_basic_html(ai_text)
    
    # Apply styling to HTML elements
    formatted_html = apply_html_styling(formatted_html)
    
    # Extract score from the text
    score = extract_score(ai_text, user_response, is_spam)
    
    return formatted_html, score

def fix_gemini_formatting(ai_text):
    """Fix common formatting issues with Gemini 2.5 output"""
    # Process text for better Markdown formatting
    processed_text = ai_text
    
    # Fix headings - multiple approaches to catch different formats
    for i in range(1, 8):
        # Standard heading format
        processed_text = re.sub(r"^" + str(i) + r"\.\s*(.+)$", 
                              r"## " + str(i) + r". \1", 
                              processed_text, 
                              flags=re.MULTILINE)
        
        # Numbered list as heading
        processed_text = re.sub(r"^" + str(i) + r"\)\s*(.+)$", 
                              r"## " + str(i) + r". \1", 
                              processed_text, 
                              flags=re.MULTILINE)
        
        # Fix existing headings to consistent format
        processed_text = re.sub(r"^#{1,5}\s+" + str(i) + r"\.\s*(.+)$", 
                              r"## " + str(i) + r". \1", 
                              processed_text, 
                              flags=re.MULTILINE)
    
    # Fix bullet points
    processed_text = re.sub(r"^\*\s*", "* ", processed_text, flags=re.MULTILINE)
    processed_text = re.sub(r"^-\s*", "* ", processed_text, flags=re.MULTILINE)
    
    # Fix bold formatting
    processed_text = re.sub(r"\*\*\s*([^*]+)\s*\*\*", r"**\1**", processed_text)
    
    # Fix italic formatting
    processed_text = re.sub(r"\*\s*([^*]+)\s*\*", r"*\1*", processed_text)
    
    # Fix spacing issues around headings
    processed_text = re.sub(r"([^\n])\n(##)", r"\1\n\n\2", processed_text)
    
    # Add line breaks between sections for better parsing
    processed_text = re.sub(r"(##[^\n]+)\n([^\n#])", r"\1\n\n\2", processed_text)
    
    return processed_text

def convert_to_basic_html(text):
    """Convert text to basic HTML as a fallback"""
    # Convert headers
    for i in range(1, 8):
        text = re.sub(r"^#{1,6}\s*" + str(i) + r"\.?\s*(.+)$", 
                      r"<h3>\1</h3>", 
                      text, 
                      flags=re.MULTILINE)
    
    # Convert bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    
    # Convert bullets
    text = re.sub(r"^\*\s*(.+)$", r"<li>\1</li>", text, flags=re.MULTILINE)
    text = re.sub(r"^-\s*(.+)$", r"<li>\1</li>", text, flags=re.MULTILINE)
    
    # Wrap consecutive list items
    text = re.sub(r"(<li>.+</li>\n)+", r"<ul>\g<0></ul>", text)
    
    # Convert paragraphs
    text = re.sub(r"([^\n<>].+[^\n<>])(\n{2,}|$)", r"<p>\1</p>", text)
    
    return f"<div>{text}</div>"

def apply_html_styling(html):
    """Apply styling to HTML elements for better presentation"""
    styled_html = html
    
    # Style list items
    styled_html = styled_html.replace("<li>", "<li style='margin-bottom: 8px;'>")
    
    # Style headings
    styled_html = styled_html.replace("<h2>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
    styled_html = styled_html.replace("</h2>", "</h3>")
    
    # Style bold text
    styled_html = styled_html.replace("<strong>", "<strong style='color: #2a3f54;'>")
    
    # Style blockquotes
    styled_html = styled_html.replace("<blockquote>", "<blockquote style='border-left: 4px solid #ccc; padding-left: 15px; margin-left: 0; color: #555;'>")
    
    # Style code elements
    styled_html = styled_html.replace("<code>", "<code style='background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px;'>")
    
    return styled_html

def extract_score(ai_text, user_response, is_spam):
    """Extract a numerical score from the AI text"""
    # Default score based on correct/incorrect answer
    base_score = 8 if user_response == is_spam else 3
    
    # Try multiple patterns to extract score
    try:
        # Pattern 1: Look for score in section 7
        match = re.search(r"(?:^|##\s*7\.[^\n]*?)(?:score|rating)[^0-9]*([1-9]|10)\b", 
                         ai_text, 
                         flags=re.IGNORECASE | re.MULTILINE)
        if match:
            candidate_score = int(match.group(1))
            if 1 <= candidate_score <= 10:
                return candidate_score
                
        # Pattern 2: Look for "X/10" format
        match = re.search(r"(\d+)/10", ai_text)
        if match:
            candidate_score = int(match.group(1))
            if 1 <= candidate_score <= 10:
                return candidate_score
                
        # Pattern 3: Look for score after "scale of 1-10"
        if "scale of 1-10" in ai_text:
            ai_score_text = ai_text.split("scale of 1-10")[1].split("\n")[0]
            ai_score_digits = ''.join(filter(str.isdigit, ai_score_text))
            if ai_score_digits and 1 <= int(ai_score_digits) <= 10:
                return int(ai_score_digits)
    
    except Exception as score_error:
        print(f"[EVALUATE] Error extracting score: {score_error}")
    
    # Return base score if extraction failed
    return base_score

def get_fallback_evaluation(is_spam, user_response, fallback_reason=None):
    """Generate a varied evaluation when AI isn't available"""
    correct = user_response == is_spam
    
    # Add banner to indicate AI is temporarily unavailable
    banner = """
    <div style='background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 12px; margin-bottom: 20px; color: #6c757d; font-size: 14px;'>
        ⚠️ AI temporarily unavailable — showing basic feedback.
    </div>
    """
    
    # Add hidden comment for debugging (if fallback_reason provided)
    hidden_comment = ""
    if fallback_reason:
        timestamp = datetime.datetime.now().isoformat()
        hidden_comment = f"<!-- FALLBACK: {fallback_reason} at {timestamp} -->\n"

    if correct:
        base_score = random.randint(7, 9)
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Verdict</h3>
            <p>Correct. You accurately identified this email's status.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. What we expected to see</h3>
            <p>A good analysis should examine:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Sender address - Verify the domain matches the supposed organization</li>
              <li style='margin-bottom: 8px;'>Links and URLs - Check where they actually point</li>
              <li style='margin-bottom: 8px;'>Tone and urgency - Is the email creating pressure?</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What you did well</h3>
            <ul>
              <li style='margin-bottom: 8px;'>You made the correct overall assessment</li>
              <li style='margin-bottom: 8px;'>You trusted your security instincts</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Where you could improve</h3>
            <p>Your analysis could benefit from:</p>
            <ul>
              <li style='margin-bottom: 8px;'>More specific details about what influenced your decision</li>
              <li style='margin-bottom: 8px;'>Examples of indicators from the email</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Score</h3>
            <p>Your assessment scores {score}/10 - Good judgment but could use more detailed analysis.</p>
            """,
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Verdict</h3>
            <p>Your assessment was correct.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. Key indicators</h3>
            <p>For this type of email, pay attention to:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Domain authenticity - Is it from the legitimate organization?</li>
              <li style='margin-bottom: 8px;'>Content quality - Professional organizations maintain quality standards</li>
              <li style='margin-bottom: 8px;'>Request nature - What is the email asking you to do?</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. Strengths in your analysis</h3>
            <ul>
              <li style='margin-bottom: 8px;'>You reached the correct conclusion</li>
              <li style='margin-bottom: 8px;'>You showed good security awareness</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Areas for improvement</h3>
            <p>To strengthen your analysis:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Be more specific about red flags or security features you noticed</li>
              <li style='margin-bottom: 8px;'>Reference particular elements of the email</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Score</h3>
            <p>{score}/10 - Good assessment with room for more detailed analysis.</p>
            """
        ]
        feedback = random.choice(templates).format(score=base_score)
    else:
        base_score = random.randint(2, 4)
        templates = [
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Verdict</h3>
            <p>Your assessment was incorrect.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. Key indicators</h3>
            <p>For this type of email, look for:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Email address inconsistencies</li>
              <li style='margin-bottom: 8px;'>Suspicious links or attachments</li>
              <li style='margin-bottom: 8px;'>Urgency or pressure tactics</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. What you did right</h3>
            <ul>
              <li style='margin-bottom: 8px;'>You attempted to analyze the email</li>
              <li style='margin-bottom: 8px;'>You considered security implications</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Where you went wrong</h3>
            <p>You missed critical indicators that would have led to the correct assessment:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Not examining the sender address carefully enough</li>
              <li style='margin-bottom: 8px;'>Missing suspicious elements in the content</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Score</h3>
            <p>{score}/10 - Your analysis needs improvement, but security awareness develops with practice.</p>
            """,
            """
            <h3 style='color: #2a3f54; margin-top: 20px;'>1. Verdict</h3>
            <p>Unfortunately, your assessment was not accurate.</p>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>2. Important signals</h3>
            <p>When analyzing emails, always check:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Sender domain authenticity</li>
              <li style='margin-bottom: 8px;'>Link destinations (hover before clicking)</li>
              <li style='margin-bottom: 8px;'>Requests for sensitive information</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>3. Positive aspects</h3>
            <ul>
              <li style='margin-bottom: 8px;'>You engaged with the security assessment exercise</li>
              <li style='margin-bottom: 8px;'>You provided some analysis of the content</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>4. Critical misses</h3>
            <p>Your analysis missed:</p>
            <ul>
              <li style='margin-bottom: 8px;'>Key indicators in the email header</li>
              <li style='margin-bottom: 8px;'>Important content red flags</li>
            </ul>
            
            <h3 style='color: #2a3f54; margin-top: 20px;'>5. Score</h3>
            <p>{score}/10 - With practice and attention to detail, your phishing detection skills will improve.</p>
            """
        ]
        feedback = random.choice(templates).format(score=base_score)

    # Prepend hidden comment and banner to feedback
    final_feedback = hidden_comment + banner + feedback

    return {
        "feedback": final_feedback,
        "score": base_score
    }

def should_use_fallback(app):
    """Determine if fallback should be used based on rate limiting"""
    rate_limited = app.config.get('RATE_LIMITED', False) if app else False
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0) if app else 0
    current_time = datetime.datetime.now().timestamp()
    
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"[EVALUATE] Using fallback due to rate limit ({int(current_time - rate_limit_time)} seconds ago)")
        return True
    return False

# =============================================================================
# RESPONSE EXTRACTION FUNCTIONS
# =============================================================================

def extract_content_from_response(response):
    """Extract text content from various response formats, with handling for empty content"""
    content = None
    
    # Print debug info about response type
    print(f"[EXTRACT] Response type: {type(response)}")
    print(f"[EXTRACT] Response str: {str(response)[:200]}...")
    
    # Check for empty response
    if is_empty_response(response):
        print("[EXTRACT] Detected empty response with only role")
        print("[EXTRACT] Using static fallback due to empty parts")
        return generate_fallback_content()
        
    # Try various methods to extract content
    extraction_methods = [
        extract_via_text_property,
        extract_via_parts,
        extract_via_candidates,
        extract_via_result_field,
        extract_via_string_parsing
    ]
    
    for method in extraction_methods:
        try:
            content = method(response)
            if content:
                return content
        except Exception as e:
            print(f"[EXTRACT] Method {method.__name__} failed: {e}")
    
    # If all methods failed, return fallback content
    print("[EXTRACT] All extraction methods failed, using fallback")
    print("[EXTRACT] Using static fallback due to empty parts")
    return generate_fallback_content()

def extract_ai_text(response):
    """Extract text from AI response with comprehensive error handling"""
    # Write to debug log
    with open('logs/extraction_debug.log', 'a') as f:
        f.write(f"\n\n[{datetime.datetime.now()}] === EXTRACTION ATTEMPT ===\n")
        f.write(f"Response type: {type(response)}\n")
    
    text_parts = []
    
    try:
        # Method 1: Try the simple .text property first
        if hasattr(response, 'text') and response.text:
            text = response.text.strip()
            if text:
                print("[EXTRACT] Method 1: .text property succeeded")
                return text
        
        # Method 2: Iterate over candidates and parts to concatenate all text
        if hasattr(response, 'candidates') and response.candidates:
            for i, candidate in enumerate(response.candidates):
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for j, part in enumerate(candidate.content.parts):
                        if hasattr(part, 'text') and part.text:
                            part_text = part.text.strip()
                            if part_text:
                                text_parts.append(part_text)
                                print(f"[EXTRACT] Found text in candidate {i}, part {j}: {len(part_text)} chars")
        
        # Method 3: Try direct parts access
        if not text_parts and hasattr(response, 'parts') and response.parts:
            for j, part in enumerate(response.parts):
                if hasattr(part, 'text') and part.text:
                    part_text = part.text.strip()
                    if part_text:
                        text_parts.append(part_text)
                        print(f"[EXTRACT] Found text in part {j}: {len(part_text)} chars")
        
        # Method 4: Try content field
        if not text_parts and hasattr(response, 'content'):
            if hasattr(response.content, 'parts') and response.content.parts:
                for j, part in enumerate(response.content.parts):
                    if hasattr(part, 'text') and part.text:
                        part_text = part.text.strip()
                        if part_text:
                            text_parts.append(part_text)
                            print(f"[EXTRACT] Found text in content part {j}: {len(part_text)} chars")
        
        # Concatenate all found text parts
        if text_parts:
            combined_text = '\n'.join(text_parts)
            print(f"[EXTRACT] Successfully extracted {len(combined_text)} chars from {len(text_parts)} parts")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write(f"Success: extracted {len(combined_text)} chars from {len(text_parts)} parts\n")
            return combined_text
        
        # If no text found, check if response is blocked/empty
        if is_empty_response(response):
            print("[EXTRACT] Response contains only role with no content")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write("Empty response detected (role only)\n")
        else:
            print("[EXTRACT] No text parts found in response")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write("No text parts found\n")
        
        return None
        
    except Exception as e:
        print(f"[EXTRACT] Error during extraction: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Extraction error: {e}\n")
        return None

def extract_via_text_property(response):
    """Extract content using the text property"""
    if hasattr(response, 'text'):
        return response.text
    return None

def extract_via_parts(response):
    """Extract content using the parts structure"""
    if hasattr(response, 'parts') and response.parts:
        return response.parts[0].text
    return None

def extract_via_candidates(response):
    """Extract content using the candidates structure"""
    if hasattr(response, 'candidates') and response.candidates:
        cand = response.candidates[0]
        if hasattr(cand, 'content') and hasattr(cand.content, 'parts'):
            return cand.content.parts[0].text
    return None

def extract_via_content_field(response):
    """Extract content using the content property"""
    if hasattr(response, 'content'):
        if hasattr(response.content, 'parts') and response.content.parts:
            return response.content.parts[0].text
        
        # Try content as string
        try:
            return str(response.content)
        except:
            pass
    return None

def extract_via_result_field(response):
    """Extract content via the result field"""
    if hasattr(response, 'result'):
        try:
            # Try to access candidates through result
            if hasattr(response.result, 'candidates') and response.result.candidates:
                # Generate fallback content in case extraction fails
                for candidate in response.result.candidates:
                    if hasattr(candidate, 'content'):
                        # Check for content with parts
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            return candidate.content.parts[0].text
                        
                        # If content exists but only has role, create fallback content
                        if hasattr(candidate.content, 'role'):
                            return None  # Signal that we found an empty response
        except Exception as e:
            print(f"[EXTRACT] Error in result extraction: {e}")
    return None

def extract_via_string_parsing(response):
    """Extract content by parsing the string representation"""
    raw_string = str(response)
    
    # Try to find required fields in the string representation
    if "Sender:" in raw_string and "Subject:" in raw_string and "Content:" in raw_string:
        return raw_string
    
    return None

def extract_via_string_representation(response):
    """Extract content by parsing the string representation with JSON attempt"""
    raw_string = str(response)
    
    # Log the raw string for debugging
    with open('logs/extraction_debug.log', 'a') as f:
        f.write(f"Raw string: {raw_string[:500]}...(truncated)\n")
    
    # Check for empty content pattern
    if "content\": { \"role\": \"model\" }" in raw_string:
        print("[EXTRACT] Detected empty content with role only")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write("Detected empty content with role only\n")
        
        # Generate fallback text for evaluation
        if "evaluate" in raw_string.lower():
            return generate_fallback_evaluation()
    
    # Try to find text in JSON-like structure
    if '{' in raw_string and '}' in raw_string:
        try:
            # Find valid JSON substring
            start = raw_string.find('{')
            # Find balanced closing brace
            brace_count = 1
            end = start + 1
            while brace_count > 0 and end < len(raw_string):
                if raw_string[end] == '{':
                    brace_count += 1
                elif raw_string[end] == '}':
                    brace_count -= 1
                end += 1
            
            json_str = raw_string[start:end]
            data = json.loads(json_str)
            
            # Try common fields that might contain text
            for field in ['text', 'content', 'message', 'output', 'result', 'response']:
                if field in data:
                    return str(data[field])
        except Exception as json_error:
            with open('logs/extraction_debug.log', 'a') as f:
                f.write(f"JSON parsing failed: {json_error}\n")
    
    # Last resort: just use the string itself
    if len(raw_string) > 30:  # Arbitrary minimum length
        return raw_string
    
    return None

def is_empty_response(response):
    """Check if response contains only role with no content"""
    response_str = str(response)
    return "content\": { \"role\": \"model\" }" in response_str or \
           "\"content\": {\"role\": \"model\"}" in response_str

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def result_has_valid_content(result):
    """Check if a generation result has valid content"""
    if not result:
        return False
        
    required_fields = ['sender', 'subject', 'content', 'is_spam']
    return all(field in result for field in required_fields) and result['content']

def process_email_text(text):
    """Process raw email text into structured format"""
    if not text:
        return None
        
    # Initialize empty result
    result = {
        'sender': '',
        'subject': '',
        'date': datetime.datetime.now().strftime("%B %d, %Y"),
        'content': '',
        'is_spam': False
    }
    
    # Extract fields using regex
    sender_match = re.search(r'Sender:\s*(.*?)(?:\n|$)', text)
    subject_match = re.search(r'Subject:\s*(.*?)(?:\n|$)', text)
    date_match = re.search(r'Date:\s*(.*?)(?:\n|$)', text)
    content_match = re.search(r'Content:\s*(.*?)(?=Is_spam:|$)', text, re.DOTALL)
    is_spam_match = re.search(r'Is_spam:\s*(.*?)(?:\n|$)', text)
    
    # Update result if matches found
    if sender_match:
        result['sender'] = sender_match.group(1).strip()
        
    if subject_match:
        result['subject'] = subject_match.group(1).strip()
        
    if date_match:
        result['date'] = date_match.group(1).strip()
        
    if content_match:
        content = content_match.group(1).strip()
        # Check if content contains HTML tags
        if not re.search(r'<html|<body|<p>|<div', content):
            # Convert to HTML if it's plain text
            content = f"<html><body><p>{content.replace(chr(10), '</p><p>')}</p></body></html>"
        result['content'] = content
        
    if is_spam_match:
        spam_value = is_spam_match.group(1).strip().lower()
        result['is_spam'] = spam_value == 'true'
    
    # Validate minimum requirements
    if not result['sender'] or not result['subject'] or not result['content']:
        print("[GENERATE] Processed email missing required fields")
        return None
        
    return result

def log_api_key_info(app, call_count):
    """Log API key information for diagnostic purposes"""
    try:
        print(f"[GENERATE] Call #{call_count} API key check")
        
        gemini_key = None
        azure_key = None
        azure_endpoint = None
        
        if app:
            gemini_key = app.config.get('GOOGLE_API_KEY')
            azure_key = app.config.get('AZURE_OPENAI_KEY')
            azure_endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
        
        gemini_status = "Available" if gemini_key else "Not configured"
        azure_status = "Available" if azure_key and azure_endpoint else "Not configured"
        
        print(f"[GENERATE] Gemini API key status: {gemini_status}")
        print(f"[GENERATE] Azure OpenAI API key status: {azure_status}")
        
        # Log status to debug file
        with open('logs/api_key_debug.log', 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - Call #{call_count}: Gemini: {gemini_status}, Azure: {azure_status}\n")
            
    except Exception as e:
        print(f"[GENERATE] Error logging API key info: {e}")

def should_use_fallback(app):
    """Check if should use fallback evaluation (for rate limiting)"""
    # If rate limit check fails, use fallback
    if not check_rate_limit():
        print("[EVALUATE] Rate limit reached, using fallback")
        return True
        
    return False

def get_fallback_evaluation(is_spam, user_response, fallback_reason="unknown"):
    """Get fallback evaluation when API is unavailable"""
    correctness = "correctly" if user_response == is_spam else "incorrectly"
    email_type = "phishing" if is_spam else "legitimate"
    user_judgment = "phishing" if user_response else "legitimate"
    
    # Generate basic feedback based on correctness
    if user_response == is_spam:
        if is_spam:
            feedback = f"""
            <h3>Good work!</h3>
            <p>You correctly identified this as a phishing email. Being able to spot suspicious elements is an important security skill.</p>
            <p>Continue practicing to further improve your threat detection abilities.</p>
            """
            score = 85
        else:
            feedback = f"""
            <h3>Good assessment!</h3>
            <p>You correctly identified this as a legitimate email. Being able to recognize genuine communications is just as important as spotting threats.</p>
            <p>Continue practicing to maintain your ability to differentiate between legitimate and suspicious messages.</p>
            """
            score = 85
    else:
        if is_spam:
            feedback = f"""
            <h3>Room for improvement</h3>
            <p>This was actually a phishing email that you identified as legitimate. Missing phishing attempts can potentially expose systems to security risks.</p>
            <p>Look carefully for suspicious elements like unexpected requests, urgency, spelling errors, and mismatched or suspicious URLs.</p>
            """
            score = 40
        else:
            feedback = f"""
            <h3>Further practice needed</h3>
            <p>This was actually a legitimate email that you flagged as phishing. While caution is good, false positives can disrupt normal communications.</p>
            <p>Try to balance security awareness with recognizing expected, normal business communications.</p>
            """
            score = 60
    
    # Add fallback reason notice
    feedback += f"<p><small>Note: This is an automated assessment due to {fallback_reason}.</small></p>"
    
    return {
        'feedback': feedback,
        'score': score,
        'correct_identification': user_response == is_spam
    }

def log_request_with_timestamp(message):
    """Log a request with timestamp to the request timeline log"""
    try:
        with open('logs/request_timeline.log', 'a') as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            f.write(f"{timestamp} - {message}\n")
    except Exception as e:
        print(f"Error logging to timeline: {e}")

def create_model(GOOGLE_API_KEY, genai):
    """Create a model with safety settings turned off"""
    # Force new model creation each time to avoid stale state
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }
    
    return genai.GenerativeModel(DEFAULT_PRIMARY_MODEL, safety_settings=safety_settings)

def parse_email_components(content):
    """Parse the components of the generated email"""
    if "Sender:" not in content or "Subject:" not in content:
        print("[GENERATE] Missing expected fields in response")
        return None

    sender = content.split("Sender:", 1)[1].split("\n", 1)[0].strip()
    subject = content.split("Subject:", 1)[1].split("\n", 1)[0].strip()

    try:
        date = content.split("Date:", 1)[1].split("\n", 1)[0].strip()
    except:
        date = datetime.datetime.now().strftime("%B %d, %Y")

    if "Content:" in content and "Is_spam:" in content:
        email_content = content.split("Content:", 1)[1].split("Is_spam:", 1)[0].strip()
    else:
        print("[GENERATE] Could not extract email content properly")
        email_content = f"<p>Training email content.</p><p>{content}</p>"

    try:
        is_spam_section = content.split("Is_spam:", 1)[1].lower().strip()
        is_spam = "true" in is_spam_section or "yes" in is_spam_section
    except:
        is_spam = random.choice([True, False])

    # Ensure HTML body
    if not email_content.strip().startswith("<"):
        email_content = f"<p>{email_content.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"

    # Add a marker for uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    email_content = email_content.replace('</body>', f'<!-- gen_id: {timestamp} --></body>')
    if '</body>' not in email_content:
        email_content += f'<!-- gen_id: {timestamp} -->'

    # Randomize sender domain for uniqueness
    sender = randomize_sender_domain(sender)

    return {
        "sender": sender,
        "subject": subject,
        "date": date,
        "content": email_content,
        "is_spam": is_spam
    }

def randomize_sender_domain(sender):
    """Add slight randomization to sender domain for uniqueness"""
    if random.random() < 0.3 and "@" in sender:
        sp = sender.split('@')
        if len(sp) == 2:
            dp = sp[1].split('.')
            if len(dp) >= 2:
                dp[0] += str(random.randint(1, 999))
                sender = f"{sp[0]}@{'.'.join(dp)}"
    return sender

def parse_sender_subject(subject_text):
    """Parse sender and subject from the generated text"""
    sender = "training@example.com"
    subject = "Important Information"
    
    if subject_text:
        if "Sender:" in subject_text:
            sender = subject_text.split("Sender:")[1].split("\n")[0].strip()
        if "Subject:" in subject_text:
            subject = subject_text.split("Subject:")[1].split("\n")[0].strip()
    
    return sender, subject

def clean_body_text(body_text):
    """Clean and format body text"""
    if not body_text:
        return "<p>Hello,</p><p>This is an important message. Please review the attached information.</p><p>Regards,<br>The Team</p>"
    
    if not body_text.strip().startswith("<"):
        return f"<p>{body_text.replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>"
    
    return body_text

def format_email_content(body_text):
    """Format the email content with a unique marker"""
    email_content = f"<html><body>{body_text}</body></html>"
    
    # Add a marker for uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    email_content = email_content.replace('</body>', f'<!-- gen_id: {timestamp} --></body>')
    if '</body>' not in email_content:
        email_content += f'<!-- gen_id: {timestamp} -->'
    
    return email_content

def generate_fallback_content():
    """Generate fallback content when extraction fails"""
    return f"""
    Sender: training@securityawareness.com
    Subject: Security Training Email
    Date: {datetime.datetime.now().strftime("%B %d, %Y")}
    Content:
    <html><body>
    <p>Dear user,</p>
    <p>This is a training email to test your security awareness.</p>
    <p>Always verify the sender and check URLs before clicking.</p>
    </body></html>
    Is_spam: {"true" if random.choice([True, False]) else "false"}
    """

def generate_fallback_evaluation():
    """Generate fallback evaluation text"""
    return f"""
## 1. Verdict
The user's verdict was {"correct" if random.choice([True, False]) else "incorrect"}.

## 2. What we expected to see
* Check sender domain
* Verify links
* Look for urgency cues

## 3. What you did well
* Made an assessment
* Considered the email content

## 4. Where you went wrong
* Needed more specific analysis
* Missing critical indicators

## 5. Evidence from the email
Example content from the email.

## 6. How to improve next time
* Check sender domains carefully
* Hover over links to see destination
* Be suspicious of urgency

## 7. Score (1-10)
{random.randint(3, 8)} - Based on your analysis.
"""

def random_company_domain():
    """Generate a random company domain"""
    companies = ["acme", "globex", "initech", "umbrella", "stark", "wayne", "cyberdyne", "aperture"]
    tlds = ["com", "org", "net", "io", "tech"]
    return f"{random.choice(companies)}{random.randint(1, 999)}.{random.choice(tlds)}"

def random_subject(is_spam):
    """Generate a random email subject"""
    if is_spam:
        templates = [
            "URGENT: Your account needs verification",
            "Important security update required",
            "Your payment was declined",
            "Invoice #12345 - Immediate action required",
            "Your account has been limited"
        ]
    else:
        templates = [
            "Your monthly newsletter",
            "Meeting summary - August 2025",
            "Thank you for your purchase",
            "Your receipt from recent transaction",
            "Product update information"
        ]
    return random.choice(templates)

def handle_rate_limit_error(error_str, app):
    """Handle rate limit errors and update app config"""
    if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
        if app:
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = datetime.datetime.now().timestamp()
        print(f"[RATE_LIMIT] API rate limit detected: {error_str}")

def log_api_key_info(app, call_count):
    """Log information about API key for debugging"""
    if app:
        try:
            with open('logs/api_key_debug.log', 'a') as f:
                f.write(f"\n[{datetime.datetime.now()}] Email generation call #{call_count}\n")
                f.write(f"API key in app config: {bool(app.config.get('GOOGLE_API_KEY'))}\n")
                f.write(f"Rate limited?: {app.config.get('RATE_LIMITED', False)}\n")
        except Exception as e:
            print(f"[LOG] Error logging API key info: {e}")

def log_request_with_timestamp(message):
    """Log a request with timestamp for debugging"""
    try:
        with open('logs/request_timeline.log', 'a') as f:
            f.write(f"[{datetime.datetime.now()}] {message}\n")
    except Exception as e:
        print(f"[LOG] Error logging request: {e}")

def debug_response_object(response, label="DEBUG"):
    """Debug a response object's structure and content"""
    try:
        with open('logs/debug_response.log', 'a') as f:
            f.write(f"\n\n[{datetime.datetime.now()}] === {label} ===\n")
            
            # Log the type
            f.write(f"Response type: {type(response)}\n")
            
            # Log the raw response
            f.write(f"String representation: {str(response)[:1000]}...(truncated)\n")
            
            # Log all attributes
            f.write("Available attributes:\n")
            for attr in dir(response):
                if not attr.startswith('_'):  # Skip private attributes
                    try:
                        value = getattr(response, attr)
                        if not callable(value):  # Skip methods
                            if isinstance(value, (str, int, float, bool, list, dict)):
                                f.write(f"  {attr}: {str(value)[:500]}...(truncated if longer)\n")
                            else:
                                f.write(f"  {attr}: {type(value)}\n")
                    except Exception as e:
                        f.write(f"  {attr}: ERROR accessing - {str(e)}\n")
            
            # Try to JSON serialize if possible
            try:
                if hasattr(response, '__dict__'):
                    f.write("JSON representation attempt:\n")
                    json_data = json.dumps(response.__dict__, default=str, indent=2)
                    f.write(f"{json_data[:2000]}...(truncated if longer)\n")
            except Exception as json_error:
                f.write(f"Could not JSON serialize: {json_error}\n")
    except Exception as e:
        print(f"[DEBUG] Error debugging response: {e}")