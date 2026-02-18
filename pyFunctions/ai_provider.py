"""
AI Provider Module - Multi-AI Provider with Fallback Support

This module provides a unified interface for working with multiple AI providers
(Azure OpenAI and Google Gemini) with automatic fallback functionality.

The primary model can be configured via environment variables, and if the primary
model fails, the system will automatically fall back to the secondary model.
"""

import os
import traceback
from typing import Dict, List, Optional, Any, Tuple, Callable

# =============================================================================
# CONFIGURATION
# =============================================================================

# Supported AI providers
PROVIDER_AZURE = "azure"
PROVIDER_GEMINI = "gemini"

# Get primary provider from environment (defaults to Azure)
PRIMARY_PROVIDER = os.getenv("PRIMARY_AI_MODEL", "azure").lower()

# Validate primary provider
if PRIMARY_PROVIDER not in [PROVIDER_AZURE, PROVIDER_GEMINI]:
    print(f"[AI_PROVIDER] Warning: Invalid PRIMARY_AI_MODEL '{PRIMARY_PROVIDER}', defaulting to 'azure'")
    PRIMARY_PROVIDER = PROVIDER_AZURE

# Determine fallback provider
FALLBACK_PROVIDER = PROVIDER_GEMINI if PRIMARY_PROVIDER == PROVIDER_AZURE else PROVIDER_AZURE

print(f"[AI_PROVIDER] Configured with PRIMARY={PRIMARY_PROVIDER}, FALLBACK={FALLBACK_PROVIDER}")

# =============================================================================
# AZURE OPENAI INTEGRATION
# =============================================================================

try:
    from .azure_openai_helper import (
        azure_openai_completion, 
        call_azure_openai_with_retry,
        extract_text_from_response
    )
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("[AI_PROVIDER] Azure OpenAI helper not available")
    def azure_openai_completion(*args, **kwargs): return None, "IMPORT_ERROR"
    def call_azure_openai_with_retry(*args, **kwargs): return None, "IMPORT_ERROR"
    def extract_text_from_response(*args, **kwargs): return None

# =============================================================================
# GOOGLE GEMINI INTEGRATION
# =============================================================================

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    _gemini_configured = False
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    _gemini_configured = False
    print("[AI_PROVIDER] Google Gemini not available")


def _normalize_gemini_model_name(model_name: Optional[str]) -> str:
    """Normalize Gemini model names.

    The Gemini SDK sometimes returns model ids like `models/gemini-...` from list_models().
    GenerativeModel() typically expects `gemini-...`.
    """
    name = (model_name or "").strip()
    if not name:
        name = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
    name = name.strip()
    if name.startswith("models/"):
        name = name[len("models/"):]
    return name

def configure_gemini(api_key: Optional[str] = None) -> bool:
    """
    Configure Google Gemini API
    
    Args:
        api_key: Optional API key. If not provided, will try to get from environment
        
    Returns:
        bool: True if configuration successful, False otherwise
    """
    global _gemini_configured
    
    if not GEMINI_AVAILABLE:
        return False
    
    if _gemini_configured:
        return True
    
    try:
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("[AI_PROVIDER] Gemini API key not found")
            return False
        
        genai.configure(api_key=api_key)
        _gemini_configured = True
        print(f"[AI_PROVIDER] Gemini configured successfully with key: {api_key[:4]}...{api_key[-4:]}")
        return True
    except Exception as e:
        print(f"[AI_PROVIDER] Error configuring Gemini: {e}")
        return False

def gemini_completion(
    prompt: Optional[str] = None,
    system_prompt: str = "You are a helpful assistant.",
    user_prompt: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    model_name: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Get completion from Google Gemini
    
    Args:
        prompt: Legacy single prompt (deprecated, use user_prompt)
        system_prompt: System instruction
        user_prompt: User message
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        model_name: Gemini model to use
        
    Returns:
        tuple: (text_response, status_message)
    """
    if not GEMINI_AVAILABLE:
        return None, "GEMINI_NOT_AVAILABLE"
    
    if not _gemini_configured:
        if not configure_gemini():
            return None, "GEMINI_NOT_CONFIGURED"
    
    # Handle legacy prompt parameter
    if user_prompt is None and prompt is not None:
        user_prompt = prompt
    
    if user_prompt is None:
        return None, "NO_PROMPT"
    
    try:
        # Create model with system instruction if supported
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        model = genai.GenerativeModel(_normalize_gemini_model_name(model_name), generation_config=generation_config)
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            print(f"[AI_PROVIDER] Gemini completion successful")
            return response.text, "SUCCESS"
        else:
            print(f"[AI_PROVIDER] Gemini returned empty response")
            return None, "EMPTY_RESPONSE"
            
    except Exception as e:
        error_msg = str(e)
        print(f"[AI_PROVIDER] Gemini error: {error_msg}")
        traceback.print_exc()
        
        # Check for specific error types
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return None, "RATE_LIMITED"
        elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
            return None, "AUTH_ERROR"
        else:
            return None, f"ERROR: {error_msg}"

def gemini_chat_completion(
    messages: List[Dict[str, str]],
    max_tokens: int = 512,
    temperature: float = 0.7,
    model_name: Optional[str] = None
) -> Tuple[Optional[Any], str]:
    """
    Get chat completion from Google Gemini (compatible with Azure format)
    
    Args:
        messages: List of message dicts with role and content
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        model_name: Gemini model to use
        
    Returns:
        tuple: (response_object, status_message)
    """
    if not GEMINI_AVAILABLE:
        return None, "GEMINI_NOT_AVAILABLE"
    
    if not _gemini_configured:
        if not configure_gemini():
            return None, "GEMINI_NOT_CONFIGURED"
    
    try:
        # Convert messages to Gemini format
        system_prompt = ""
        user_prompt = ""
        
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt += content + "\n"
            elif role == "user":
                user_prompt += content + "\n"
        
        # Use completion function
        text, status = gemini_completion(
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            max_tokens=max_tokens,
            temperature=temperature,
            model_name=model_name
        )
        
        if status == "SUCCESS" and text:
            # Create a response object compatible with Azure format
            response = type('obj', (object,), {
                'text': text,
                'choices': [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': text
                    })()
                })()]
            })()
            return response, status
        else:
            return None, status
            
    except Exception as e:
        print(f"[AI_PROVIDER] Gemini chat error: {e}")
        traceback.print_exc()
        return None, f"ERROR: {str(e)}"

# =============================================================================
# UNIFIED AI INTERFACE WITH FALLBACK
# =============================================================================

def ai_completion_with_fallback(
    prompt: Optional[str] = None,
    system_prompt: str = "You are a helpful assistant.",
    user_prompt: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    app = None
) -> Tuple[Optional[str], str, str]:
    """
    Get AI completion with automatic fallback to secondary provider
    
    Args:
        prompt: Legacy single prompt
        system_prompt: System instruction
        user_prompt: User message
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        app: Flask app for config access
        
    Returns:
        tuple: (text_response, status_message, provider_used)
    """
    # Handle legacy prompt parameter
    if user_prompt is None and prompt is not None:
        user_prompt = prompt
    
    if user_prompt is None:
        return None, "NO_PROMPT", "none"
    
    print(f"[AI_PROVIDER] Attempting completion with primary provider: {PRIMARY_PROVIDER}")
    
    # Try primary provider first
    text, status = _call_provider(
        PRIMARY_PROVIDER,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        app=app
    )
    
    if status == "SUCCESS" and text:
        print(f"[AI_PROVIDER] Success with primary provider: {PRIMARY_PROVIDER}")
        return text, status, PRIMARY_PROVIDER
    
    # Primary failed, try fallback
    print(f"[AI_PROVIDER] Primary provider {PRIMARY_PROVIDER} failed with status: {status}")
    print(f"[AI_PROVIDER] Attempting fallback to: {FALLBACK_PROVIDER}")
    
    text, status = _call_provider(
        FALLBACK_PROVIDER,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        app=app
    )
    
    if status == "SUCCESS" and text:
        print(f"[AI_PROVIDER] Success with fallback provider: {FALLBACK_PROVIDER}")
        return text, status, FALLBACK_PROVIDER
    
    # Both failed
    print(f"[AI_PROVIDER] Both providers failed. Fallback status: {status}")
    return None, f"ALL_PROVIDERS_FAILED: primary={PRIMARY_PROVIDER}, fallback={FALLBACK_PROVIDER}", "none"

def ai_chat_completion_with_fallback(
    messages: List[Dict[str, str]],
    max_tokens: int = 512,
    temperature: float = 0.7,
    app = None
) -> Tuple[Optional[Any], str, str]:
    """
    Get AI chat completion with automatic fallback to secondary provider
    
    Args:
        messages: List of message dicts with role and content
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        app: Flask app for config access
        
    Returns:
        tuple: (response_object, status_message, provider_used)
    """
    print(f"[AI_PROVIDER] Attempting chat completion with primary provider: {PRIMARY_PROVIDER}")
    
    # Try primary provider first
    response, status = _call_provider_chat(
        PRIMARY_PROVIDER,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        app=app
    )
    
    if status == "SUCCESS" and response:
        print(f"[AI_PROVIDER] Success with primary provider: {PRIMARY_PROVIDER}")
        return response, status, PRIMARY_PROVIDER
    
    # Primary failed, try fallback
    print(f"[AI_PROVIDER] Primary provider {PRIMARY_PROVIDER} failed with status: {status}")
    print(f"[AI_PROVIDER] Attempting fallback to: {FALLBACK_PROVIDER}")
    
    response, status = _call_provider_chat(
        FALLBACK_PROVIDER,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        app=app
    )
    
    if status == "SUCCESS" and response:
        print(f"[AI_PROVIDER] Success with fallback provider: {FALLBACK_PROVIDER}")
        return response, status, FALLBACK_PROVIDER
    
    # Both failed
    print(f"[AI_PROVIDER] Both providers failed. Fallback status: {status}")
    return None, f"ALL_PROVIDERS_FAILED: primary={PRIMARY_PROVIDER}, fallback={FALLBACK_PROVIDER}", "none"

# =============================================================================
# INTERNAL HELPER FUNCTIONS
# =============================================================================

def _call_provider(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    temperature: float,
    app = None
) -> Tuple[Optional[str], str]:
    """Call a specific AI provider"""
    if provider == PROVIDER_AZURE:
        if not AZURE_AVAILABLE:
            return None, "AZURE_NOT_AVAILABLE"
        return azure_openai_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            app=app
        )
    elif provider == PROVIDER_GEMINI:
        if not GEMINI_AVAILABLE:
            return None, "GEMINI_NOT_AVAILABLE"
        return gemini_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    else:
        return None, f"UNKNOWN_PROVIDER: {provider}"

def _call_provider_chat(
    provider: str,
    messages: List[Dict[str, str]],
    max_tokens: int,
    temperature: float,
    app = None
) -> Tuple[Optional[Any], str]:
    """Call a specific AI provider with chat format"""
    if provider == PROVIDER_AZURE:
        if not AZURE_AVAILABLE:
            return None, "AZURE_NOT_AVAILABLE"
        return call_azure_openai_with_retry(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            app=app
        )
    elif provider == PROVIDER_GEMINI:
        if not GEMINI_AVAILABLE:
            return None, "GEMINI_NOT_AVAILABLE"
        return gemini_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
    else:
        return None, f"UNKNOWN_PROVIDER: {provider}"

def extract_text_from_ai_response(response: Any, provider: str) -> Optional[str]:
    """
    Extract text from AI response regardless of provider
    
    Args:
        response: The response object from the AI provider
        provider: Which provider generated the response
        
    Returns:
        Extracted text or None
    """
    if not response:
        return None
    
    try:
        if provider == PROVIDER_AZURE:
            return extract_text_from_response(response)
        elif provider == PROVIDER_GEMINI:
            # Gemini response format
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content
        
        return None
    except Exception as e:
        print(f"[AI_PROVIDER] Error extracting text: {e}")
        return None

# =============================================================================
# PROVIDER STATUS CHECKING
# =============================================================================

def get_provider_status() -> Dict[str, Any]:
    """
    Get status of all AI providers
    
    Returns:
        dict: Status information for each provider
    """
    status = {
        "primary_provider": PRIMARY_PROVIDER,
        "fallback_provider": FALLBACK_PROVIDER,
        "providers": {}
    }
    
    # Azure status
    if AZURE_AVAILABLE:
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        status["providers"]["azure"] = {
            "available": True,
            "configured": bool(azure_key and azure_endpoint)
        }
    else:
        status["providers"]["azure"] = {
            "available": False,
            "configured": False
        }
    
    # Gemini status
    if GEMINI_AVAILABLE:
        gemini_key = os.getenv("GOOGLE_API_KEY")
        status["providers"]["gemini"] = {
            "available": True,
            "configured": bool(gemini_key)
        }
    else:
        status["providers"]["gemini"] = {
            "available": False,
            "configured": False
        }
    
    return status

# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_ai_providers(app = None):
    """
    Initialize all available AI providers
    
    Args:
        app: Optional Flask app for configuration
    """
    print("[AI_PROVIDER] Initializing AI providers...")
    
    # Get status
    status = get_provider_status()
    print(f"[AI_PROVIDER] Status: {status}")
    
    # Try to configure Gemini if it's the primary or if we have the key
    if GEMINI_AVAILABLE:
        configure_gemini()
    
    return status
