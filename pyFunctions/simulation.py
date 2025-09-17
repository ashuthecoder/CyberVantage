import random
import datetime
import traceback
import os
from pyFunctions.api_logging import log_api_request

# Try to import Azure OpenAI helper functions
try:
    from .azure_openai_helper import azure_openai_completion
    AZURE_HELPERS_AVAILABLE = True
except ImportError:
    AZURE_HELPERS_AVAILABLE = False

# Import Google Generative AI types if available
try:
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    # Create dummy classes if import fails
    class HarmCategory:
        HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
        HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
        HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"
    
    class HarmBlockThreshold:
        BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"

# Keep existing generate_unique_simulation_email function
def generate_unique_simulation_email(api_key, genai, session, app):
    """
    Generate a unique phishing or legitimate email for simulation
    
    Args:
        api_key: Google API key for Gemini
        genai: Google Generative AI module
        session: User session data
        app: Flask app
        
    Returns:
        Dict containing email data and whether it's phishing
    """
    # Implementation of email generation for simulation
    # For now, this is a simple placeholder implementation
    templates = [
        {
            "sender": "security@yourcompany.com",
            "subject": "Urgent: Security Alert - Password Reset Required",
            "content": "<p>Dear Valued Employee,</p><p>We have detected unusual login activity on your account. Please reset your password immediately by clicking the link below:</p><p><a href='#'>Reset Password Now</a></p>",
            "is_spam": True
        },
        {
            "sender": "hr@yourcompany.com",
            "subject": "Company Newsletter - June 2024",
            "content": "<p>Hello Team,</p><p>Please find attached the company newsletter for June 2024. It includes important updates about our new office location and upcoming team events.</p>",
            "is_spam": False
        },
        {
            "sender": "payroll@companyx-payments.com",
            "subject": "Action Required: Payroll Information Update",
            "content": "<p>Dear Employee,</p><p>Our records indicate your direct deposit information needs to be verified. Please log in using the link below to confirm your banking details:</p><p><a href='#'>Verify Banking Information</a></p>",
            "is_spam": True
        }
    ]
    
    # Select a random template
    template = random.choice(templates)
    
    # Store in session if needed
    if session:
        session['last_simulation_email'] = template
    
    return template

def generate_simulation_analysis(user_responses, api_key, genai, app):
    """
    Generate detailed analysis of user's simulation performance
    
    Args:
        user_responses: List of user's simulation responses
        api_key: Google API key for Gemini
        genai: Google Generative AI module
        app: Flask app
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Try Azure OpenAI first if available
        if app and app.config.get('AZURE_OPENAI_KEY') and app.config.get('AZURE_OPENAI_ENDPOINT') and AZURE_HELPERS_AVAILABLE:
            try:
                print("[ANALYSIS] Attempting to use Azure OpenAI for simulation analysis")
                azure_result = generate_simulation_analysis_azure(user_responses, app)
                
                if azure_result and azure_result.get("success"):
                    print("[ANALYSIS] Azure OpenAI analysis succeeded")
                    return azure_result
                else:
                    print("[ANALYSIS] Azure OpenAI analysis failed, falling back to Gemini")
            except Exception as e:
                print(f"[ANALYSIS] Azure OpenAI error: {e}")
                # Continue with Gemini fallback
        
        # Fall back to Gemini
        if not api_key:
            return {"error": "API key not available for analysis"}
            
        # Extract insights from user responses
        correct_responses = sum(1 for r in user_responses if r.user_response == r.is_spam_actual)
        total_responses = len(user_responses)
        accuracy = (correct_responses / total_responses) * 100 if total_responses > 0 else 0
        
        # Categorize mistakes
        false_positives = [r for r in user_responses if r.user_response and not r.is_spam_actual]
        false_negatives = [r for r in user_responses if not r.user_response and r.is_spam_actual]
        
        # Prepare prompt for AI analysis
        prompt = f"""
        Generate a detailed analysis of a user's phishing email detection performance. 
        
        Performance details:
        - Total emails analyzed: {total_responses}
        - Correctly identified: {correct_responses}
        - Accuracy rate: {accuracy:.1f}%
        - False positives (legitimate emails marked as phishing): {len(false_positives)}
        - False negatives (phishing emails missed): {len(false_negatives)}
        
        Please provide:
        1. An overall assessment of their performance with specific strengths and weaknesses
        2. Analysis of their mistake patterns (what types of phishing they miss or legitimate emails they flag)
        3. Specific, actionable recommendations for improvement
        4. Security implications of their current detection abilities
        
        Format the response as HTML with appropriate headings (<h3>) and paragraphs (<p>).
        """
        
        model = genai.GenerativeModel('gemini-1.5-pro', 
                                     safety_settings={
                                         HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                         HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                         HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                         HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                                     })
        
        # Log API request
        log_api_request(
            function_name="generate_simulation_analysis",
            prompt_length=len(prompt),
            success=True
        )
        
        response = model.generate_content(prompt)
        analysis_html = response.text
        
        return {
            "success": True,
            "analysis_html": analysis_html,
            "accuracy": accuracy,
            "correct_responses": correct_responses,
            "total_responses": total_responses
        }
        
    except Exception as e:
        error_message = f"Error generating analysis: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="generate_simulation_analysis",
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        return {
            "success": False,
            "error": error_message,
            "analysis_html": "<p>Unable to generate detailed analysis at this time. Please try again later.</p>"
        }

def generate_simulation_analysis_azure(user_responses, app):
    """
    Generate detailed analysis of user's simulation performance using Azure OpenAI
    
    Args:
        user_responses: List of user's simulation responses
        app: Flask app
        
    Returns:
        Dict containing analysis results
    """
    try:
        # Extract insights from user responses
        correct_responses = sum(1 for r in user_responses if r.user_response == r.is_spam_actual)
        total_responses = len(user_responses)
        accuracy = (correct_responses / total_responses) * 100 if total_responses > 0 else 0
        
        # Categorize mistakes
        false_positives = [r for r in user_responses if r.user_response and not r.is_spam_actual]
        false_negatives = [r for r in user_responses if not r.user_response and r.is_spam_actual]
        
        # Prepare prompts for Azure OpenAI
        system_prompt = """You are a cybersecurity educator analyzing phishing simulation results."""
        
        user_prompt = f"""
        Generate a detailed analysis of a user's phishing email detection performance. 
        
        Performance details:
        - Total emails analyzed: {total_responses}
        - Correctly identified: {correct_responses}
        - Accuracy rate: {accuracy:.1f}%
        - False positives (legitimate emails marked as phishing): {len(false_positives)}
        - False negatives (phishing emails missed): {len(false_negatives)}
        
        Please provide:
        1. An overall assessment of their performance with specific strengths and weaknesses
        2. Analysis of their mistake patterns (what types of phishing they miss or legitimate emails they flag)
        3. Specific, actionable recommendations for improvement
        4. Security implications of their current detection abilities
        
        Format the response as HTML with appropriate headings (<h3>) and paragraphs (<p>).
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
            function_name="generate_simulation_analysis_azure",
            prompt_length=len(user_prompt),
            success=status == "SUCCESS",
            error=None if status == "SUCCESS" else f"Status: {status}"
        )
        
        if not text or status != "SUCCESS":
            print(f"[ANALYSIS] Azure analysis failed with status: {status}")
            return None
        
        analysis_html = text
        
        return {
            "success": True,
            "analysis_html": analysis_html,
            "accuracy": accuracy,
            "correct_responses": correct_responses,
            "total_responses": total_responses
        }
        
    except Exception as e:
        error_message = f"Error generating analysis with Azure: {str(e)}"
        traceback.print_exc()
        
        # Log the error
        log_api_request(
            function_name="generate_simulation_analysis_azure",
            prompt_length=0,
            success=False,
            error=error_message
        )
        
        # Re-raise to allow fallback to Gemini
        raise