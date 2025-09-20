"""
Azure OpenAI API Helper Module

This module provides utility functions for working with Azure OpenAI API,
including retry logic, error handling, and response extraction.
"""

import os
import time
import json
import traceback
import uuid
from typing import Dict, List, Optional, Any, Tuple

# Try to use openai library, depending on version
try:
    import openai
    from openai import OpenAI, AzureOpenAI
    OPENAI_VERSION = getattr(openai, "__version__", "0.0.0")
    IS_OPENAI_V1 = OPENAI_VERSION.startswith("1.")
except ImportError:
    # If import fails, create mock objects
    OPENAI_VERSION = "0.0.0"
    IS_OPENAI_V1 = False
    
    class OpenAI:
        pass
        
    class AzureOpenAI:
        pass

# Import older openai error types if available
if not IS_OPENAI_V1:
    try:
        from openai.error import (
            APIError, 
            RateLimitError, 
            ServiceUnavailableError, 
            Timeout
        )
    except ImportError:
        # Create dummy error classes if import fails
        class APIError(Exception): pass
        class RateLimitError(Exception): pass
        class ServiceUnavailableError(Exception): pass
        class Timeout(Exception): pass

# Common imports that should work regardless of version
import requests

# Import API logging functions with fallback
try:
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

# Set the default Azure OpenAI model/deployment
DEFAULT_AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-nano")
DEFAULT_MAX_TOKENS = 512
LOG_FILE_PATH = 'logs/azure_openai_requests.log'

# Global client variable
azure_client = None

# =============================================================================
# RETRY HELPERS AND UTILS
# =============================================================================

def extract_deployment_from_endpoint(endpoint: str) -> str:
    """Extract deployment name from an Azure OpenAI endpoint URL"""
    if not endpoint or '/deployments/' not in endpoint:
        return DEFAULT_AZURE_DEPLOYMENT
    
    try:
        deployment_parts = endpoint.split('/deployments/')
        if len(deployment_parts) > 1:
            return deployment_parts[1].split('/')[0]
    except Exception:
        pass
        
    return DEFAULT_AZURE_DEPLOYMENT

def get_api_version_from_endpoint(endpoint: str) -> str:
    """Extract API version from an Azure OpenAI endpoint URL"""
    if not endpoint or 'api-version=' not in endpoint:
        return "2023-05-15"
    
    try:
        version_parts = endpoint.split('api-version=')
        if len(version_parts) > 1:
            return version_parts[1].split('&')[0]
    except Exception:
        pass
    
    return "2023-05-15"

def mask_api_key(key: str) -> str:
    """Mask the API key for logging"""
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

def setup_azure_client(api_key: str, endpoint: str) -> Any:
    """Set up the appropriate Azure OpenAI client based on the OpenAI version"""
    global azure_client
    
    # Extract base URL from endpoint if needed
    if '/deployments/' in endpoint:
        base_url = endpoint.split('/deployments/')[0]
    else:
        base_url = endpoint
    
    # Remove trailing '/openai' if present to avoid double /openai/openai/ in URLs
    # The AzureOpenAI client automatically adds the /openai prefix
    if base_url.endswith('/openai'):
        base_url = base_url[:-7]  # Remove '/openai'
    
    api_version = get_api_version_from_endpoint(endpoint)
    
    # For OpenAI SDK v1.x
    if IS_OPENAI_V1:
        azure_client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=base_url
        )
        return azure_client
    
    # For older OpenAI SDK versions
    else:
        # Set configuration globally
        openai.api_type = "azure"
        openai.api_key = api_key
        
        # These attributes might not exist in newer versions, so use setattr
        try:
            setattr(openai, "api_base", base_url)
            setattr(openai, "api_version", api_version)
        except:
            pass
            
        return openai

def call_azure_openai_with_retry(
    messages: List[Dict[str, str]], 
    deployment_name: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.7,
    app = None,
    max_attempts: int = 3,
    initial_delay: float = 0.5
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Call Azure OpenAI API with retry logic and exponential backoff.
    
    Args:
        messages: List of message dicts with role and content
        deployment_name: Azure OpenAI deployment name
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        app: Flask app for config access
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay between retries in seconds
    
    Returns:
        tuple: (response_dict, status_message) - response can be None if all attempts fail
    """
    global azure_client
    
    # Ensure Azure client is initialized if needed
    if IS_OPENAI_V1 and azure_client is None:
        # Get API credentials
        api_key = None
        endpoint = None
        
        if app:
            api_key = app.config.get('AZURE_OPENAI_KEY')
            endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
        
        if not api_key:
            api_key = os.getenv('AZURE_OPENAI_KEY')
        
        if not endpoint:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        
        # Initialize client if we have credentials
        if api_key and endpoint:
            azure_client = setup_azure_client(api_key, endpoint)
            print(f"[AZURE] Initialized Azure client with endpoint: {endpoint}")
    
    if app:
        # Get deployment from app config if available
        deployment_name = deployment_name or app.config.get('AZURE_OPENAI_DEPLOYMENT', DEFAULT_AZURE_DEPLOYMENT)
    else:
        deployment_name = deployment_name or DEFAULT_AZURE_DEPLOYMENT
    
    response = None
    status_message = "ERROR"
    
    # Add request ID for idempotency and tracing
    request_id = str(uuid.uuid4())
    
    for attempt in range(max_attempts):
        try:
            print(f"[AZURE] Attempt {attempt + 1}/{max_attempts} with deployment {deployment_name}")
            
            # Create the API request - handle both OpenAI v1 and older versions
            if IS_OPENAI_V1 and azure_client:
                response = azure_client.chat.completions.create(
                    model=deployment_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            elif not IS_OPENAI_V1:
                response = openai.ChatCompletion.create(
                    engine=deployment_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    request_timeout=30,
                    user=request_id
                )
            else:
                raise ValueError("OpenAI client not properly initialized")
            
            if is_valid_completion_response(response):
                print(f"[AZURE] Success on attempt {attempt + 1}")
                status_message = "SUCCESS"
                return response, status_message
            else:
                print(f"[AZURE] Invalid response format on attempt {attempt + 1}")
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"[AZURE] Waiting {delay}s before retry...")
                    time.sleep(delay)
                
        except Exception as e:
            error_class = e.__class__.__name__
            print(f"[AZURE] Error ({error_class}) on attempt {attempt + 1}: {e}")
            
            # Handle rate limits specially
            if error_class == "RateLimitError" or "rate limit" in str(e).lower():
                status_message = "RATE_LIMITED"
                # Longer delay for rate limits
                if attempt < max_attempts - 1:
                    delay = initial_delay * (4 ** attempt)
                    print(f"[AZURE] Waiting {delay}s before retry...")
                    time.sleep(delay)
            
            # Handle timeouts
            elif error_class == "Timeout" or "timeout" in str(e).lower():
                status_message = "TIMEOUT"
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"[AZURE] Waiting {delay}s before retry...")
                    time.sleep(delay)
            
            # Handle API errors
            elif error_class in ["APIError", "ServiceUnavailableError"] or "503" in str(e):
                status_message = f"API_ERROR: {str(e)}"
                if attempt < max_attempts - 1:
                    delay = initial_delay * (2 ** attempt)
                    print(f"[AZURE] Waiting {delay}s before retry...")
                    time.sleep(delay)
            
            # Other unexpected errors
            else:
                print(f"[AZURE] Unexpected error on attempt {attempt + 1}: {e}")
                traceback.print_exc()
                status_message = f"ERROR: {str(e)}"
                # For unexpected errors, don't retry
                break
    
    print("[AZURE] All attempts failed")
    return None, status_message

def is_valid_completion_response(response: Any) -> bool:
    """Check if response contains valid completion data"""
    if not response:
        return False
        
    try:
        # Handle different response formats based on OpenAI version
        if IS_OPENAI_V1:
            # OpenAI v1 returns objects with model attributes
            return hasattr(response, "choices") and len(response.choices) > 0
        else:
            # Older versions return dictionaries
            if isinstance(response, dict):
                if "choices" in response and response["choices"]:
                    if "message" in response["choices"][0]:
                        return True
                    
        return False
    except Exception as e:
        print(f"[AZURE] Error checking response: {e}")
        return False

def extract_text_from_response(response: Any) -> Optional[str]:
    """Extract text content from Azure OpenAI API response"""
    if not response:
        return None
        
    try:
        # Handle different response formats based on OpenAI version
        if IS_OPENAI_V1:
            # OpenAI v1 returns objects with model attributes
            if hasattr(response, "choices") and len(response.choices) > 0:
                return response.choices[0].message.content
        else:
            # Older versions return dictionaries
            if isinstance(response, dict):
                if "choices" in response and response["choices"]:
                    if "message" in response["choices"][0] and "content" in response["choices"][0]["message"]:
                        return response["choices"][0]["message"]["content"]
                    
        return None
    except Exception as e:
        print(f"[AZURE] Error extracting text: {e}")
        return None

# =============================================================================
# HIGH-LEVEL API FUNCTIONS
# =============================================================================

def azure_openai_completion(
    prompt: Optional[str] = None,
    system_prompt: str = "You are a helpful assistant.",
    user_prompt: Optional[str] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.7,
    app = None,
    deployment_name: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    High-level function to get a completion from Azure OpenAI.
    
    Args:
        prompt: DEPRECATED - legacy plain prompt (use system_prompt and user_prompt instead)
        system_prompt: System message 
        user_prompt: User message
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        app: Flask app for config access
        deployment_name: Azure OpenAI deployment name
        
    Returns:
        tuple: (text_response, status_message) - text can be None if request fails
    """
    global azure_client
    
    # Check rate limit before API call
    if not check_rate_limit():
        print("[AZURE] Rate limit reached")
        return None, "RATE_LIMITED"
    
    # Prepare messages - support both new and legacy calling patterns
    if user_prompt is None and prompt is not None:
        # Legacy single prompt mode
        user_prompt = prompt
    
    # Ensure we have at least a user prompt
    if user_prompt is None:
        print("[AZURE] No prompt provided")
        return None, "NO_PROMPT"
        
    # Construct messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Extract API key from environment or app config
    api_key = None
    endpoint = None
    
    if app:
        api_key = app.config.get('AZURE_OPENAI_KEY')
        endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
    
    if not api_key:
        api_key = os.getenv('AZURE_OPENAI_KEY')
    
    if not endpoint:
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    
    # Set up OpenAI client with Azure details if not already configured
    if api_key and endpoint:
        extracted_deployment = extract_deployment_from_endpoint(endpoint)
        deployment_to_use = deployment_name or extracted_deployment or DEFAULT_AZURE_DEPLOYMENT
        
        # Set up the appropriate client
        azure_client = setup_azure_client(api_key, endpoint)
        
        print(f"Using Azure OpenAI with API key: {mask_api_key(api_key)}")
        print(f"Endpoint: {endpoint}")
        print(f"Deployment: {deployment_to_use}")
    else:
        print("[AZURE] Missing API key or endpoint")
        return None, "MISSING_CREDENTIALS"
    
    # Create cache key for possible reuse
    cache_key = create_cache_key("azure_openai", f"{system_prompt}|{user_prompt}|{max_tokens}|{temperature}")
    
    # Define the function to call if not cached
    def generate_fresh():
        # Log the API request
        log_api_request(
            function_name="azure_openai_completion",
            prompt_length=len(user_prompt) if user_prompt else 0,
            success=True,
            model_used=deployment_to_use,
            api_source="AZURE"
        )
                        
        # Make the API call with retry
        response, status = call_azure_openai_with_retry(
            messages=messages,
            deployment_name=deployment_to_use,
            max_tokens=max_tokens,
            temperature=temperature,
            app=app
        )
        
        # Extract text from response
        text = extract_text_from_response(response) if response else None
        
        return text, status
    
    # Try to get from cache or generate fresh
    return get_cached_or_generate(cache_key, generate_fresh)

def azure_openai_get_embedding(
    text: str,
    app = None,
    deployment_name: Optional[str] = None
) -> Tuple[Optional[List[float]], str]:
    """Get an embedding vector for a text using Azure OpenAI API"""
    # This is a placeholder for embedding functionality
    # Implementation would be similar to completion but use embedding API
    return None, "NOT_IMPLEMENTED"

# =============================================================================
# DIAGNOSTICS AND TESTING
# =============================================================================

def test_azure_openai_connection(app=None) -> Dict[str, Any]:
    """
    Test the Azure OpenAI connection and return diagnostic information.
    
    Args:
        app: Flask app for config access
        
    Returns:
        dict: Diagnostic information about the connection
    """
    result = {
        "status": "NOT_TESTED",
        "sdk_version": OPENAI_VERSION,
        "details": {},
        "error": None
    }
    
    try:
        # Get API credentials
        api_key = None
        endpoint = None
        deployment = None
        
        if app:
            api_key = app.config.get('AZURE_OPENAI_KEY')
            endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
            deployment = app.config.get('AZURE_OPENAI_DEPLOYMENT', DEFAULT_AZURE_DEPLOYMENT)
        
        if not api_key:
            api_key = os.getenv('AZURE_OPENAI_KEY')
        
        if not endpoint:
            endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            
        if not deployment and endpoint:
            deployment = extract_deployment_from_endpoint(endpoint) or DEFAULT_AZURE_DEPLOYMENT
        elif not deployment:
            deployment = DEFAULT_AZURE_DEPLOYMENT
        
        # Add details to result
        result["details"]["api_key_present"] = bool(api_key)
        result["details"]["endpoint_present"] = bool(endpoint)
        result["details"]["deployment"] = deployment
        
        if not api_key or not endpoint:
            result["status"] = "MISSING_CREDENTIALS"
            result["error"] = "API key or endpoint not found"
            return result
        
        # Make a simple test call
        text, status = azure_openai_completion(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, Azure OpenAI is working!' if you can see this message.",
            max_tokens=50,
            temperature=0.7,
            deployment_name=deployment,
            app=app
        )
        
        if status == "SUCCESS" and text:
            result["status"] = "SUCCESS"
            result["details"]["response"] = text
        else:
            result["status"] = "ERROR"
            result["error"] = f"API call failed with status: {status}"
            
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        traceback.print_exc()
    
    return result
    
    if app:
        api_key = app.config.get('AZURE_OPENAI_KEY')
        endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
        deployment = app.config.get('AZURE_OPENAI_DEPLOYMENT')
    else:
        api_key = os.getenv("AZURE_OPENAI_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    if not deployment and endpoint:
        deployment = extract_deployment_from_endpoint(endpoint)
    
    result["deployment"] = deployment
    result["endpoint"] = endpoint
    
    if not api_key or not endpoint:
        result["status"] = "MISSING_CONFIG"
        result["error"] = "API key or endpoint not configured"
        return result
    
    # Make a simple test request
    try:
        text, status = azure_openai_completion(
            system_prompt="You are a test assistant.",
            user_prompt="Reply with 'Connection successful' if you can read this.",
            max_tokens=20,
            temperature=0.7,
            deployment_name=deployment
        )
        
        if text:
            result["status"] = "SUCCESS"
            result["response_sample"] = text[:100] + "..." if len(text) > 100 else text
        else:
            result["status"] = "API_ERROR"
            result["error"] = status
    except Exception as e:
        result["status"] = "EXCEPTION"
        result["error"] = str(e)
    
    return result