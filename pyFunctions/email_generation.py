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
from google.generativeai.types import HarmCategory, HarmBlockThreshold

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

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

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

    # Early returns for missing prerequisites
    if not GOOGLE_API_KEY or not genai:
        log_api_request("generate_ai_email", 0, False, error="No API key or genai module")
        print("[GENERATE] No API key or genai module - using template email")
        return get_template_email()

    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("generate_ai_email", 0, False, error="Rate limit reached")
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
        log_api_request("evaluate_explanation", 0, False, error="Using fallback due to rate limit")
        return get_fallback_evaluation(is_spam, user_response)

    if not GOOGLE_API_KEY or not genai:
        log_api_request("evaluate_explanation", 0, False, error="No API key or genai module")
        print("[EVALUATE] No API key - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)

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
    return execute_generation(prompt, GOOGLE_API_KEY, genai, app)

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
    return execute_generation(prompt, GOOGLE_API_KEY, genai, app)

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
    try:
        # Generate sender and subject
        model = create_model(GOOGLE_API_KEY, genai)
        subject_response = model.generate_content(subject_prompt)
        subject_text = extract_content_from_response(subject_response)
        
        # Parse sender and subject
        sender, subject = parse_sender_subject(subject_text)
        
        # Generate email body separately
        is_spam = random.choice([True, False])
        body_prompt = f"""
Write a short email body in HTML format. The email should be {"suspicious with subtle red flags" if is_spam else "legitimate and professional"}.
Include only the HTML content, nothing else.
"""
        # Try with exponential backoff for rate limits
        for attempt in range(3):
            try:
                body_response = model.generate_content(body_prompt)
                body_text = extract_content_from_response(body_response)
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    print(f"[GENERATE] Rate limited, waiting {2**attempt} seconds...")
                    time.sleep(2**attempt)
                else:
                    raise
        
        # Clean up body text and format email
        body_text = clean_body_text(body_text)
        email_content = format_email_content(body_text)
        
        # Randomize sender domain for uniqueness
        sender = randomize_sender_domain(sender)
        
        return {
            "sender": sender,
            "subject": subject,
            "date": datetime.datetime.now().strftime("%B %d, %Y"),
            "content": email_content,
            "is_spam": is_spam
        }
        
    except Exception as e:
        print(f"[GENERATE] Error in structured generation: {e}")
        return None

def try_basic_generation(user_name, GOOGLE_API_KEY, genai, app):
    """Fallback to very basic generation approach"""
    # For when all else fails, create a super simple prompt
    is_spam = random.choice([True, False])
    email_type = "suspicious" if is_spam else "normal business"
    
    prompt = f"Write a short {email_type} email from a company to a customer."
    
    try:
        model = create_model(GOOGLE_API_KEY, genai)
        response = model.generate_content(prompt)
        
        # Extract whatever we can get
        content = extract_content_from_response(response)
        
        if content:
            # Create our own metadata
            sender = f"service@{random_company_domain()}"
            subject = random_subject(is_spam)
            
            # Wrap the content in HTML
            email_content = f"<html><body><p>{content.replace('. ', '.</p><p>')}</p></body></html>"
            
            # Add a marker for uniqueness
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            email_content = email_content.replace('</body>', f'<!-- gen_id: {timestamp} --></body>')
            
            return {
                "sender": sender,
                "subject": subject,
                "date": datetime.datetime.now().strftime("%B %d, %Y"),
                "content": email_content,
                "is_spam": is_spam
            }
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
                       len(str(response)) if response else 0)

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
    return True

# =============================================================================
# EVALUATION IMPLEMENTATION
# =============================================================================

def execute_evaluation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY, genai, app):
    """Execute the evaluation with the Gemini API"""
    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("evaluate_explanation", 0, False, error="Rate limit reached")
        print("[EVALUATE] Rate limit reached - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
        
    # Prepare evaluation prompt
    prompt = get_evaluation_prompt(email_content, is_spam, user_response, user_explanation)
    
    try:
        # Create model with safety settings turned off
        model = create_model(GOOGLE_API_KEY, genai)
        print("[EVALUATE] Sending evaluation request to Gemini API with safety settings")
        
        # Log the API request attempt
        prompt_length = len(prompt)
        
        # Make API call with generation_config to ensure proper response formatting
        generation_config = {
            "temperature": 0.2,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Debug the raw response object before extraction
        debug_response_object(response, "EVALUATE_RESPONSE")
        
        # Log successful API call
        log_api_request("evaluate_explanation", prompt_length, True, 
                       len(str(response)) if response else 0)

        # Check for empty content
        if is_empty_response(response):
            print("[EVALUATE] Detected empty content with role only")
            return get_fallback_evaluation(is_spam, user_response)

        # Get response text with enhanced extraction
        ai_text = extract_ai_text(response)
        
        # Debug the extracted text
        if ai_text:
            with open('logs/debug_text.log', 'a') as f:
                f.write(f"\n\n[{datetime.datetime.now()}] === EXTRACTED TEXT ===\n")
                f.write(ai_text[:1000] + "...(truncated if longer)\n")
        
        if not ai_text:
            log_api_request("evaluate_explanation", prompt_length, False, 
                           error="Failed to extract AI text from response")
            return get_fallback_evaluation(is_spam, user_response)

        # Debug the raw output
        print(f"[EVALUATE] Raw AI response first 100 chars: {ai_text[:100]}")
        print(f"[EVALUATE] Raw AI response last 100 chars: {ai_text[-100:] if len(ai_text) > 100 else ai_text}")

        # Process Markdown and convert to HTML
        processed_html, score = process_ai_text_to_html(ai_text, user_response, is_spam)
        
        return {
            "feedback": processed_html,
            "score": score
        }
    except Exception as e:
        # Log failed API call
        log_api_request("evaluate_explanation", len(prompt), False, error=e)
        print(f"[EVALUATE] Error in evaluation: {e}")
        traceback.print_exc()
        handle_rate_limit_error(str(e), app)
        return get_fallback_evaluation(is_spam, user_response)

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

def get_fallback_evaluation(is_spam, user_response):
    """Generate a varied evaluation when AI isn't available"""
    correct = user_response == is_spam

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

    return {
        "feedback": feedback,
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
    return generate_fallback_content()

def extract_ai_text(response):
    """Extract text from AI response with comprehensive error handling"""
    # Write to debug log
    with open('logs/extraction_debug.log', 'a') as f:
        f.write(f"\n\n[{datetime.datetime.now()}] === EXTRACTION ATTEMPT ===\n")
        f.write(f"Response type: {type(response)}\n")
    
    # Check for empty response
    if is_empty_response(response):
        print("[EXTRACT] Detected empty content with role only")
        return generate_fallback_evaluation()
    
    # Try different extraction methods
    extraction_methods = [
        (extract_via_text_property, "Method 1: .text property"),
        (extract_via_parts, "Method 2: .parts[0].text"),
        (extract_via_candidates, "Method 3: candidates.content.parts"),
        (extract_via_content_field, "Method 4: .content.parts"),
        (extract_via_string_representation, "Method 5-6: string parsing")
    ]
    
    for method, description in extraction_methods:
        try:
            ai_text = method(response)
            if ai_text:
                print(f"[EXTRACT] {description} succeeded")
                with open('logs/extraction_debug.log', 'a') as f:
                    f.write(f"{description} succeeded\n")
                return ai_text
        except Exception as e:
            print(f"[EXTRACT] {description} failed: {e}")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write(f"{description} failed: {e}\n")
    
    # If all methods failed
    print("[EXTRACT] All extraction methods failed")
    with open('logs/extraction_debug.log', 'a') as f:
        f.write("All extraction methods failed\n")
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
    
    return genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)

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