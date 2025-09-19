"""
Azure OpenAI Service integration for CyberVantage.
"""
import os
import json
import random
import logging
import openai
from flask import current_app
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureOpenAIService:
    """
    Service class for integrating with Azure OpenAI.
    """
    
    def __init__(self):
        """
        Initialize the Azure OpenAI service with API key and endpoint.
        """
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        openai.api_type = "azure"
        openai.api_version = "2023-05-15"
        openai.api_key = self.api_key
        openai.api_base = self.endpoint
    
    def get_ai_response(self, prompt, max_tokens=150, system_prompt="You are a helpful assistant."):
        """
        Get response from Azure OpenAI for a given prompt.
        """
        try:
            response = openai.ChatCompletion.create(
                engine=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"Azure OpenAI API error: {str(e)}")
            return None
    
    def generate_simulation_email(self, difficulty, is_phishing):
        """
        Generate a simulated email for phishing training.
        """
        email_type = "phishing" if is_phishing else "legitimate"
        system_prompt = (
            "You are an expert in cybersecurity and email security. "
            "Your task is to create realistic email scenarios for security training."
        )
        
        prompt = f"""
        Create a {difficulty} {email_type} email for cybersecurity training.
        
        If it's a phishing email, include subtle red flags appropriate for the {difficulty} level.
        If it's legitimate, make it realistic but without suspicious elements.
        
        Provide the email in JSON format with these fields:
        - subject: The email subject line
        - sender: The sender's email address (make it appropriate for the email type)
        - content: The HTML body of the email (keep it under 200 words)
        - is_phishing: {str(is_phishing).lower()}
        - explanation: A detailed explanation of why this is or isn't a phishing email
        
        Just return the JSON object without any other text.
        """
        
        try:
            response = self.get_ai_response(prompt, max_tokens=800, system_prompt=system_prompt)
            if not response:
                return None
                
            # Extract JSON from response (handle cases where model adds extra text)
            try:
                # Try to parse the entire response first
                email_data = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON using string manipulation
                try:
                    json_start = response.find('{')
                    json_end = response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        email_json = response[json_start:json_end]
                        email_data = json.loads(email_json)
                    else:
                        return None
                except:
                    return None
            
            # Validate required fields
            required_fields = ['subject', 'sender', 'content', 'is_phishing', 'explanation']
            for field in required_fields:
                if field not in email_data:
                    return None
                    
            # Ensure is_phishing matches what was requested
            email_data['is_phishing'] = is_phishing
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error generating simulation email: {str(e)}")
            return None
    
    def evaluate_user_action(self, email_data, user_assessment, user_explanation):
        """
        Evaluate the user's explanation for their assessment of an email.
        """
        email_type = "phishing" if email_data.get('is_phishing') else "legitimate"
        was_correct = (user_assessment == email_data.get('is_phishing'))
        actual_explanation = email_data.get('explanation', '')
        
        system_prompt = (
            "You are a cybersecurity education expert specializing in phishing awareness. "
            "Your job is to provide helpful, educational feedback to users in training."
        )
        
        prompt = f"""
        The user was shown a {email_type} email with these details:
        Subject: "{email_data.get('subject')}"
        Sender: {email_data.get('sender')}
        
        The user's assessment was that this email was {'phishing' if user_assessment else 'legitimate'}, which is {'correct' if was_correct else 'incorrect'}.
        
        The user provided this explanation: "{user_explanation}"
        
        The actual explanation is: "{actual_explanation}"
        
        Please provide constructive feedback on the user's explanation. Include:
        1. What they got right (if anything)
        2. What they missed or misunderstood (if anything)
        3. Key indicators they should look for in the future
        
        Keep your feedback educational, encouraging, and under 200 words.
        """
        
        try:
            feedback = self.get_ai_response(prompt, max_tokens=400, system_prompt=system_prompt)
            return feedback if feedback else "No feedback available."
        except Exception as e:
            logger.error(f"Error evaluating user explanation: {str(e)}")
            return "An error occurred while evaluating your explanation."
    
    def get_simulation_scenario(self, difficulty="medium", category="phishing"):
        """
        Generate a cybersecurity simulation scenario.
        """
        prompt = f"Create a detailed {difficulty} level cybersecurity simulation scenario about {category}."
        return self.get_ai_response(prompt, max_tokens=500)
    
    def get_analysis(self, user_actions, scenario):
        """
        Analyze user's actions in a simulation scenario.
        """
        prompt = f"Analyze the following user actions in response to a {scenario} scenario: {user_actions}"
        return self.get_ai_response(prompt, max_tokens=300)

# Create service instance for import
ai_service = AzureOpenAIService()

# Export functions for blueprint routes
get_ai_response = ai_service.get_ai_response
get_simulation_scenario = ai_service.get_simulation_scenario
get_analysis = ai_service.get_analysis
generate_simulation_email = ai_service.generate_simulation_email
evaluate_user_action = ai_service.evaluate_user_action