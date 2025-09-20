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
        # Provide a static assignment when AI is not available
        if not api_key:
            return {
                "instructions": """
                <h2>Phishing Email Creation Assignment</h2>
                <p>Your task is to create a convincing phishing email for educational purposes. This assignment helps you understand how attackers think and craft their messages.</p>
                
                <h3>Assignment Requirements:</h3>
                <ul>
                    <li><strong>Target Scenario:</strong> Create a phishing email pretending to be from a popular online service (e.g., bank, social media, or email provider)</li>
                    <li><strong>Social Engineering Elements:</strong> Include urgency, fear, or authority to motivate quick action</li>
                    <li><strong>Technical Elements:</strong> Use realistic sender addresses, subject lines, and formatting</li>
                    <li><strong>Call to Action:</strong> Include a clear request for the victim to click a link or provide information</li>
                </ul>
                
                <h3>Tips for Success:</h3>
                <ul>
                    <li>Research real phishing emails for inspiration (but don't copy directly)</li>
                    <li>Think about what would make you click or respond to an email</li>
                    <li>Use professional language and formatting to build trust</li>
                    <li>Create a sense of urgency without being too obvious</li>
                </ul>
                
                <p><strong>Remember:</strong> This is for educational purposes only. Never use these techniques maliciously!</p>
                """,
                "rubric": [
                    {"criteria": "Social Engineering Tactics", "points": 30, "description": "Use of urgency, fear, curiosity, or authority"},
                    {"criteria": "Technical Elements", "points": 30, "description": "URLs, formatting, email headers, spoofed sender addresses"},
                    {"criteria": "Psychological Manipulation", "points": 20, "description": "Persuasive language and emotional triggers"},
                    {"criteria": "Realism", "points": 20, "description": "How believable the scenario is in a real-world context"}
                ]
            }
        
        # If we have API access, we could generate dynamic assignments here
        # For now, we'll still use the static version
        return {
            "instructions": """
            <h2>Phishing Email Creation Assignment</h2>
            <p>Your task is to create a convincing phishing email for educational purposes. This assignment helps you understand how attackers think and craft their messages.</p>
            
            <h3>Assignment Requirements:</h3>
            <ul>
                <li><strong>Target Scenario:</strong> Create a phishing email pretending to be from a popular online service (e.g., bank, social media, or email provider)</li>
                <li><strong>Social Engineering Elements:</strong> Include urgency, fear, or authority to motivate quick action</li>
                <li><strong>Technical Elements:</strong> Use realistic sender addresses, subject lines, and formatting</li>
                <li><strong>Call to Action:</strong> Include a clear request for the victim to click a link or provide information</li>
            </ul>
            
            <h3>Tips for Success:</h3>
            <ul>
                <li>Research real phishing emails for inspiration (but don't copy directly)</li>
                <li>Think about what would make you click or respond to an email</li>
                <li>Use professional language and formatting to build trust</li>
                <li>Create a sense of urgency without being too obvious</li>
            </ul>
            
            <p><strong>Remember:</strong> This is for educational purposes only. Never use these techniques maliciously!</p>
            """,
            "rubric": [
                {"criteria": "Social Engineering Tactics", "points": 30, "description": "Use of urgency, fear, curiosity, or authority"},
                {"criteria": "Technical Elements", "points": 30, "description": "URLs, formatting, email headers, spoofed sender addresses"},
                {"criteria": "Psychological Manipulation", "points": 20, "description": "Persuasive language and emotional triggers"},
                {"criteria": "Realism", "points": 20, "description": "How believable the scenario is in a real-world context"}
            ]
        }
        
    except Exception as e:
        print(f"[PHISHING_ASSIGNMENT] Error in assign_phishing_creation: {str(e)}")
        traceback.print_exc()
        return None

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