import random
import traceback
import datetime
import re
import markdown
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import API logging functions with fallback
try:
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"

def generate_ai_email(user_name, previous_responses, GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an AI email with robust error handling"""
    print(f"[GENERATE] Starting email generation for user: {user_name}")
    from .template_emails import get_template_email

    if not GOOGLE_API_KEY or not genai:
        log_api_request("generate_ai_email", 0, False, error="No API key or genai module")
        print("[GENERATE] No API key or genai module - using template email")
        return get_template_email()

    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("generate_ai_email", 0, False, error="Rate limit reached")
        print("[GENERATE] Rate limit reached - using template email")
        return get_template_email()

    # Strict generation prompt with a fixed schema the parser expects
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

    try:
        # Configure safety settings to bypass content filtering for educational purposes
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
        
        model = genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)
        print("[GENERATE] Sending request to Gemini API with safety settings")
        
        # Log the API request attempt
        prompt_length = len(prompt)
        
        response = model.generate_content(prompt)
        
        # Log successful API call
        log_api_request("generate_ai_email", prompt_length, True, 
                       len(str(response)) if response else 0)

        # Extract content from response
        content = extract_content_from_response(response)
        
        if not content:
            log_api_request("generate_ai_email", prompt_length, False, 
                           error="Failed to extract content from response")
            print("[GENERATE] Failed to extract content from response")
            return get_template_email()

        print(f"[GENERATE] Response content length: {len(content)}")
        print(f"[GENERATE] First 100 chars: {content[:100]}")

        # Parse email components
        try:
            email_data = parse_email_components(content)
            if not email_data:
                print("[GENERATE] Could not parse email components")
                return get_template_email()
                
            return email_data
            
        except Exception as parse_error:
            log_api_request("generate_ai_email", prompt_length, False, 
                           error=f"Error parsing response: {parse_error}")
            print(f"[GENERATE] Error parsing response: {parse_error}")
            traceback.print_exc()
            return get_template_email()
    except Exception as e:
        # Log failed API call
        log_api_request("generate_ai_email", len(prompt), False, error=e)
        print(f"[GENERATE] Error in AI email generation: {e}")
        traceback.print_exc()

        # Rate limit tracking
        handle_rate_limit_error(str(e), app)

        return get_template_email()

def extract_content_from_response(response):
    """Extract text content from various response formats"""
    content = None
    
    if hasattr(response, 'text'):
        content = response.text
        print("[GENERATE] Successfully extracted text via .text property")
    elif hasattr(response, 'parts') and response.parts:
        content = response.parts[0].text
        print("[GENERATE] Successfully extracted text via .parts[0].text")
    elif hasattr(response, 'candidates') and response.candidates:
        cand = response.candidates[0]
        if hasattr(cand, 'content') and hasattr(cand.content, 'parts'):
            content = cand.content.parts[0].text
            print("[GENERATE] Successfully extracted text via candidates structure")

    if not content:
        content = str(response)
        print("[GENERATE] Using string representation as fallback")
        
    return content

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

def handle_rate_limit_error(error_str, app):
    """Handle rate limit errors and update app config"""
    if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
        if app:
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = datetime.datetime.now().timestamp()
        print(f"[GENERATE] API rate limit detected: {error_str}")

def execute_evaluation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY, genai, app):
    """Execute the evaluation with the Gemini API"""
    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("evaluate_explanation", 0, False, error="Rate limit reached")
        print("[EVALUATE] Rate limit reached - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
        
    # Rigorous evaluation prompt
    prompt = get_evaluation_prompt(email_content, is_spam, user_response, user_explanation)
    
    try:
        # Create a fresh model instance each time
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
        
        # Force new model creation each time to avoid stale state
        genai.configure(api_key=GOOGLE_API_KEY)  # Reconfigure to ensure fresh state
        model = genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)
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
    
def execute_evaluation(email_content, is_spam, user_response, user_explanation, GOOGLE_API_KEY, genai, app):
    """Execute the evaluation with the Gemini API"""
    # Check rate limit before API call
    if not check_rate_limit():
        log_api_request("evaluate_explanation", 0, False, error="Rate limit reached")
        print("[EVALUATE] Rate limit reached - using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
        
    # Rigorous evaluation prompt
    prompt = get_evaluation_prompt(email_content, is_spam, user_response, user_explanation)
    
    try:
        # Configure safety settings to bypass content filtering for educational purposes
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
        }
        
        model = genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)
        print("[EVALUATE] Sending evaluation request to Gemini API with safety settings")
        
        # Log the API request attempt
        prompt_length = len(prompt)
        
        response = model.generate_content(prompt)
        
        # Log successful API call
        log_api_request("evaluate_explanation", prompt_length, True, 
                       len(str(response)) if response else 0)

        # Get response text
        ai_text = extract_ai_text(response)
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

def should_use_fallback(app):
    """Determine if fallback should be used based on rate limiting"""
    rate_limited = app.config.get('RATE_LIMITED', False) if app else False
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0) if app else 0
    current_time = datetime.datetime.now().timestamp()
    
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"[EVALUATE] Using fallback due to rate limit ({int(current_time - rate_limit_time)} seconds ago)")
        return True
    return False

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

def extract_ai_text(response):
    """Extract text from AI response with comprehensive error handling"""
    import json
    
    # Write to debug log
    with open('logs/extraction_debug.log', 'a') as f:
        f.write(f"\n\n[{datetime.datetime.now()}] === EXTRACTION ATTEMPT ===\n")
        f.write(f"Response type: {type(response)}\n")
    
    ai_text = None
    
    # Method 1: Direct text property
    try:
        if hasattr(response, 'text'):
            ai_text = response.text
            print("[EXTRACT] Method 1: Got text via .text property")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write("Method 1 succeeded: .text property\n")
            return ai_text
    except Exception as e:
        print(f"[EXTRACT] Method 1 failed: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Method 1 failed: {e}\n")
    
    # Method 2: Parts structure
    try:
        if hasattr(response, 'parts') and response.parts:
            ai_text = response.parts[0].text
            print("[EXTRACT] Method 2: Got text via .parts[0].text")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write("Method 2 succeeded: .parts[0].text\n")
            return ai_text
    except Exception as e:
        print(f"[EXTRACT] Method 2 failed: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Method 2 failed: {e}\n")
    
    # Method 3: Candidates structure
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                ai_text = candidate.content.parts[0].text
                print("[EXTRACT] Method 3: Got text via candidates.content.parts")
                with open('logs/extraction_debug.log', 'a') as f:
                    f.write("Method 3 succeeded: candidates.content.parts\n")
                return ai_text
    except Exception as e:
        print(f"[EXTRACT] Method 3 failed: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Method 3 failed: {e}\n")
    
    # Method 4: Content property
    try:
        if hasattr(response, 'content'):
            if hasattr(response.content, 'parts') and response.content.parts:
                ai_text = response.content.parts[0].text
                print("[EXTRACT] Method 4: Got text via .content.parts")
                with open('logs/extraction_debug.log', 'a') as f:
                    f.write("Method 4 succeeded: .content.parts\n")
                return ai_text
            
            # Try content as string
            try:
                ai_text = str(response.content)
                print("[EXTRACT] Method 4b: Got text via str(content)")
                with open('logs/extraction_debug.log', 'a') as f:
                    f.write("Method 4b succeeded: str(content)\n")
                return ai_text
            except:
                pass
    except Exception as e:
        print(f"[EXTRACT] Method 4 failed: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Method 4 failed: {e}\n")
    
    # Method 5: Try string representation and JSON parsing
    try:
        raw_string = str(response)
        
        # Log the raw string for debugging
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Raw string: {raw_string[:500]}...(truncated)\n")
        
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
                        ai_text = str(data[field])
                        print(f"[EXTRACT] Method 5: Got text from JSON field '{field}'")
                        with open('logs/extraction_debug.log', 'a') as f:
                            f.write(f"Method 5 succeeded: JSON field '{field}'\n")
                        return ai_text
            except:
                pass
        
        # Last resort: just use the string itself
        if len(raw_string) > 30:  # Arbitrary minimum length
            ai_text = raw_string
            print("[EXTRACT] Method 6: Using full string representation")
            with open('logs/extraction_debug.log', 'a') as f:
                f.write("Method 6 succeeded: full string representation\n")
            return ai_text
    except Exception as e:
        print(f"[EXTRACT] Method 5-6 failed: {e}")
        with open('logs/extraction_debug.log', 'a') as f:
            f.write(f"Method 5-6 failed: {e}\n")
    
    # If we got here, all methods failed
    print("[EXTRACT] All extraction methods failed")
    with open('logs/extraction_debug.log', 'a') as f:
        f.write("All extraction methods failed\n")
    return None

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

def debug_response_object(response, label="DEBUG"):
    """Exhaustively debug a response object's structure and content"""
    import inspect
    import json
    
    # Create a log file for deep debugging
    with open('logs/debug_response.log', 'a') as f:
        f.write(f"\n\n[{datetime.datetime.now()}] === {label} ===\n")
        
        # Log the type
        f.write(f"Response type: {type(response)}\n")
        
        # Try to log the raw response
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
        
        # If it has a dictionary-like structure, try to serialize to JSON
        try:
            if hasattr(response, '__dict__'):
                f.write("JSON representation attempt:\n")
                json_data = json.dumps(response.__dict__, default=str, indent=2)
                f.write(f"{json_data[:2000]}...(truncated if longer)\n")
        except:
            f.write("Could not JSON serialize\n")

def get_fallback_evaluation(is_spam, user_response):
    """Generate a varied evaluation when AI isn't available"""
    correct = user_response == is_spam

    if correct:
        base_score = random.randint(7, 9)
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
        base_score = random.randint(2, 4)
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