import random
import datetime
import re
import markdown
import traceback
from pyFunctions.api_logging import log_api_request

# Import Azure OpenAI helper functions with fallback
try:
    from .azure_openai_helper import (
        call_azure_openai_with_retry, extract_text_from_response
    )
    AZURE_HELPERS_AVAILABLE = True
except ImportError:
    AZURE_HELPERS_AVAILABLE = False
    def call_azure_openai_with_retry(*args, **kwargs): 
        return None, "IMPORT_ERROR"
    def extract_text_from_response(*args, **kwargs): 
        return ""

def assign_phishing_creation(api_key, genai, app):
    """
    Generate a phishing email creation assignment.
    Renamed from 'final assignment' to 'craft phishing email'
    """
    try:
        # Return structured assignment data
        assignment_data = {
            "instructions": """
                <h3>Create a Phishing Email</h3>
                <p>Your final challenge is to create a convincing phishing email that demonstrates your understanding of social engineering tactics. This exercise will help you understand how attackers think and craft malicious messages.</p>
                
                <h4>Your Task:</h4>
                <p>Create a phishing email that targets an employee at a fictional company called "TechCorp Solutions". Your email should aim to steal login credentials by directing the target to a fake login page.</p>
                
                <h4>Required Elements:</h4>
                <ul>
                    <li><strong>Compelling Subject Line:</strong> Create urgency or curiosity</li>
                    <li><strong>Sender Identity:</strong> Choose a believable sender (IT support, HR, management, etc.)</li>
                    <li><strong>Social Engineering Hook:</strong> Use urgency, fear, authority, or curiosity</li>
                    <li><strong>Call to Action:</strong> Include a fake link or instruction</li>
                    <li><strong>Professional Appearance:</strong> Make it look legitimate</li>
                </ul>
                
                <h4>Example Scenarios to Consider:</h4>
                <ul>
                    <li>IT security update requiring password verification</li>
                    <li>HR announcement about benefits that requires login</li>
                    <li>Executive request for urgent information</li>
                    <li>Security alert about suspicious account activity</li>
                </ul>
                
                <p><strong>Remember:</strong> This is for educational purposes only. Never use these techniques for malicious purposes.</p>
            """,
            "rubric": [
                "Social Engineering Tactics (30%): Effective use of urgency, fear, authority, or curiosity",
                "Technical Realism (25%): Believable sender, subject line, and technical details",
                "Psychological Appeal (25%): Persuasive language and emotional triggers",
                "Professional Appearance (20%): Formatting, grammar, and overall believability"
            ]
        }
        
        return assignment_data
        
    except Exception as e:
        print(f"[PHISHING_ASSIGNMENT] Error generating assignment: {e}")
        traceback.print_exc()
        
        # Return fallback assignment
        return {
            "instructions": """
                <h3>Create a Phishing Email</h3>
                <p>Create a phishing email that demonstrates your understanding of social engineering tactics. Your email should target a fictional company employee and aim to steal login credentials.</p>
                
                <h4>Include these elements:</h4>
                <ul>
                    <li>Compelling subject line</li>
                    <li>Believable sender identity</li>
                    <li>Social engineering hook (urgency, fear, authority, or curiosity)</li>
                    <li>Call to action with fake link</li>
                    <li>Professional appearance</li>
                </ul>
                
                <p><strong>Note:</strong> This is for educational purposes only.</p>
            """,
            "rubric": [
                "Social Engineering Tactics (30%)",
                "Technical Realism (25%)",
                "Psychological Appeal (25%)",
                "Professional Appearance (20%)"
            ]
        }

def evaluate_phishing_creation(phishing_email, api_key, genai, app):
    """
    Evaluate user-created phishing email and provide detailed scoring and feedback
    """
    try:
        # Try Azure OpenAI first if available
        if AZURE_HELPERS_AVAILABLE and app and app.config.get('AZURE_OPENAI_KEY'):
            print("[PHISHING_EVAL] Attempting Azure OpenAI evaluation")
            result = evaluate_phishing_creation_azure(phishing_email, app)
            if result:
                return result
        
        # Try Gemini if API key is available
        if api_key and genai:
            print("[PHISHING_EVAL] Attempting Gemini evaluation")
            return evaluate_phishing_creation_gemini(phishing_email, api_key, genai, app)
        
        # Use enhanced fallback evaluation
        print("[PHISHING_EVAL] Using enhanced fallback evaluation")
        return get_enhanced_fallback_evaluation(phishing_email)
        
    except Exception as e:
        error_message = f"Error evaluating phishing creation: {str(e)}"
        print(f"[PHISHING_EVAL] {error_message}")
        traceback.print_exc()
        
        return {
            "feedback": "<p>We couldn't evaluate your phishing email at this time. Please try again later.</p>",
            "score": 0,
            "effectiveness_rating": "Not Rated"
        }

def evaluate_phishing_creation_azure(phishing_email, app):
    """
    Evaluate phishing email using Azure OpenAI
    """
    try:
        # Enhanced evaluation prompt for better scoring
        prompt = f"""You are a cybersecurity expert evaluating a phishing email created by a student for educational purposes.

Student-created phishing email:
{phishing_email}

Evaluate this phishing email on these criteria and provide scores for each:

1. **Social Engineering Tactics (30 points)**:
   - Use of urgency, fear, curiosity, or authority
   - Emotional triggers and psychological pressure
   
2. **Technical Realism (30 points)**:
   - Believable sender address/domain
   - Professional formatting and layout
   - Realistic links or attachments mentioned
   
3. **Psychological Manipulation (20 points)**:
   - Persuasive language and tone
   - Exploitation of trust or authority
   - Use of social proof or scarcity
   
4. **Scenario Believability (20 points)**:
   - Realistic context and timing
   - Appropriate target audience
   - Credible reason for action

For each criterion, assign a specific score and explain your reasoning.

Then provide:
- Overall score (out of 100)
- Effectiveness rating (Low/Medium/High/Very High)
- Specific strengths in the approach
- Areas for improvement
- Actionable recommendations

Format your response as HTML with clear headings and organized content. Be constructive and educational in your feedback."""

        # Call Azure OpenAI
        response, status = call_azure_openai_with_retry(
            messages=[{"role": "user", "content": prompt}],
            app=app,
            max_tokens=1024,
            temperature=0.3
        )
        
        if response and status == "SUCCESS":
            feedback_html = extract_text_from_response(response)
            if feedback_html:
                # Extract score and effectiveness rating
                score, effectiveness_rating = parse_evaluation_response(feedback_html)
                
                return {
                    "feedback": feedback_html,
                    "score": score,
                    "effectiveness_rating": effectiveness_rating
                }
        
        return None
        
    except Exception as e:
        print(f"[PHISHING_EVAL] Azure evaluation error: {e}")
        return None

def evaluate_phishing_creation_gemini(phishing_email, api_key, genai, app):
    """
    Evaluate phishing email using Gemini (original implementation with enhanced prompt)
    """
    try:
        # Configure safety settings
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Enhanced evaluation prompt
        prompt = f"""You are a cybersecurity expert evaluating a phishing email created by a student for educational purposes.

Student-created phishing email:
```
{phishing_email}
```

Evaluate this phishing email on these criteria and provide scores for each:

1. **Social Engineering Tactics (30 points)**:
   - Use of urgency, fear, curiosity, or authority
   - Emotional triggers and psychological pressure
   
2. **Technical Realism (30 points)**:
   - Believable sender address/domain
   - Professional formatting and layout
   - Realistic links or attachments mentioned
   
3. **Psychological Manipulation (20 points)**:
   - Persuasive language and tone
   - Exploitation of trust or authority
   - Use of social proof or scarcity
   
4. **Scenario Believability (20 points)**:
   - Realistic context and timing
   - Appropriate target audience
   - Credible reason for action

For each criterion, assign a specific score and explain your reasoning.

Then provide:
- Overall score (out of 100)
- Effectiveness rating (Low/Medium/High/Very High)
- Specific strengths in the approach
- Areas for improvement
- Actionable recommendations

Format your response as HTML with clear headings and organized content. Be constructive and educational in your feedback."""
        
        model = genai.GenerativeModel('gemini-1.5-pro', 
                                     safety_settings=safety_settings)
        
        function_name = "evaluate_phishing_creation"
        start_time = datetime.datetime.now()
        
        response = model.generate_content(prompt)
        
        # Log API request
        log_api_request(
            function_name=function_name,
            model="gemini-1.5-pro",
            prompt_length=len(prompt),
            response_length=len(response.text) if hasattr(response, 'text') else 0,
            start_time=start_time,
            end_time=datetime.datetime.now(),
            success=True,
            error_message=None
        )
        
        # Extract score and effectiveness
        feedback_html = response.text
        score, effectiveness_rating = parse_evaluation_response(feedback_html)
        
        return {
            "feedback": feedback_html,
            "score": score,
            "effectiveness_rating": effectiveness_rating
        }
        
    except Exception as e:
        error_message = f"Error evaluating phishing creation: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="evaluate_phishing_creation",
            model="gemini-1.5-pro",
            prompt_length=len(prompt) if 'prompt' in locals() else 0,
            response_length=0,
            start_time=start_time if 'start_time' in locals() else datetime.datetime.now(),
            end_time=datetime.datetime.now(),
            success=False,
            error_message=error_message
        )
        
        return None

def parse_evaluation_response(feedback_html):
    """
    Parse evaluation response to extract score and effectiveness rating
    """
    score = 70  # Default score
    effectiveness_rating = "Medium"
    
    # Extract score using improved heuristics
    if "overall score" in feedback_html.lower():
        try:
            score_text = feedback_html.lower().split("overall score")[1].split(".")[0]
            possible_scores = [int(s) for s in score_text.split() if s.isdigit()]
            if possible_scores:
                score = min(100, max(0, possible_scores[0]))  # Clamp between 0-100
        except:
            pass
    
    # Look for score patterns like "Score: 85" or "85/100"
    score_patterns = [
        r'score[:\s]+(\d+)',
        r'(\d+)/100',
        r'(\d+)\s*out\s*of\s*100',
        r'(\d+)\s*points?'
    ]
    
    for pattern in score_patterns:
        matches = re.findall(pattern, feedback_html, re.IGNORECASE)
        if matches:
            try:
                potential_score = int(matches[0])
                if 0 <= potential_score <= 100:
                    score = potential_score
                    break
            except:
                continue
    
    # Extract effectiveness rating
    if "effectiveness rating" in feedback_html.lower():
        if "very high" in feedback_html.lower():
            effectiveness_rating = "Very High"
        elif "high" in feedback_html.lower():
            effectiveness_rating = "High"
        elif "medium" in feedback_html.lower():
            effectiveness_rating = "Medium"
        elif "low" in feedback_html.lower():
            effectiveness_rating = "Low"
    
    return score, effectiveness_rating

def get_enhanced_fallback_evaluation(phishing_email):
    """
    Provide enhanced fallback evaluation when AI is not available
    """
    # Analyze email content for basic scoring factors
    email_lower = phishing_email.lower()
    
    # Base score
    score = 40
    
    # Check for various phishing techniques
    techniques_found = []
    
    # Urgency indicators
    urgency_words = ['urgent', 'immediate', 'asap', 'expires', 'deadline', 'limited time', 'act now', 'hurry']
    if any(word in email_lower for word in urgency_words):
        score += 15
        techniques_found.append("urgency")
    
    # Authority indicators
    authority_words = ['security', 'admin', 'it department', 'management', 'ceo', 'hr', 'support team']
    if any(word in email_lower for word in authority_words):
        score += 12
        techniques_found.append("authority")
    
    # Fear tactics
    fear_words = ['suspended', 'compromised', 'hack', 'breach', 'virus', 'unauthorized', 'locked', 'terminated']
    if any(word in email_lower for word in fear_words):
        score += 10
        techniques_found.append("fear")
    
    # Links/actions
    action_words = ['click', 'verify', 'confirm', 'update', 'login', 'download', 'open attachment']
    if any(word in email_lower for word in action_words):
        score += 8
        techniques_found.append("call-to-action")
    
    # Professional appearance (length and structure)
    if len(phishing_email) > 200:
        score += 5
    
    if '@' in phishing_email:  # Has email addresses
        score += 3
    
    if 'http' in phishing_email or 'www' in phishing_email:  # Has links
        score += 5
    
    # Determine effectiveness rating based on score
    if score >= 80:
        effectiveness_rating = "Very High"
    elif score >= 65:
        effectiveness_rating = "High"
    elif score >= 45:
        effectiveness_rating = "Medium"
    else:
        effectiveness_rating = "Low"
    
    # Generate detailed feedback
    feedback = f"""
    <h3>Phishing Email Analysis Results</h3>
    <p><strong>Note:</strong> This evaluation is performed using automated analysis since AI evaluation is not currently available.</p>
    
    <h3>Overall Assessment</h3>
    <p>Your phishing email shows {"good understanding" if score >= 60 else "basic understanding"} of social engineering techniques.</p>
    
    <h3>Techniques Identified</h3>
    <ul>
    """
    
    if techniques_found:
        for technique in techniques_found:
            if technique == "urgency":
                feedback += "<li><strong>Urgency:</strong> ✓ Creates time pressure to prompt quick action</li>"
            elif technique == "authority":
                feedback += "<li><strong>Authority:</strong> ✓ Uses authoritative sources to build trust</li>"
            elif technique == "fear":
                feedback += "<li><strong>Fear:</strong> ✓ Creates anxiety about potential consequences</li>"
            elif technique == "call-to-action":
                feedback += "<li><strong>Action Request:</strong> ✓ Includes clear instructions for victim</li>"
    else:
        feedback += "<li>No clear social engineering techniques identified</li>"
    
    feedback += """
    </ul>
    
    <h3>Areas for Improvement</h3>
    <ul>
    """
    
    if "urgency" not in techniques_found:
        feedback += "<li>Add time-sensitive elements to create urgency</li>"
    if "authority" not in techniques_found:
        feedback += "<li>Impersonate a trusted authority figure or organization</li>"
    if "call-to-action" not in techniques_found:
        feedback += "<li>Include a clear, specific action for the victim to take</li>"
    if len(phishing_email) < 200:
        feedback += "<li>Expand the email content for more realistic appearance</li>"
    
    feedback += """
    </ul>
    
    <h3>Security Learning Points</h3>
    <p>Understanding these techniques helps you:</p>
    <ul>
        <li>Recognize similar tactics in real phishing attempts</li>
        <li>Educate others about social engineering risks</li>
        <li>Develop better security awareness</li>
    </ul>
    
    <p><strong>Remember:</strong> This knowledge should only be used for defensive security purposes and education.</p>
    """
    
    return {
        "feedback": feedback,
        "score": min(100, score),
        "effectiveness_rating": effectiveness_rating
    }