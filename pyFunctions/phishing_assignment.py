import random
import datetime
import re
import markdown
import traceback
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Import API logging functions
try:
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"

def assign_phishing_creation(GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an assignment asking the user to create a phishing email"""
    
    # Default assignment if AI is not available
    default_assignment = {
        "instructions": """
        <h3 style='color: #2a3f54; margin-top: 20px;'>Final Assignment: Create a Phishing Email</h3>
        <p>Now that you've learned to identify phishing emails, it's time to demonstrate your understanding by creating one yourself.</p>
        
        <h4 style='color: #2a3f54; margin-top: 15px;'>Instructions:</h4>
        <ul>
            <li style='margin-bottom: 8px;'>Draft a convincing phishing email that includes at least 3 common phishing tactics.</li>
            <li style='margin-bottom: 8px;'>Include a fake URL or domain name.</li>
            <li style='margin-bottom: 8px;'>Create a sense of urgency or fear.</li>
            <li style='margin-bottom: 8px;'>Request sensitive information or credentials.</li>
        </ul>
        
        <p>Write your phishing email in the textbox below. The AI will evaluate how convincing and effective your phishing tactics are.</p>
        """,
        "rubric": [
            "Convincing pretext",
            "Use of social engineering tactics",
            "Quality of deceptive elements",
            "Technical accuracy of phishing techniques"
        ]
    }
    
    if not GOOGLE_API_KEY or not genai:
        log_api_request("assign_phishing_creation", 0, False, error="No API key or genai module")
        print("[ASSIGNMENT] No API key - using default assignment")
        return default_assignment
    
    # Use cached assignment - assignments don't need to be unique
    cache_key = "phishing_assignment"
    
    def generate_assignment():
        # Assignment generation prompt
        prompt = """
        Create instructions for a cybersecurity training assignment where the user needs to write their own phishing email. 
        
        The assignment should:
        1. Ask the user to create a realistic phishing email that demonstrates their understanding of phishing tactics
        2. Provide clear guidelines on what elements to include (urgency, fake URLs, requests for information, etc.)
        3. Explain that their creation will be evaluated by an AI
        4. Include 4-5 evaluation criteria that will be used to judge their phishing email
        
        Format your response in Markdown with:
        - A clear title
        - Instructions paragraph
        - Specific requirements as bullet points
        - Evaluation criteria as a separate section
        
        Keep it educational and ethical - emphasize this is for learning purposes only.
        """
        
        # Check rate limit before making API call
        if not check_rate_limit():
            log_api_request("assign_phishing_creation", len(prompt), False, error="Rate limit reached")
            print("[ASSIGNMENT] Rate limit reached - using default assignment")
            return default_assignment
        
        try:
            # Configure safety settings to bypass content filtering for educational purposes
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
            }
            
            model = genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)
            print("[ASSIGNMENT] Sending assignment generation request to Gemini API with safety settings")
            
            # Log the API request attempt
            prompt_length = len(prompt)
            
            response = model.generate_content(prompt)
            
            # Log successful API call
            log_api_request("assign_phishing_creation", prompt_length, True, 
                           len(str(response)) if response else 0)
            
            # Extract content
            ai_text = extract_ai_text(response)
            if not ai_text:
                log_api_request("assign_phishing_creation", prompt_length, False, 
                               error="Failed to extract AI text")
                print("[ASSIGNMENT] Failed to extract AI text - using default assignment")
                return default_assignment
            
            # Convert markdown to HTML
            formatted_html = convert_markdown_to_html(ai_text, "[ASSIGNMENT]")
            
            # Extract evaluation criteria/rubric
            rubric = extract_rubric(ai_text)
            
            return {
                "instructions": formatted_html,
                "rubric": rubric
            }
        
        except Exception as e:
            # Log failed API call
            log_api_request("assign_phishing_creation", len(prompt), False, error=e)
            print(f"[ASSIGNMENT] Error generating assignment: {e}")
            traceback.print_exc()
            handle_rate_limit_error(str(e), app)
            return default_assignment
    
    # Use cache to avoid regenerating assignment unnecessarily
    return get_cached_or_generate(cache_key, generate_assignment)

def evaluate_phishing_creation(user_phishing_email, GOOGLE_API_KEY=None, genai=None, app=None):
    """Evaluate a user-created phishing email"""
    
    # Default evaluation if AI is not available
    default_evaluation = {
        "feedback": """
        <h3 style='color: #2a3f54; margin-top: 20px;'>Evaluation of Your Phishing Email</h3>
        <p>Thank you for creating a phishing email as part of your training. Here's an assessment of your work:</p>
        
        <h4 style='color: #2a3f54; margin-top: 15px;'>Strengths:</h4>
        <ul>
            <li style='margin-bottom: 8px;'>You attempted to create a phishing scenario, which demonstrates engagement with the exercise.</li>
            <li style='margin-bottom: 8px;'>Your email shows an understanding of basic phishing concepts.</li>
        </ul>
        
        <h4 style='color: #2a3f54; margin-top: 15px;'>Areas for Improvement:</h4>
        <ul>
            <li style='margin-bottom: 8px;'>Consider adding more sophisticated social engineering tactics.</li>
            <li style='margin-bottom: 8px;'>Work on making your URLs and domains more convincingly deceptive.</li>
            <li style='margin-bottom: 8px;'>Focus on creating a stronger sense of urgency without making it too obvious.</li>
        </ul>
        
        <h4 style='color: #2a3f54; margin-top: 15px;'>Overall Assessment:</h4>
        <p>Your phishing email shows a basic understanding of phishing techniques. With more practice, you can create more sophisticated and convincing phishing scenarios, which will help you better identify them in real life.</p>
        
        <h4 style='color: #2a3f54; margin-top: 15px;'>Score: 7/10</h4>
        """,
        "score": 7,
        "effectiveness_rating": "Moderate"
    }
    
    if not GOOGLE_API_KEY or not genai or not user_phishing_email.strip():
        log_api_request("evaluate_phishing_creation", 0, False, 
                       error="No API key, genai module, or empty submission")
        print("[PHISHING_EVAL] No API key or empty submission - using default evaluation")
        return default_evaluation
    
    # Check for rate limiting
    if should_use_fallback(app):
        log_api_request("evaluate_phishing_creation", 0, False, error="Rate limit fallback")
        print("[PHISHING_EVAL] Using fallback due to rate limit")
        return default_evaluation
    
    # Create a cache key based on the user's submission
    cache_key = create_cache_key("phishing_eval", user_phishing_email[:1000])  # Use first 1000 chars
    
    def perform_evaluation():
        # Evaluation prompt
        prompt = f"""
        You are a cybersecurity expert evaluating a phishing email created by a student as part of their training.
        
        Student-created phishing email:
        ```
        {user_phishing_email}
        ```
        
        Provide a detailed evaluation of this phishing email creation. Your evaluation should cover:
        
        1. Effectiveness: How convincing would this phishing attempt be to an average user?
        2. Techniques: What phishing techniques did the student incorporate successfully?
        3. Weaknesses: What aspects would make this phishing attempt less effective or more easily detectable?
        4. Improvements: What specific changes would make this phishing attempt more convincing?
        5. Overall Rating: Score the phishing attempt on a scale of 1-10, where 10 is extremely convincing.
        
        Also include an "Effectiveness Rating" that is exactly one of these categories: Low, Moderate, High, Very High
        
        Format your response as Markdown with clear headings and bullet points for each section.
        Make sure your feedback is constructive and educational, as this is for learning purposes only.
        """
        
        # Check rate limit before API call
        if not check_rate_limit():
            log_api_request("evaluate_phishing_creation", len(prompt), False, error="Rate limit reached")
            print("[PHISHING_EVAL] Rate limit reached - using default evaluation")
            return default_evaluation
        
        try:
            # Configure safety settings to bypass content filtering for educational purposes
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
            }
            
            model = genai.GenerativeModel('gemini-2.5-pro', safety_settings=safety_settings)
            print("[PHISHING_EVAL] Sending evaluation request to Gemini API with safety settings")
            
            # Log the API request attempt
            prompt_length = len(prompt)
            
            response = model.generate_content(prompt)
            
            # Log successful API call
            log_api_request("evaluate_phishing_creation", prompt_length, True, 
                           len(str(response)) if response else 0)
            
            # Extract content
            ai_text = extract_ai_text(response)
            if not ai_text:
                log_api_request("evaluate_phishing_creation", prompt_length, False, 
                               error="Failed to extract AI text")
                print("[PHISHING_EVAL] Failed to extract AI text - using default evaluation")
                return default_evaluation
            
            # Convert markdown to HTML
            formatted_html = convert_markdown_to_html(ai_text, "[PHISHING_EVAL]")
            
            # Apply styling
            formatted_html = apply_html_styling(formatted_html)
            
            # Extract score and effectiveness rating
            score = extract_score(ai_text)
            effectiveness_rating = extract_effectiveness_rating(ai_text)
            
            return {
                "feedback": formatted_html,
                "score": score,
                "effectiveness_rating": effectiveness_rating
            }
        
        except Exception as e:
            # Log failed API call
            log_api_request("evaluate_phishing_creation", len(prompt), False, error=e)
            print(f"[PHISHING_EVAL] Error in evaluation: {e}")
            traceback.print_exc()
            handle_rate_limit_error(str(e), app)
            return default_evaluation
    
    # Use cache to avoid reevaluating identical submissions
    return get_cached_or_generate(cache_key, perform_evaluation)

# Helper functions

def extract_ai_text(response):
    """Extract text from AI response with robust error handling"""
    ai_text = None
    try:
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
        
        print(f"[AI_TEXT] Successfully extracted text, length: {len(ai_text)}")
        return ai_text
    except Exception as text_error:
        print(f"[AI_TEXT] Error extracting text: {text_error}")
        return None

def convert_markdown_to_html(markdown_text, log_prefix=""):
    """Convert markdown to HTML with error handling"""
    try:
        # Use proper markdown conversion
        formatted_html = markdown.markdown(markdown_text, extensions=['extra'])
        print(f"{log_prefix} Successfully converted markdown to HTML")
        return formatted_html
    except Exception as md_error:
        print(f"{log_prefix} Error in markdown conversion: {md_error}")
        return fallback_markdown_conversion(markdown_text)

def fallback_markdown_conversion(text):
    """Basic fallback for markdown conversion if the library fails"""
    html = text.replace('# ', '<h3>').replace('\n\n', '</p><p>')
    html = re.sub(r'\n- ', '</p><ul><li>', html)
    html = re.sub(r'\n\d+\. ', '</p><ol><li>', html)
    html = html.replace('\n', '<br>')
    
    # Close any open tags
    if '<ul><li>' in html and '</li></ul>' not in html:
        html += '</li></ul>'
    if '<ol><li>' in html and '</li></ol>' not in html:
        html += '</li></ol>'
    if html.startswith('<p>') and not html.endswith('</p>'):
        html += '</p>'
        
    return f"<div>{html}</div>"

def apply_html_styling(html):
    """Apply consistent styling to HTML elements"""
    styled = html
    
    # Style headings
    styled = styled.replace("<h1>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
    styled = styled.replace("</h1>", "</h3>")
    styled = styled.replace("<h2>", "<h4 style='color: #2a3f54; margin-top: 15px;'>")
    styled = styled.replace("</h2>", "</h4>")
    
    # Style list items
    styled = styled.replace("<li>", "<li style='margin-bottom: 8px;'>")
    
    # Style strong elements
    styled = styled.replace("<strong>", "<strong style='color: #2a3f54;'>")
    
    return styled

def extract_rubric(ai_text):
    """Extract evaluation criteria/rubric from AI text"""
    default_rubric = [
        "Convincing pretext",
        "Use of social engineering tactics",
        "Quality of deceptive elements",
        "Technical accuracy of phishing techniques"
    ]
    
    try:
        # Look for sections with evaluation criteria
        criteria_section = re.search(
            r"(?:evaluation criteria|rubric|grading criteria|you will be evaluated on)(.+?)(?:\n\n|$)", 
            ai_text.lower(), re.DOTALL
        )
        
        if criteria_section:
            criteria_text = criteria_section.group(1)
            
            # Extract bullet points
            criteria_items = re.findall(r"[-*]\s*([^\n]+)", criteria_text)
            if criteria_items:
                return criteria_items
                
            # Try numbered lists
            criteria_items = re.findall(r"\d+\.\s*([^\n]+)", criteria_text)
            if criteria_items:
                return criteria_items
    except Exception as rubric_error:
        print(f"[EXTRACT] Error extracting rubric: {rubric_error}")
    
    # Return default if extraction fails
    return default_rubric

def extract_score(ai_text):
    """Extract score from AI text"""
    default_score = 7
    
    try:
        # Try to find score in the text
        score_match = re.search(r"(?:score|rating)[^0-9]*([1-9]|10)(?:/10)?", ai_text, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
            return score
    except Exception as score_error:
        print(f"[EXTRACT] Error extracting score: {score_error}")
    
    return default_score

def extract_effectiveness_rating(ai_text):
    """Extract effectiveness rating from AI text"""
    default_rating = "Moderate"
    
    try:
        # Look for effectiveness rating
        rating_match = re.search(r"effectiveness rating\s*:\s*(low|moderate|high|very high)", ai_text, re.IGNORECASE)
        if rating_match:
            rating = rating_match.group(1).title()
            return rating
    except Exception as rating_error:
        print(f"[EXTRACT] Error extracting effectiveness rating: {rating_error}")
    
    return default_rating

def should_use_fallback(app):
    """Check if we should use fallback due to rate limiting"""
    rate_limited = app.config.get('RATE_LIMITED', False) if app else False
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0) if app else 0
    current_time = datetime.datetime.now().timestamp()
    
    if rate_limited and (current_time - rate_limit_time < 600):  # 10 minutes
        print(f"[RATE_LIMIT] Using fallback ({int(current_time - rate_limit_time)} seconds since limit)")
        return True
    return False

def handle_rate_limit_error(error_str, app):
    """Handle rate limit errors by setting appropriate flags"""
    if any(term in error_str.lower() for term in ["429", "quota", "rate limit"]):
        if app:
            app.config['RATE_LIMITED'] = True
            app.config['RATE_LIMIT_TIME'] = datetime.datetime.now().timestamp()
        print(f"[RATE_LIMIT] API rate limit detected: {error_str}")