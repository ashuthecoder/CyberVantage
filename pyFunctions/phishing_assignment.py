import random
import datetime
import re
import markdown
import traceback

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
        print("[ASSIGNMENT] No API key - using default assignment")
        return default_assignment
    
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
    
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        print("[ASSIGNMENT] Sending assignment generation request to Gemini API")
        response = model.generate_content(prompt)
        
        # Extract content
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
            
            print(f"[ASSIGNMENT] Successfully got assignment text, length: {len(ai_text)}")
        except Exception as text_error:
            print(f"[ASSIGNMENT] Error extracting text: {text_error}")
            return default_assignment
        
        # Convert markdown to HTML
        try:
            formatted_html = markdown.markdown(ai_text, extensions=['extra'])
            print("[ASSIGNMENT] Successfully converted markdown to HTML")
        except Exception as md_error:
            print(f"[ASSIGNMENT] Error in markdown conversion: {md_error}")
            formatted_html = f"<div>{ai_text.replace('# ', '<h3>').replace('\n\n', '</p><p>').replace('\n- ', '</p><ul><li>').replace('\n', '<br>')}</div>"
        
        # Extract evaluation criteria/rubric
        rubric = []
        try:
            # Look for sections with evaluation criteria
            criteria_section = re.search(r"(?:evaluation criteria|rubric|grading criteria|you will be evaluated on)(.+?)(?:\n\n|$)", 
                                        ai_text.lower(), re.DOTALL)
            if criteria_section:
                criteria_text = criteria_section.group(1)
                # Extract bullet points
                criteria_items = re.findall(r"[-*]\s*([^\n]+)", criteria_text)
                if criteria_items:
                    rubric = criteria_items
                else:
                    # Try numbered lists
                    criteria_items = re.findall(r"\d+\.\s*([^\n]+)", criteria_text)
                    if criteria_items:
                        rubric = criteria_items
        except Exception as rubric_error:
            print(f"[ASSIGNMENT] Error extracting rubric: {rubric_error}")
        
        # If we couldn't extract a rubric, use default
        if not rubric:
            rubric = [
                "Convincing pretext",
                "Use of social engineering tactics",
                "Quality of deceptive elements",
                "Technical accuracy of phishing techniques"
            ]
        
        return {
            "instructions": formatted_html,
            "rubric": rubric
        }
    
    except Exception as e:
        print(f"[ASSIGNMENT] Error generating assignment: {e}")
        traceback.print_exc()
        return default_assignment

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
        print("[PHISHING_EVAL] No API key or empty submission - using default evaluation")
        return default_evaluation
    
    # Check for rate limiting
    rate_limited = app.config.get('RATE_LIMITED', False) if app else False
    rate_limit_time = app.config.get('RATE_LIMIT_TIME', 0) if app else 0
    current_time = datetime.datetime.now().timestamp()
    
    if rate_limited and (current_time - rate_limit_time < 600):
        print(f"[PHISHING_EVAL] Using fallback due to rate limit ({int(current_time - rate_limit_time)} seconds ago)")
        return default_evaluation
    
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
    
    try:
        model = genai.GenerativeModel('gemini-2.5-pro')
        print("[PHISHING_EVAL] Sending evaluation request to Gemini API")
        response = model.generate_content(prompt)
        
        # Extract content
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
            
            print(f"[PHISHING_EVAL] Successfully got evaluation text, length: {len(ai_text)}")
        except Exception as text_error:
            print(f"[PHISHING_EVAL] Error extracting text: {text_error}")
            return default_evaluation
        
        # Convert markdown to HTML
        try:
            # Use proper markdown conversion
            formatted_html = markdown.markdown(ai_text, extensions=['extra'])
            print("[PHISHING_EVAL] Successfully converted markdown to HTML")
        except Exception as md_error:
            print(f"[PHISHING_EVAL] Error in markdown conversion: {md_error}")
            formatted_html = f"<div>{ai_text.replace('# ', '<h3>').replace('\n\n', '</p><p>').replace('\n- ', '</p><ul><li>').replace('\n', '<br>')}</div>"
        
        # Apply styling
        formatted_html = formatted_html.replace("<h1>", "<h3 style='color: #2a3f54; margin-top: 20px;'>")
        formatted_html = formatted_html.replace("</h1>", "</h3>")
        formatted_html = formatted_html.replace("<h2>", "<h4 style='color: #2a3f54; margin-top: 15px;'>")
        formatted_html = formatted_html.replace("</h2>", "</h4>")
        formatted_html = formatted_html.replace("<li>", "<li style='margin-bottom: 8px;'>")
        formatted_html = formatted_html.replace("<strong>", "<strong style='color: #2a3f54;'>")
        
        # Extract score
        score = 7  # Default score
        try:
            # Try to find score in the text
            score_match = re.search(r"(?:score|rating)[^0-9]*([1-9]|10)(?:/10)?", ai_text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
        except Exception as score_error:
            print(f"[PHISHING_EVAL] Error extracting score: {score_error}")
        
        # Extract effectiveness rating
        effectiveness_rating = "Moderate"  # Default rating
        try:
            # Look for effectiveness rating
            rating_match = re.search(r"effectiveness rating\s*:\s*(low|moderate|high|very high)", ai_text, re.IGNORECASE)
            if rating_match:
                effectiveness_rating = rating_match.group(1).title()
        except Exception as rating_error:
            print(f"[PHISHING_EVAL] Error extracting effectiveness rating: {rating_error}")
        
        return {
            "feedback": formatted_html,
            "score": score,
            "effectiveness_rating": effectiveness_rating
        }
    
    except Exception as e:
        print(f"[PHISHING_EVAL] Error in evaluation: {e}")
        traceback.print_exc()
        
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
            if app:
                app.config['RATE_LIMITED'] = True
                app.config['RATE_LIMIT_TIME'] = current_time
            print(f"[PHISHING_EVAL] Rate limit detected: {error_str}")
        
        return default_evaluation