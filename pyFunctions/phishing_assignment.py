import random
import datetime
import re
import markdown
import traceback
from pyFunctions.api_logging import log_api_request

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
        if not api_key:
            return {
                "feedback": "API key not available for evaluation. Using fallback evaluation.",
                "score": 50,
                "effectiveness_rating": "Not Rated"
            }
            
        # Configure safety settings
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Prepare evaluation prompt
        prompt = f"""
        You are a cybersecurity expert evaluating a phishing email created by a student as part of their training.
        
        Student-created phishing email:
        ```
        {phishing_email}
        ```
        
        Evaluate the phishing email on the following criteria:
        1. Social Engineering Tactics (30 points): Use of urgency, fear, curiosity, or authority
        2. Technical Elements (30 points): URLs, formatting, email headers, spoofed sender addresses
        3. Psychological Manipulation (20 points): Persuasive language and emotional triggers
        4. Realism (20 points): How believable the scenario is in a real-world context
        
        For each criterion, assign a specific score and explain why.
        
        Then provide:
        1. Overall score (out of 100)
        2. Effectiveness rating (Low, Medium, High, Very High)
        3. Detailed feedback with specific improvements
        4. What worked well in their approach
        
        Format your response as HTML with appropriate headings (<h3>) and paragraphs (<p>).
        Begin with an overall assessment and end with actionable recommendations.
        """
        
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
        
        # Extract score using rough heuristics (more sophisticated parsing could be implemented)
        score = 0
        effectiveness_rating = "Medium"
        
        if "overall score" in feedback_html.lower():
            try:
                score_text = feedback_html.lower().split("overall score")[1].split(".")[0]
                possible_scores = [int(s) for s in score_text.split() if s.isdigit()]
                if possible_scores:
                    score = possible_scores[0]
            except:
                score = 70  # Default if parsing fails
                
        if "effectiveness rating" in feedback_html.lower():
            if "very high" in feedback_html.lower():
                effectiveness_rating = "Very High"
            elif "high" in feedback_html.lower():
                effectiveness_rating = "High"
            elif "medium" in feedback_html.lower():
                effectiveness_rating = "Medium"
            elif "low" in feedback_html.lower():
                effectiveness_rating = "Low"
        
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
        
        return {
            "feedback": "<p>We couldn't evaluate your phishing email at this time. Please try again later.</p>",
            "score": 0,
            "effectiveness_rating": "Not Rated"
        }