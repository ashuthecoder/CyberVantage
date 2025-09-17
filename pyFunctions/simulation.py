import datetime
import random
import traceback
import os
from pyFunctions.api_logging import log_api_request

# Keep existing generate_unique_simulation_email function

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
        if not api_key:
            return {"error": "API key not available for analysis"}
            
        # Configure safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
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
                                     safety_settings=safety_settings)
        
        function_name = "generate_simulation_analysis"
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
            model="gemini-1.5-pro",
            prompt_length=len(prompt) if 'prompt' in locals() else 0,
            response_length=0,
            start_time=start_time if 'start_time' in locals() else datetime.datetime.now(),
            end_time=datetime.datetime.now(),
            success=False,
            error_message=error_message
        )
        
        return {
            "success": False,
            "error": error_message,
            "analysis_html": "<p>Unable to generate detailed analysis at this time. Please try again later.</p>"
        }