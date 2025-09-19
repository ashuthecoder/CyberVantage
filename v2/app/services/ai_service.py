"""
Azure OpenAI Service integration for CyberVantage.
"""
import os
import openai
from flask import current_app

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
    
    def get_ai_response(self, prompt, max_tokens=150):
        """
        Get response from Azure OpenAI for a given prompt.
        """
        try:
            response = openai.Completion.create(
                engine=self.deployment_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].text.strip()
        except Exception as e:
            current_app.logger.error(f"Azure OpenAI API error: {str(e)}")
            return None
    
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