"""
Email Generation Module - Gemini primary, Azure OpenAI fallback

This module handles AI-powered email generation for security training simulations
and evaluation of user explanations about phishing emails.
"""

import random
import traceback
import datetime
import re
import json
import os
import time

from pathlib import Path

# =============================================================================
# INITIALIZATION AND IMPORTS
# =============================================================================

# Import API logging functions with fallback
try:
    from .api_logging import log_api_request, check_rate_limit, get_cached_or_generate, create_cache_key, get_log_dir
except ImportError:
    # Create dummy functions if import fails
    def log_api_request(*args, **kwargs): pass
    def check_rate_limit(): return True
    def get_cached_or_generate(key, func, *args, **kwargs): return func(*args, **kwargs)
    def create_cache_key(prefix, content): return f"{prefix}_{hash(content)}"
    def get_log_dir(): return None

# Import AI provider with fallback support
try:
    from .ai_provider import (
        ai_completion_with_fallback,
        ai_chat_completion_with_fallback,
        extract_text_from_ai_response,
        get_provider_status
    )
    AI_PROVIDER_AVAILABLE = True
except ImportError:
    AI_PROVIDER_AVAILABLE = False
    def ai_completion_with_fallback(*args, **kwargs): return None, "IMPORT_ERROR", "none"
    def ai_chat_completion_with_fallback(*args, **kwargs): return None, "IMPORT_ERROR", "none"
    def extract_text_from_ai_response(*args, **kwargs): return ""
    def get_provider_status(): return {}

# Import Google Generative AI (Gemini) with fallback
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# Import template email fallback
try:
    from .template_emails import get_template_email
except ImportError:
    def get_template_email():
        return {
            "sender": "security@company.com",
            "subject": "Security Training Email",
            "content": "<p>This is a template email for training purposes.</p>",
            "is_spam": False
        }

# Determine writable log directory (may be None on serverless)
LOG_DIR = get_log_dir()

# Gemini model configuration
# Default to a stable model with typically less restrictive preview quotas.
_DEPRECATED_GEMINI_MODELS = {
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "models/gemini-1.5-pro",
    "models/gemini-1.5-pro-latest",
}

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip()
if DEFAULT_GEMINI_MODEL in _DEPRECATED_GEMINI_MODELS:
    DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"

_raw_fallback_models = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-pro,gemini-2.0-flash").split(",")
    if m.strip()
]

# Remove deprecated entries and de-dupe while preserving order.
DEFAULT_GEMINI_FALLBACK_MODELS = []
for _m in _raw_fallback_models:
    if _m in _DEPRECATED_GEMINI_MODELS:
        continue
    if _m not in DEFAULT_GEMINI_FALLBACK_MODELS:
        DEFAULT_GEMINI_FALLBACK_MODELS.append(_m)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def log_api_key_info(app, call_count):
    """Log API key information for diagnostic purposes"""
    try:
        print(f"[GENERATE] Call #{call_count} API key check")
        
        azure_key = None
        azure_endpoint = None
        
        if app:
            azure_key = app.config.get('AZURE_OPENAI_KEY')
            azure_endpoint = app.config.get('AZURE_OPENAI_ENDPOINT')
        
        azure_status = "Available" if azure_key and azure_endpoint else "Not configured"
        
        print(f"[GENERATE] Azure OpenAI API key status: {azure_status}")
        
        # Log status to debug file if available
        if LOG_DIR:
            log_path = os.path.join(LOG_DIR, 'api_key_debug.log')
            with open(log_path, 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{timestamp} - Call #{call_count} - Azure: {azure_status}\n")
            
    except Exception as e:
        print(f"[GENERATE] Error logging API key info: {e}")

def result_has_valid_content(result):
    """Check if a result has valid content"""
    if not result:
        return False
    
    if isinstance(result, dict):
        content = result.get('content', '')
        sender = result.get('sender', '')
        subject = result.get('subject', '')
        
        return bool(content and content.strip() and sender and subject)
    
    return False

# =============================================================================
# EMAIL GENERATION ENTRY POINTS
# =============================================================================

def generate_ai_email(user_name, previous_responses, GOOGLE_API_KEY=None, genai=None, app=None):
    """Generate an AI email with robust error handling - Gemini primary, Azure fallback"""
    call_count = getattr(generate_ai_email, 'call_count', 0) + 1
    generate_ai_email.call_count = call_count
    
    print(f"[GENERATE] Starting email generation (call #{call_count})")
    log_api_key_info(app, call_count)
    
    # ── 1. Try Gemini (primary) ──────────────────────────────────────────
    gemini_key = GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key and GEMINI_AVAILABLE:
        try:
            print("[GENERATE] Attempting Gemini generation (primary)")
            result = multi_approach_generation_gemini(user_name, previous_responses, gemini_key)
            if result_has_valid_content(result):
                print("[GENERATE] Gemini generation succeeded")
                return result
            else:
                print("[GENERATE] Gemini generation returned empty result, falling back")
        except Exception as e:
            print(f"[GENERATE] Gemini error: {e}")
            log_api_request("generate_ai_email", 0, False, error=str(e), api_source="GEMINI")
    else:
        if not gemini_key:
            print("[GENERATE] No Gemini API key configured, skipping Gemini")
        if not GEMINI_AVAILABLE:
            print("[GENERATE] google-generativeai package not installed, skipping Gemini")

    # ── 2. Try Azure OpenAI (fallback) ───────────────────────────────────
    if AZURE_HELPERS_AVAILABLE:
        try:
            print("[GENERATE] Attempting Azure OpenAI generation (fallback)")
            result = multi_approach_generation_azure(user_name, previous_responses, app)
            if result_has_valid_content(result):
                print("[GENERATE] AI generation succeeded")
                return result
            else:
                print("[GENERATE] AI generation failed, falling back to template")
        except Exception as e:
            print(f"[GENERATE] AI error: {e}")
            log_api_request("generate_ai_email", 0, False, error=str(e), api_source="AI")
    
    # ── 3. Fallback to template email ────────────────────────────────────
    print("[GENERATE] Using template email fallback")
    return get_template_email()

def evaluate_explanation(
    email_content,
    is_spam,
    user_response,
    user_explanation,
    GOOGLE_API_KEY=None,
    genai=None,
    app=None,
    email_sender: str | None = None,
    email_subject: str | None = None,
    email_date: str | None = None,
):
    """Evaluate the user's explanation of why an email is phishing/legitimate - Gemini primary, Azure fallback"""
    try:
        print("[EVALUATE] Starting explanation evaluation")

        # Users view the email rendered in a sandbox; evaluate against what they can actually see.
        visible_text = _strip_html_to_user_visible_text(email_content or "", max_chars=2000)
        email_context = (
            f"Sender: {email_sender or '(unknown)'}\n"
            f"Subject: {email_subject or '(unknown)'}\n"
            f"Date: {email_date or '(unknown)'}\n\n"
            "Rendered email content (what the student saw):\n"
            f"{visible_text}\n"
        )
        
        # ── 1. Try Gemini (primary) ──────────────────────────────────────
        gemini_key = GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key and GEMINI_AVAILABLE:
            try:
                result = evaluate_with_gemini(email_context, is_spam, user_response, user_explanation, gemini_key)
                if result:
                    return result
            except Exception as e:
                print(f"[EVALUATE] Gemini error: {e}")
                log_api_request("evaluate_explanation", 0, False, error=str(e), api_source="GEMINI")

        # ── 2. Try Azure OpenAI (fallback) ───────────────────────────────
        if AZURE_HELPERS_AVAILABLE:
            try:
                result = evaluate_with_ai_fallback(email_context, is_spam, user_response, user_explanation, app)
                if result:
                    return result
            except Exception as e:
                print(f"[EVALUATE] AI error: {e}")
                log_api_request("evaluate_explanation", 0, False, error=str(e), api_source="AI")
        
        # Fallback evaluation
        print("[EVALUATE] Using fallback evaluation")
        return get_fallback_evaluation(is_spam, user_response)
        
    except Exception as e:
        print(f"[EVALUATE] Error in evaluate_explanation: {e}")
        traceback.print_exc()
        return get_fallback_evaluation(is_spam, user_response)


def _strip_html_to_user_visible_text(html: str, max_chars: int = 2000) -> str:
    """Convert HTML-ish email content into a user-visible plain-text summary.

    Phase 2 emails are rendered in an iframe sandbox, so users see the *rendered* email,
    not the raw HTML source. This helper prevents evaluation prompts from overfitting to
    HTML boilerplate (e.g., <!doctype html>). It's intentionally lightweight (no deps).
    """
    if not html:
        return ""

    text = html
    # Remove scripts/styles
    text = re.sub(r"<\s*(script|style)[^>]*>.*?<\s*/\s*\1\s*>", " ", text, flags=re.I | re.S)
    # Convert common block breaks into newlines
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<\s*/\s*(p|div|tr|li|h\d)\s*>", "\n", text, flags=re.I)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode a few common entities (avoid importing html module at top-level)
    try:
        import html as _html
        text = _html.unescape(text)
    except Exception:
        pass
    # Normalize whitespace
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[\t\f\v ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if max_chars and len(text) > max_chars:
        return text[:max_chars].rstrip() + "…"
    return text


_DEFAULT_MAJOR_COMPANIES = [
    "Apple", "Microsoft", "Alphabet (Google)", "Amazon", "NVIDIA", "Meta", "Tesla",
    "Samsung", "TSMC", "Intel", "IBM", "Oracle", "Cisco", "SAP", "Sony", "Panasonic",
    "Dell Technologies", "HP", "Lenovo", "ASUS", "Acer", "Qualcomm", "Broadcom", "AMD",
    "Arm", "Siemens", "Bosch", "Philips", "LG", "Xiaomi", "ByteDance", "Tencent",
    "Alibaba", "Baidu", "Huawei", "Netflix", "Adobe", "Salesforce", "ServiceNow",
    "Palantir", "Snowflake", "Shopify", "Uber", "Airbnb", "PayPal", "Block", "Visa",
    "Mastercard", "American Express", "JPMorgan Chase", "Bank of America", "Citigroup",
    "Wells Fargo", "Goldman Sachs", "Morgan Stanley", "HSBC", "Barclays", "Deutsche Bank",
    "BNP Paribas", "Santander", "UBS", "Credit Suisse", "ING", "UniCredit", "Intesa Sanpaolo",
    "Royal Bank of Canada", "TD Bank", "Scotiabank", "ANZ", "Westpac", "Commonwealth Bank",
    "ICBC", "China Construction Bank", "Bank of China", "Agricultural Bank of China",
    "HDFC Bank", "ICICI Bank", "State Bank of India",
    "Walmart", "Costco", "Target", "Home Depot", "Lowe's", "IKEA", "Carrefour", "Tesco",
    "Ahold Delhaize", "Kroger", "Aldi", "Lidl",
    "ExxonMobil", "Chevron", "Shell", "BP", "TotalEnergies", "Saudi Aramco", "PetroChina",
    "Gazprom", "Equinor",
    "Toyota", "Volkswagen", "BMW", "Mercedes-Benz", "Honda", "Ford", "General Motors",
    "Stellantis", "Hyundai", "Kia", "Renault", "Nissan", "Volvo", "Geely", "BYD",
    "Boeing", "Airbus", "Lockheed Martin", "Northrop Grumman", "Raytheon", "BAE Systems",
    "SpaceX",
    "United Airlines", "Delta Air Lines", "American Airlines", "Lufthansa", "Air France-KLM",
    "Emirates", "Singapore Airlines", "Qantas",
    "FedEx", "UPS", "DHL", "Maersk", "MSC", "DP World",
    "Coca-Cola", "PepsiCo", "Nestlé", "Unilever", "Procter & Gamble", "Danone", "Mondelez",
    "Kraft Heinz", "Mars", "AB InBev", "Heineken", "Diageo",
    "McDonald's", "Starbucks", "KFC", "Burger King", "Subway", "Domino's",
    "Pfizer", "Johnson & Johnson", "Merck", "Novartis", "Roche", "Sanofi", "AstraZeneca",
    "GSK", "Bayer", "AbbVie", "Bristol Myers Squibb", "Amgen", "Eli Lilly", "Moderna",
    "Takeda", "Novo Nordisk", "CSL", "Thermo Fisher Scientific", "Siemens Healthineers",
    "Medtronic", "Stryker",
    "UnitedHealth", "CVS Health", "Cigna", "Anthem (Elevance)", "Kaiser Permanente",
    "Allianz", "AXA", "Zurich Insurance", "Prudential", "MetLife",
    "ArcelorMittal", "Rio Tinto", "BHP", "Vale", "Glencore",
    "LVMH", "Kering", "Hermès", "Nike", "Adidas", "Puma", "Inditex (Zara)", "H&M",
    "Rolex", "Swatch Group",
    "Comcast", "Disney", "Warner Bros. Discovery", "BBC", "Spotify",
    "Accenture", "Deloitte", "PwC", "EY", "KPMG", "Capgemini", "Tata Consultancy Services",
    "Infosys", "Wipro", "Cognizant",
    "OpenAI", "Anthropic",
]


def _load_major_companies() -> list:
    path = Path(__file__).resolve().parent.parent / "config" / "top_companies.json"
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and all(isinstance(x, str) for x in data) and len(data) >= 50:
                return data
    except Exception:
        pass
    return _DEFAULT_MAJOR_COMPANIES


_MAJOR_COMPANIES = _load_major_companies()


def _company_to_domain_hint(company_name: str) -> str:
    """Create a safe, non-realistic but plausible domain hint using .example."""
    base = (company_name or "company").lower()
    base = re.sub(r"\(.*?\)", "", base)  # remove parentheticals
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    base = re.sub(r"-+", "-", base)
    if not base:
        base = "company"
    # Keep it short-ish
    base = base[:40].strip("-")
    return f"{base}.example"

# =============================================================================
# GEMINI IMPLEMENTATION
# =============================================================================

# If Gemini quota/daily limit is hit, avoid hammering the API on subsequent calls.
_GEMINI_QUOTA_EXHAUSTED_UNTIL = None

def _configure_gemini(api_key):
    """Configure the Gemini SDK with the provided API key."""
    import google.generativeai as _genai
    _genai.configure(api_key=api_key)
    return _genai


def _is_gemini_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(term in msg for term in [
        "resource_exhausted",
        "quota",
        "daily",
        "limit",
        "rate limit",
        "too many requests",
        "429",
    ])


def _is_gemini_invalid_model_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(term in msg for term in [
        "model not found",
        "not found",
        "unknown model",
        "does not exist",
        "deprecated",
        "invalid argument",
    ]) and "quota" not in msg

def _call_gemini_with_retry(api_key, prompt, max_attempts=3, initial_delay=0.5):
    """Call Gemini API with retry logic and model fallback."""
    global _GEMINI_QUOTA_EXHAUSTED_UNTIL

    # If we recently hit a quota/daily-limit error, skip Gemini to avoid wasting calls.
    try:
        if _GEMINI_QUOTA_EXHAUSTED_UNTIL is not None:
            now_ts = time.time()
            if now_ts < _GEMINI_QUOTA_EXHAUSTED_UNTIL:
                remaining = int(_GEMINI_QUOTA_EXHAUSTED_UNTIL - now_ts)
                print(f"[GEMINI] Skipping Gemini due to recent quota exhaustion (cooldown {remaining}s remaining)")
                return None
    except Exception:
        # If anything goes wrong, don't block calls.
        _GEMINI_QUOTA_EXHAUSTED_UNTIL = None

    _genai = _configure_gemini(api_key)

    models_to_try = []
    for _m in ([DEFAULT_GEMINI_MODEL] + DEFAULT_GEMINI_FALLBACK_MODELS):
        if _m and _m not in models_to_try:
            models_to_try.append(_m)

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    for model_name in models_to_try:
        for attempt in range(max_attempts):
            try:
                # Local per-minute limiter to avoid accidental retry storms.
                if not check_rate_limit():
                    log_api_request(
                        "gemini_generate_content",
                        len(prompt) if prompt else 0,
                        False,
                        error="Local rate limiter blocked Gemini call",
                        fallback_reason="local_rate_limited",
                        model_used=model_name,
                        api_source="GEMINI",
                    )
                    return None

                print(f"[GEMINI] Attempt {attempt + 1}/{max_attempts} with {model_name}")
                model = _genai.GenerativeModel(model_name, safety_settings=safety_settings)
                response = model.generate_content(prompt)

                if hasattr(response, 'text') and response.text and response.text.strip():
                    print(f"[GEMINI] Success with {model_name}")
                    log_api_request(
                        "gemini_generate_content",
                        len(prompt) if prompt else 0,
                        True,
                        response_length=len(response.text),
                        model_used=model_name,
                        api_source="GEMINI",
                    )
                    return response.text
            except Exception as e:
                print(f"[GEMINI] Error with {model_name} attempt {attempt + 1}: {e}")
                # If we hit a quota/daily-limit error, do NOT keep retrying (it just burns more requests).
                if _is_gemini_quota_error(e):
                    # Cool down until next local midnight (or a configurable minimum cooldown),
                    # so the app doesn't keep retrying Gemini on every request.
                    try:
                        cooldown_seconds = int(os.getenv("GEMINI_QUOTA_COOLDOWN_SECONDS", "21600"))  # 6h
                        now = datetime.datetime.now()
                        next_midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                        until_midnight = max(0, int((next_midnight - now).total_seconds()))
                        _GEMINI_QUOTA_EXHAUSTED_UNTIL = time.time() + min(until_midnight, cooldown_seconds)
                    except Exception:
                        _GEMINI_QUOTA_EXHAUSTED_UNTIL = time.time() + 21600

                    log_api_request(
                        "gemini_generate_content",
                        len(prompt) if prompt else 0,
                        False,
                        error=str(e),
                        fallback_reason="quota_exhausted",
                        model_used=model_name,
                        api_source="GEMINI",
                    )
                    return None

                # If the model is invalid/deprecated, skip retries on it and try the next model in the list.
                if _is_gemini_invalid_model_error(e):
                    log_api_request(
                        "gemini_generate_content",
                        len(prompt) if prompt else 0,
                        False,
                        error=str(e),
                        fallback_reason="invalid_model",
                        model_used=model_name,
                        api_source="GEMINI",
                    )
                    break

                log_api_request(
                    "gemini_generate_content",
                    len(prompt) if prompt else 0,
                    False,
                    error=str(e),
                    fallback_reason="exception",
                    model_used=model_name,
                    api_source="GEMINI",
                )

                if attempt < max_attempts - 1:
                    time.sleep(initial_delay * (2 ** attempt))

    return None


def multi_approach_generation_gemini(user_name, previous_responses, api_key):
    """Generate email using Gemini with multiple prompt approaches."""
    print("[GEMINI] Starting multi-approach generation")

    approaches = [
        "Generate a realistic training email (either phishing or legitimate) for cybersecurity education.",
        "Create a simulated email for security awareness training purposes.",
        "Produce an educational email example for phishing detection training."
    ]

    for i, base_prompt in enumerate(approaches):
        try:
            prompt = build_generation_prompt(base_prompt, user_name, previous_responses)
            text = _call_gemini_with_retry(api_key, prompt)
            if text:
                parsed = parse_email_response(text)
                if parsed:
                    parsed = _sanitize_generated_email(parsed)
                if parsed and result_has_valid_content(parsed):
                    print(f"[GEMINI] Success with approach {i + 1}")
                    return parsed
        except Exception as e:
            print(f"[GEMINI] Error with approach {i + 1}: {e}")
            continue

    print("[GEMINI] All approaches failed")
    return None


def evaluate_with_gemini(email_context, is_spam, user_response, user_explanation, api_key):
    """Evaluate user explanation using Gemini."""
    correct_answer = "phishing" if is_spam else "legitimate"
    user_answer = "phishing" if user_response else "legitimate"

    prompt = f"""You are a cybersecurity expert evaluating a student's analysis of an email for phishing detection training.

Important constraints (must follow):
- The student saw the email rendered in a sandbox. Do NOT reference raw HTML/source code (e.g., doctype/html/head tags) and do NOT mention that the email "starts with <!DOCTYPE".
- Only reference indicators visible in the rendered email: sender address/domain, display name, subject, wording, requests, link destinations, tone, and inconsistencies.
- If you are tempted to mention HTML/source code, replace it with a visible indicator instead.

Email (student-visible context):
{str(email_context)[:1800]}

Correct Classification: {correct_answer}
User Classification: {user_answer}
User Explanation: {user_explanation}

Evaluate the student's explanation considering:
1. Accuracy (40%): Did they correctly identify the email type?
2. Analysis Quality (30%): How well did they explain their reasoning?
3. Security Awareness (20%): Did they identify relevant security indicators?
4. Learning Progress (10%): Evidence of cybersecurity understanding

Provide detailed, constructive feedback.

Format as JSON: {{"feedback": "detailed HTML feedback", "score": 7}}"""

    text = _call_gemini_with_retry(api_key, prompt)
    if text:
        text = clean_html_code_blocks(text)
        result = _parse_ai_evaluation_result(text)
        if result and "feedback" in result and "score" in result:
            result["feedback"] = _sanitize_phase2_feedback(clean_html_code_blocks(result["feedback"]))
            return result

        extracted_score = extract_score_from_feedback(text, is_spam, user_response)
        return {"feedback": _sanitize_phase2_feedback(text), "score": extracted_score}

    return None

# =============================================================================
# AZURE OPENAI IMPLEMENTATION
# =============================================================================

def multi_approach_generation_with_fallback(user_name, previous_responses, app):
    """Generate email using AI with multiple prompt approaches and automatic fallback"""
    print("[AI] Starting multi-approach generation with fallback")
    
    approaches = [
        "Generate a realistic training email (either phishing or legitimate) for cybersecurity education.",
        "Create a simulated email for security awareness training purposes.",
        "Produce an educational email example for phishing detection training."
    ]
    
    for i, base_prompt in enumerate(approaches):
        try:
            print(f"[AI] Trying approach {i+1}: {base_prompt[:50]}...")
            
            # Build full prompt
            prompt = build_generation_prompt(base_prompt, user_name, previous_responses)
            
            # Call AI with automatic fallback
            response, status, provider = ai_chat_completion_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                app=app,
                max_tokens=512,
                temperature=0.7
            )
            
            if response and status == "SUCCESS":
                # Extract and parse response
                text_content = extract_text_from_ai_response(response, provider)
                if text_content:
                    parsed = parse_email_response(text_content)
                    if parsed:
                        parsed = _sanitize_generated_email(parsed)
                    if parsed and result_has_valid_content(parsed):
                        print(f"[AI] Success with approach {i+1} using provider: {provider}")
                        return parsed
            
            print(f"[AI] Approach {i+1} failed with status: {status}")
            
        except Exception as e:
            print(f"[AI] Error with approach {i+1}: {e}")
            continue
    
    print("[AI] All approaches failed")
    return None

def extract_score_from_feedback(feedback_text, is_spam, user_response):
    """Extract the actual score from AI feedback text that contains point breakdowns"""
    try:
        import re
        
        # Look for point patterns like "+3 points", "+0 points", etc.
        point_pattern = r'\(\+(\d+)\s+points?\)'
        matches = re.findall(point_pattern, feedback_text)
        
        if matches:
            # Sum all the points found
            total_points = sum(int(match) for match in matches)
            print(f"[EXTRACT_SCORE] Found point breakdown: {matches}, total: {total_points}")
            return total_points
        
        # Alternative pattern: look for "X points" without parentheses  
        alt_pattern = r'\+(\d+)\s+points?'
        alt_matches = re.findall(alt_pattern, feedback_text)
        
        if alt_matches:
            total_points = sum(int(match) for match in alt_matches)
            print(f"[EXTRACT_SCORE] Found alternative point breakdown: {alt_matches}, total: {total_points}")
            return total_points
        
        # Look for direct score mentions like "score: 7" or "Score: 7"
        score_pattern = r'score[:\s]+(\d+)'
        score_match = re.search(score_pattern, feedback_text, re.IGNORECASE)
        
        if score_match:
            score = int(score_match.group(1))
            print(f"[EXTRACT_SCORE] Found direct score mention: {score}")
            return score
        
        # Look for "X/10" pattern
        fraction_pattern = r'(\d+)/10'
        fraction_match = re.search(fraction_pattern, feedback_text)
        
        if fraction_match:
            score = int(fraction_match.group(1))
            print(f"[EXTRACT_SCORE] Found fraction score: {score}")
            return score
        
        # If no score found, use fallback logic
        print("[EXTRACT_SCORE] No score pattern found, using fallback logic")
        return 7 if user_response == is_spam else 3
        
    except Exception as e:
        print(f"[EXTRACT_SCORE] Error extracting score: {e}")
        # Return fallback score
        return 7 if user_response == is_spam else 3

def evaluate_with_ai_fallback(email_context, is_spam, user_response, user_explanation, app):
    """Evaluate user explanation using AI with automatic fallback"""
    try:
        print("[AI] Starting evaluation with fallback")
        
        # Build evaluation prompt
        correct_answer = "phishing" if is_spam else "legitimate"
        user_answer = "phishing" if user_response else "legitimate"
        
        prompt = f"""You are a cybersecurity expert evaluating a student's analysis of an email for phishing detection training.

    Important constraints (must follow):
    - The student saw the email rendered in a sandbox. Do NOT reference raw HTML/source code (e.g., doctype/html/head tags) and do NOT mention that the email "starts with <!DOCTYPE".
    - Only reference indicators visible in the rendered email: sender address/domain, display name, subject, wording, requests, link destinations, tone, and inconsistencies.

    Email (student-visible context):
    {str(email_context)[:1800]}

Correct Classification: {correct_answer}
User Classification: {user_answer}
User Explanation: {user_explanation}

Evaluate the student's explanation considering these factors:

1. **Accuracy (40%)**: Did they correctly identify the email type?
2. **Analysis Quality (30%)**: How well did they explain their reasoning?
3. **Security Awareness (20%)**: Did they identify relevant security indicators?
4. **Learning Progress (10%)**: Evidence of cybersecurity understanding

Score calculation:
- Base score starts at 5/10
- Correct classification: +2-3 points
- Good reasoning/explanation: +1-2 points  
- Identification of specific indicators: +1-2 points
- Demonstration of security knowledge: +0-1 points
- Incorrect classification but good reasoning: partial credit possible

Provide detailed, constructive feedback that helps them improve their phishing detection skills.

Format as JSON: {{"feedback": "detailed HTML feedback with specific recommendations", "score": 7}}"""
        
        # Call AI with automatic fallback
        response, status, provider = ai_chat_completion_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            app=app,
            max_tokens=1024,  # Increased from 256 to prevent feedback truncation
            temperature=0.3
        )
        
        if response and status == "SUCCESS":
            text_content = extract_text_from_ai_response(response, provider)
            if text_content:
                # Clean HTML code blocks from AI response
                text_content = clean_html_code_blocks(text_content)

                result = _parse_ai_evaluation_result(text_content)
                if result and "feedback" in result and "score" in result:
                    result["feedback"] = _sanitize_phase2_feedback(clean_html_code_blocks(result["feedback"]))
                    print(f"[AI] Evaluation successful using provider: {provider}")
                    return result

                # Fallback parsing - extract score from text content
                extracted_score = extract_score_from_feedback(text_content, is_spam, user_response)
                return {
                    "feedback": _sanitize_phase2_feedback(text_content),
                    "score": extracted_score
                }
        
        return None
        
    except Exception as e:
        print(f"[AI] Evaluation error: {e}")
        return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def build_generation_prompt(base_prompt, user_name, previous_responses):
    """Build a complete prompt for email generation"""
    import random
    
    # Add randomization to ensure uniqueness
    random_id = random.randint(10000, 99999)
    timestamp = datetime.datetime.now().strftime("%H%M%S")
    
    company_name = random.choice(_MAJOR_COMPANIES)
    company_domain = _company_to_domain_hint(company_name)
    ref_id = f"{random_id}-{timestamp}"

    prompt = f"""{base_prompt}

Scenario requirements:
- Create ONE realistic email (either phishing OR legitimate) themed around a major global company.
- Use this company for the scenario: {company_name}
- Use safe, non-real domains/links: base domains must end with .example (e.g., https://login.{company_domain}/...).
- Make the email unique for this request using seed/reference: {ref_id}
- Include the reference id exactly once in the subject OR as a small footer line (e.g., "Ref: {ref_id}"). It should look like a normal internal reference and not be a phishing tell by itself.
- Difficulty: adapt subtlety based on this performance context: {previous_responses}

Output format requirements:
- Output valid JSON only with keys: sender, subject, date, content, is_spam
- sender must look like an email address (e.g., security@{company_domain} or alerts@{company_domain})
- content must be an HTML *fragment* suitable for embedding inside an email body.
  - Do NOT include <!DOCTYPE>, <html>, <head>, or <body> tags.
  - Do NOT include <script>.
  - Basic tags like <p>, <strong>, <ul>, <li>, <a>, <table> are OK.

Training realism requirements:
- If is_spam=true (phishing): include realistic social engineering (urgency/authority), and at least 2 visible red flags the student can cite (e.g., mismatched link text vs href, odd sender subdomain, unusual request, threatening tone, grammar, attachment pressure).
- If is_spam=false (legitimate): make it professional, non-alarming, with safe CTA and no credential harvesting.
- Do NOT use the student's real name or personal details.

Generate the JSON now."""
    
    return prompt

def parse_email_response(text_content):
    """Parse email response from AI"""
    try:
        # Try to find JSON in the response
        json_start = text_content.find('{')
        json_end = text_content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text_content[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['sender', 'subject', 'content', 'is_spam']
            if all(field in parsed for field in required_fields):
                # Ensure date field
                if 'date' not in parsed:
                    parsed['date'] = datetime.datetime.now().strftime("%B %d, %Y")
                return _sanitize_generated_email(parsed)
        
        return None
        
    except Exception as e:
        print(f"[PARSE] Error parsing response: {e}")
        return None


def _sanitize_generated_email(email_data: dict) -> dict:
    """Harden generated email payloads for Phase 2 rendering.

    - Ensure `content` is an embeddable HTML fragment (no doctype/html/head/body wrappers).
    - Ensure links/senders use safe `.example` domains.
    """
    if not isinstance(email_data, dict):
        return email_data

    sanitized = dict(email_data)

    # Content
    content = sanitized.get("content") or ""
    content = clean_html_code_blocks(content)
    content = _sanitize_email_html_fragment(content)
    content = _sanitize_links_to_example_domains(content)
    sanitized["content"] = content

    # Sender
    sender = (sanitized.get("sender") or "").strip()
    sanitized["sender"] = _coerce_sender_to_example(sender)

    # Subject: keep as-is but trim whitespace
    if "subject" in sanitized and isinstance(sanitized["subject"], str):
        sanitized["subject"] = sanitized["subject"].strip()

    return sanitized


def _sanitize_email_html_fragment(html: str) -> str:
    if not html:
        return ""
    text = html
    # Remove full-document wrappers if the model included them.
    text = re.sub(r"<!\s*doctype[^>]*>", "", text, flags=re.I)
    text = re.sub(r"<\s*head[^>]*>.*?<\s*/\s*head\s*>", "", text, flags=re.I | re.S)
    text = re.sub(r"</?\s*html[^>]*>", "", text, flags=re.I)
    text = re.sub(r"</?\s*body[^>]*>", "", text, flags=re.I)
    # Strip scripts defensively.
    text = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.I | re.S)
    return text.strip()


def _force_example_domain(domain: str) -> str:
    d = (domain or "").strip().lower()
    d = d.split("/")[0]
    d = d.split(":")[0]
    if not d:
        return "training.example"
    if d.endswith(".example"):
        return d
    # Replace last label with `.example` when possible.
    if "." in d:
        parts = [p for p in d.split(".") if p]
        if len(parts) >= 2:
            return ".".join(parts[:-1] + ["example"])
    return f"{d}.example"


def _coerce_sender_to_example(sender: str) -> str:
    s = (sender or "").strip()
    if not s:
        return "notifications@training.example"

    # Extract email if wrapped like "Name <a@b.com>"
    m = re.search(r"<\s*([^>\s]+@[^>\s]+)\s*>", s)
    if m:
        s = m.group(1)

    if "@" not in s:
        # Not a valid-looking email; return a safe placeholder.
        return "notifications@training.example"

    local, domain = s.split("@", 1)
    local = re.sub(r"[^a-zA-Z0-9._%+-]+", "", local) or "notifications"
    return f"{local}@{_force_example_domain(domain)}"


def _sanitize_links_to_example_domains(html: str) -> str:
    """Rewrite http(s) links to `.example` domains (safe/non-realistic)."""
    if not html:
        return html
    try:
        from urllib.parse import urlsplit, urlunsplit
    except Exception:
        return html

    def _rewrite(match: re.Match) -> str:
        url = match.group(0)
        try:
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"}:
                return url
            netloc = parts.netloc
            if not netloc:
                return url
            if "@" in netloc:
                # userinfo@host
                userinfo, host = netloc.rsplit("@", 1)
                host = _force_example_domain(host)
                netloc2 = f"{userinfo}@{host}"
            else:
                netloc2 = _force_example_domain(netloc)
            return urlunsplit((parts.scheme, netloc2, parts.path, parts.query, parts.fragment))
        except Exception:
            return url

    return re.sub(r"https?://[^\s\"'<>]+", _rewrite, html)


def _sanitize_phase2_feedback(feedback: str) -> str:
    """Remove references to raw HTML/source code in Phase 2 feedback."""
    if not feedback:
        return feedback

    text = feedback
    invisible_markers = [
        r"<!\s*doctype",
        r"<\s*html\b",
        r"<\s*head\b",
        r"<\s*body\b",
        r"raw\s+html",
        r"source\s+code",
    ]
    if any(re.search(p, text, flags=re.I) for p in invisible_markers):
        # Replace paragraphs/lines that mention raw HTML/source code with a sandbox-appropriate note.
        replacement = (
            "<p><strong>Note:</strong> In this simulation, the email is rendered in a sandbox preview, "
            "so the underlying HTML markup isn’t shown. Focus on visible indicators like sender domain, link destination, "
            "wording, urgency, and the specific action requested.</p>"
        )
        inserted_note = False
        # HTML paragraph removal
        def _replace_para(match: re.Match) -> str:
            nonlocal inserted_note
            if not inserted_note:
                inserted_note = True
                return replacement
            return ""

        text = re.sub(
            r"(?is)<p>.*?(<!\s*doctype|raw\s+html|source\s+code).*?</p>",
            _replace_para,
            text,
        )
        # Plain-text line removal
        text = re.sub(
            r"(?im)^.*(<!\s*doctype|raw\s+html|source\s+code).*$\n?",
            "",
            text,
        )
        # Any remaining stray tag mentions
        text = re.sub(r"(?i)<!\s*doctype[^\n]*", "", text)
        text = re.sub(r"(?i)</?\s*(html|head|body)\b[^>]*>", "", text)

        if not inserted_note:
            # If we removed lines but didn't replace any HTML paragraph, prepend the note.
            text = replacement + "\n" + text

    return text

def clean_html_code_blocks(text):
    """
    Remove markdown code blocks (```html) from AI responses.
    This fixes the issue where AI returns HTML wrapped in markdown code blocks.
    """
    if not text:
        return text
    
    import re
    
    # Step 1: Handle complete text that is just a code block
    # Check for ```html ... ``` patterns that span the entire text
    html_block_pattern = r'^```html\s*\n?(.*?)\n?```\s*$'
    html_match = re.search(html_block_pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # Check for generic code blocks that span the entire text
    generic_block_pattern = r'^```\s*\n?(.*?)\n?```\s*$'
    generic_match = re.search(generic_block_pattern, text, flags=re.DOTALL)
    if generic_match:
        content = generic_match.group(1).strip()
        # Only remove code blocks if content clearly looks like HTML
        if (content.startswith('<') and content.endswith('>') and
            ('<h' in content.lower() or '<p' in content.lower() or '<div' in content.lower() or 
             '<strong' in content.lower() or '<ul' in content.lower() or '<li' in content.lower())):
            return content
    
    # Step 2: Handle embedded code blocks within text
    def is_html_content(content):
        """Check if content looks like HTML"""
        content = content.strip()
        return (content.startswith('<') and content.endswith('>') and
                ('<h' in content.lower() or '<p' in content.lower() or '<div' in content.lower() or 
                 '<strong' in content.lower() or '<ul' in content.lower() or '<li' in content.lower()))
    
    # Find and replace all ```html blocks (with proper closing)
    def replace_html_block(match):
        content = match.group(1).strip()
        if is_html_content(content):
            return content
        return match.group(0)  # Return original if not HTML
    
    # Pattern for ```html ... ``` anywhere in text
    text = re.sub(r'```html\s*\n?(.*?)\n?```', replace_html_block, text, flags=re.IGNORECASE | re.DOTALL)
    
    # Step 3: Handle malformed blocks (missing closing ```)
    def replace_malformed_block(match):
        content = match.group(1).strip()
        if is_html_content(content):
            return content
        return match.group(0)  # Return original if not HTML
    
    # Look for ```html at start of line or after whitespace, followed by HTML content
    # Stop at double newline, start of new sentence, or end of string
    text = re.sub(r'```html\s*\n?(.*?)(?=\n\s*\n|\n[A-Z]|$)', replace_malformed_block, text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()


def _strip_markdown_code_fences(text: str) -> str:
    """Return the first fenced block content if present, else return the original text."""
    if not text:
        return text

    import re

    # Prefer ```json ... ``` but accept any language tag.
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip()


def _parse_ai_evaluation_result(text: str):
    """Parse AI evaluation output into {'feedback': str, 'score': int}.

    The models sometimes return JSON wrapped in ```json fences, or JSON-like content
    where the feedback string contains raw newlines (invalid JSON). This parser is
    intentionally tolerant.
    """
    if not text:
        return None

    import re

    candidate = _strip_markdown_code_fences(text)

    # 1) Try strict JSON parsing on the full candidate.
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return _normalize_evaluation_dict(parsed)
    except Exception:
        pass

    # 2) Try strict JSON parsing on the first {...} block we can find.
    json_start = candidate.find('{')
    json_end = candidate.rfind('}') + 1
    if json_start >= 0 and json_end > json_start:
        json_str = candidate[json_start:json_end]
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict):
                return _normalize_evaluation_dict(parsed)
        except Exception:
            pass

    # 3) Tolerant extraction for JSON-like blobs with invalid string escaping.
    # Extract score first.
    score = None
    score_match = re.search(r'"score"\s*:\s*(\d+)', candidate)
    if score_match:
        try:
            score = int(score_match.group(1))
        except Exception:
            score = None

    # Extract feedback as everything between the feedback key and the score key.
    feedback = None
    feedback_key_pos = candidate.lower().find('"feedback"')
    score_key_pos = candidate.lower().find('"score"')
    if feedback_key_pos != -1 and score_key_pos != -1 and score_key_pos > feedback_key_pos:
        # Find the first quote after the ':' following "feedback".
        colon_pos = candidate.find(':', feedback_key_pos)
        if colon_pos != -1:
            first_quote = candidate.find('"', colon_pos)
            if first_quote != -1 and first_quote < score_key_pos:
                raw_feedback_region = candidate[first_quote + 1:score_key_pos]
                # Trim trailing characters like ", or whitespace before the next key.
                raw_feedback_region = raw_feedback_region.rstrip()
                raw_feedback_region = re.sub(r'\s*,\s*$', '', raw_feedback_region)
                # Remove a trailing quote if the model closed it right before the score key.
                raw_feedback_region = raw_feedback_region.rstrip('"')
                feedback = raw_feedback_region.strip()

    if feedback is not None and score is not None:
        return {"feedback": feedback, "score": score}

    return None


def _normalize_evaluation_dict(result: dict) -> dict:
    """Coerce score to int when possible and ensure feedback is a string."""
    if not isinstance(result, dict):
        return result

    normalized = dict(result)
    if "score" in normalized:
        try:
            normalized["score"] = int(normalized["score"])
        except Exception:
            pass
    if "feedback" in normalized and normalized["feedback"] is not None:
        normalized["feedback"] = str(normalized["feedback"])
    return normalized

def get_fallback_evaluation(is_spam, user_response):
    """Generate a dynamic evaluation when AI isn't available"""
    correct = (user_response == is_spam)
    
    # Base scoring - more nuanced than just 8 or 3
    if correct:
        # Correct answers get scores between 6-9 with some randomness for variety
        base_score = 7 + random.randint(0, 2)  # 7-9 range
        feedback = "<p>✓ <strong>Correct identification!</strong> You properly identified this email.</p>"
    else:
        # Incorrect answers get scores between 2-5 with some variation
        base_score = 3 + random.randint(0, 2)  # 3-5 range  
        feedback = "<p>✗ <strong>Incorrect identification.</strong> Review the email characteristics more carefully.</p>"
    
    # Add additional feedback based on email type
    if is_spam:
        if correct:
            feedback += """
            <p><strong>Good catch!</strong> This was indeed a phishing/spam email. Key indicators to look for in such emails include:</p>
            <ul>
                <li>Suspicious sender domains or mismatched addresses</li>
                <li>Urgency tactics or threats</li>
                <li>Requests for personal information or credentials</li>
                <li>Poor grammar or formatting</li>
                <li>Unexpected attachments or links</li>
            </ul>
            """
        else:
            feedback += """
            <p><strong>This was actually a phishing email.</strong> Here are some warning signs you might have missed:</p>
            <ul>
                <li>Check the sender's email address carefully</li>
                <li>Look for urgent language designed to make you act quickly</li>
                <li>Be suspicious of unexpected requests for information</li>
                <li>Verify independently before clicking any links</li>
            </ul>
            """
    else:
        if correct:
            feedback += """
            <p><strong>Well done!</strong> This was a legitimate email. Good signs that indicated authenticity might include:</p>
            <ul>
                <li>Sender from a recognized, legitimate domain</li>
                <li>Professional formatting and tone</li>
                <li>Reasonable requests appropriate to the context</li>
                <li>No urgent pressure tactics</li>
            </ul>
            """
        else:
            feedback += """
            <p><strong>This was actually a legitimate email.</strong> Consider these factors when evaluating emails:</p>
            <ul>
                <li>Verify the sender's domain and identity</li>
                <li>Consider if the request makes sense in context</li>
                <li>Look for signs of authenticity vs. deception</li>
                <li>When in doubt, verify through alternative means</li>
            </ul>
            """
    
    # Add general security tips
    feedback += """
    <p><strong>Remember:</strong> When in doubt about an email's authenticity, it's always better to verify through independent means before taking any action.</p>
    """
    
    return {
        "feedback": feedback,
        "score": base_score
    }