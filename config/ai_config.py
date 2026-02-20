"""
AI configuration - Multi-AI Provider support (Azure OpenAI and Google Gemini)
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
        print("✓ Azure OpenAI API key loaded successfully")
        print(f"✓ Azure OpenAI deployment: {deployment_name}")
    else:
        print("Warning: AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT not found.")
    
    return AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT

def configure_ai_providers(app):
    """Configure all AI providers (Azure OpenAI and Google Gemini) with fallback support"""
    # Configure Azure OpenAI
    configure_azure_openai(app)
    
    # Configure Google Gemini
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        app.config['GOOGLE_API_KEY'] = GOOGLE_API_KEY
        print("✓ Google Gemini API key loaded successfully")
    else:
        print("Warning: GOOGLE_API_KEY not found.")
    
    # Get primary AI model configuration
    PRIMARY_AI_MODEL = os.getenv("PRIMARY_AI_MODEL", "azure").lower()
    app.config['PRIMARY_AI_MODEL'] = PRIMARY_AI_MODEL
    
    # Determine fallback
    FALLBACK_AI_MODEL = "gemini" if PRIMARY_AI_MODEL == "azure" else "azure"
    app.config['FALLBACK_AI_MODEL'] = FALLBACK_AI_MODEL
    
    print(f"✓ AI Provider Configuration:")
    print(f"  - Primary Model: {PRIMARY_AI_MODEL}")
    print(f"  - Fallback Model: {FALLBACK_AI_MODEL}")
    
    # Initialize AI provider module
    try:
        from pyFunctions.ai_provider import initialize_ai_providers
        initialize_ai_providers(app)
    except ImportError as e:
        print(f"Warning: Could not initialize AI providers: {e}")
    
    return {
        "azure_configured": bool(os.getenv("AZURE_OPENAI_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT")),
        "gemini_configured": bool(GOOGLE_API_KEY),
        "primary_model": PRIMARY_AI_MODEL,
        "fallback_model": FALLBACK_AI_MODEL
    }