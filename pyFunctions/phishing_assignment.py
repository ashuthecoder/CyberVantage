import datetime
import traceback
import json
import re
from pyFunctions.api_logging import log_api_request

# Try to import Azure OpenAI helper functions
try:
    from .azure_openai_helper import azure_openai_completion
    AZURE_HELPERS_AVAILABLE = True
except ImportError:
    AZURE_HELPERS_AVAILABLE = False

def assign_phishing_creation(api_key, genai, app):
    """
    Generate a phishing email creation assignment.
    Renamed from 'final assignment' to 'craft phishing email'
    """
    try:
        # Try Azure OpenAI first if available
        if app and app.config.get('AZURE_OPENAI_KEY') and app.config.get('AZURE_OPENAI_ENDPOINT') and AZURE_HELPERS_AVAILABLE:
            try:
                print("[ASSIGN] Attempting to use Azure OpenAI for phishing assignment")
                azure_result = assign_phishing_creation_azure(app)
                
                if azure_result and 'assignment' in azure_result:
                    print("[ASSIGN] Azure OpenAI assignment succeeded")
                    return azure_result
                else:
                    print("[ASSIGN] Azure OpenAI assignment failed, falling back to Gemini")
            except Exception as e:
                print(f"[ASSIGN] Azure OpenAI error: {e}")
                # Continue with Gemini fallback
        
        # Fall back to Gemini
        if not api_key:
            return {
                "assignment": "<p>API key not available for generating assignment. Please try again later.</p>",
                "success": False
            }
            
        # Configure safety settings
        safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Prepare prompt
        prompt = """
        Create an assignment for cybersecurity trainees to craft a convincing phishing email for educational purposes.
        
        The assignment should include:
        1. A specific target organization (company, university, service provider, etc.)
        2. The phishing goal (credential harvesting, malware delivery, etc.)
        3. Constraints and requirements for the exercise
        4. 3-4 tips or best practices for creating effective phishing emails
        5. A reminder that this is for educational purposes only
        
        Format the response as HTML with appropriate headings (<h3>) and paragraphs (<p>).
        Make the assignment challenging but achievable for beginners in cybersecurity training.
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro', 
                                     safety_settings=safety_settings)
        
        # Log API request
        log_api_request(
            function_name="assign_phishing_creation",
            prompt_length=len(prompt),
            success=True
        )
        
        response = model.generate_content(prompt)
        
        return {
            "assignment": response.text,
            "success": True
        }
        
    except Exception as e:
        error_message = f"Error generating phishing assignment: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="assign_phishing_creation",
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        return {
            "assignment": "<p>We couldn't generate an assignment at this time. Please try again later.</p>",
            "success": False
        }

def assign_phishing_creation_azure(app):
    """
    Generate a phishing email creation assignment using Azure OpenAI
    """
    try:
        # Prepare prompts for Azure OpenAI
        system_prompt = """You are a cybersecurity educator creating training assignments."""
        
        user_prompt = """
        Create an assignment for cybersecurity trainees to craft a convincing phishing email for educational purposes.
        
        The assignment should include:
        1. A specific target organization (company, university, service provider, etc.)
        2. The phishing goal (credential harvesting, malware delivery, etc.)
        3. Constraints and requirements for the exercise
        4. 3-4 tips or best practices for creating effective phishing emails
        5. A reminder that this is for educational purposes only
        
        Format the response as HTML with appropriate headings (<h3>) and paragraphs (<p>).
        Make the assignment challenging but achievable for beginners in cybersecurity training.
        """
        
        # Call Azure OpenAI
        text, status = azure_openai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=0.7,
            app=app
        )
        
        # Log API request
        log_api_request(
            function_name="assign_phishing_creation_azure",
            prompt_length=len(user_prompt),
            success=status == "SUCCESS",
            error=None if status == "SUCCESS" else f"Status: {status}"
        )
        
        if not text or status != "SUCCESS":
            print(f"[ASSIGN] Azure phishing assignment failed with status: {status}")
            return None
        
        return {
            "assignment": text,
            "success": True
        }
        
    except Exception as e:
        error_message = f"Error generating phishing assignment with Azure: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="assign_phishing_creation_azure",
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        # Re-raise to allow fallback to Gemini
        raise

def evaluate_phishing_creation(phishing_email, api_key, genai, app):
    """
    Evaluate user-created phishing email and provide detailed scoring and feedback
    """
    try:
        # Try Azure OpenAI first if available
        if app and app.config.get('AZURE_OPENAI_KEY') and app.config.get('AZURE_OPENAI_ENDPOINT') and AZURE_HELPERS_AVAILABLE:
            try:
                print("[EVALUATE] Attempting to use Azure OpenAI for phishing evaluation")
                azure_result = evaluate_phishing_creation_azure(phishing_email, app)
                
                if azure_result and 'feedback' in azure_result:
                    print("[EVALUATE] Azure OpenAI evaluation succeeded")
                    return azure_result
                else:
                    print("[EVALUATE] Azure OpenAI evaluation failed, falling back to Gemini")
            except Exception as e:
                print(f"[EVALUATE] Azure OpenAI error: {e}")
                # Continue with Gemini fallback
                
        # Fall back to Gemini
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
        Evaluate this user-created phishing email for a cybersecurity education platform.
        
        USER'S PHISHING EMAIL:
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
        
        # Log API request
        log_api_request(
            function_name="evaluate_phishing_creation",
            prompt_length=len(prompt),
            success=True
        )
        
        response = model.generate_content(prompt)
        
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
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        return {
            "feedback": "<p>We couldn't evaluate your phishing email at this time. Please try again later.</p>",
            "score": 0,
            "effectiveness_rating": "Not Rated"
        }

def evaluate_phishing_creation_azure(phishing_email, app):
    """
    Evaluate user-created phishing email using Azure OpenAI and provide detailed scoring and feedback
    """
    try:
        # Prepare prompts for Azure OpenAI
        system_prompt = """You are a cybersecurity educator evaluating phishing emails created for educational purposes."""
        
        user_prompt = f"""
        Evaluate this user-created phishing email for a cybersecurity education platform.
        
        USER'S PHISHING EMAIL:
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
        
        # Call Azure OpenAI
        text, status = azure_openai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1024,
            temperature=0.2,
            app=app
        )
        
        # Log API request
        log_api_request(
            function_name="evaluate_phishing_creation_azure",
            prompt_length=len(user_prompt),
            success=status == "SUCCESS",
            error=None if status == "SUCCESS" else f"Status: {status}"
        )
        
        if not text or status != "SUCCESS":
            print(f"[EVALUATE] Azure phishing evaluation failed with status: {status}")
            return None
        
        # Extract score using rough heuristics (more sophisticated parsing could be implemented)
        feedback_html = text
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
        error_message = f"Error evaluating phishing creation with Azure: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="evaluate_phishing_creation_azure",
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        # Re-raise to allow fallback to Gemini
        raise