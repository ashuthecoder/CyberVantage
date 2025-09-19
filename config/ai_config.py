"""
AI configuration - Azure OpenAI only (Gemini logic removed as requested)
"""
import os
import openai

def configure_azure_openai(app):
    """Configure Azure OpenAI integration"""
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    if AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT:
        openai.api_key = AZURE_OPENAI_KEY
        openai.api_base = AZURE_OPENAI_ENDPOINT.split('/openai/')[0] if '/openai/' in AZURE_OPENAI_ENDPOINT else AZURE_OPENAI_ENDPOINT
        openai.api_type = "azure"
        openai.api_version = "2023-05-15"  # Update with the API version used in your Azure endpoint
        app.config['AZURE_OPENAI_KEY'] = AZURE_OPENAI_KEY  # Set for diagnostics
        app.config['AZURE_OPENAI_ENDPOINT'] = AZURE_OPENAI_ENDPOINT
        
        # Extract deployment name from endpoint or use default
        deployment_parts = AZURE_OPENAI_ENDPOINT.split('/deployments/')
        deployment_name = "gpt-4.1-nano"  # Default
        if len(deployment_parts) > 1:
            deployment_name = deployment_parts[1].split('/')[0]
        
        app.config['AZURE_OPENAI_DEPLOYMENT'] = deployment_name
        print(f"✓ Azure OpenAI API key loaded successfully: {AZURE_OPENAI_KEY[:4]}...{AZURE_OPENAI_KEY[-4:]}")
        print(f"✓ Azure OpenAI deployment: {deployment_name}")
    else:
        print("Warning: AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT not found. AI features will be limited.")
    
    return AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT