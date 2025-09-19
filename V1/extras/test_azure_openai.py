import os
import sys
import json
import time
import traceback
import uuid
from typing import Optional, List

import requests
from dotenv import load_dotenv


def get_env(name: str, fallback_names: Optional[List[str]] = None) -> Optional[str]:
    """Get env var by name; if not found, try fallbacks."""
    if fallback_names is None:
        fallback_names = []
    val = os.getenv(name)
    if val:
        return val
    for fb in fallback_names:
        v = os.getenv(fb)
        if v:
            print(f"[env] Using fallback {fb} for {name}")
            return v
    return None


def mask(s: Optional[str], show: int = 4) -> str:
    if not s:
        return "<empty>"
    if len(s) <= show * 2:
        return (s[0] if s else "") + "…" * 3
    return f"{s[:show]}…{s[-show:]}"


def main():
    load_dotenv()

    api_key = get_env("AZURE_OPENAI_KEY")
    # Accept both correct and misspelled endpoint names
    endpoint = get_env("AZURE_OPENAI_ENDPOINT", ["AUZRE_OPENAI_ENDPOINT"])  # typo fallback

    print("[diag] AZURE_OPENAI_KEY:", mask(api_key))
    print("[diag] AZURE_OPENAI_ENDPOINT:", endpoint or "<not set>")

    if not api_key:
        print("FAIL: AZURE_OPENAI_KEY is not set")
        return 2
    if not endpoint:
        print("FAIL: AZURE_OPENAI_ENDPOINT/AUZRE_OPENAI_ENDPOINT is not set")
        return 2

    # --- Prompt sources ---
    # Priority: CLI arg > AZURE_TEST_PROMPT env > default
    user_prompt = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not user_prompt:
        user_prompt = os.getenv("AZURE_TEST_PROMPT", "Reply with OK.")
    system_prompt = os.getenv("AZURE_TEST_SYSTEM", "You are a sanity check bot.")

    print("[diag] System prompt:", system_prompt)
    print("[diag] User prompt:", user_prompt)

    # If user pasted full chat completions URL, use as-is; else append a reasonable default path
    url = endpoint
    if not any(p in endpoint for p in ("/chat/completions", "/completions")):
        # Heuristic default path — adjust to your deployment
        if endpoint.endswith('/'):
            url = endpoint + "openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-08-01-preview"
        else:
            url = endpoint + "/openai/deployments/gpt-4o-mini/chat/completions?api-version=2024-08-01-preview"
        print("[diag] Normalized URL:", url)

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
        # helpful for tracing in Azure
        "x-ms-client-request-id": str(uuid.uuid4()),
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Small max_tokens to keep it cheap and quick
        "max_tokens": 10,
    }

    print("[http] POST", url)
    try:
        t0 = time.time()
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        dt = time.time() - t0
        print(f"[http] status={resp.status_code} time={dt:.2f}s")

        if resp.status_code == 200:
            data = resp.json()
            # Try to extract a small snippet for confirmation
            content = None
            try:
                choices = data.get("choices") or []
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content")
            except Exception:
                pass
            print("PASS: Received response. Snippet:", (content[:100] + "…") if isinstance(content, str) else str(data)[:120] + "…")
            return 0
        else:
            # Helpful diagnostics for common errors
            txt = None
            try:
                txt = resp.text
            except Exception:
                pass
            print("FAIL:", resp.status_code, txt)
            if resp.status_code in (401, 403):
                print("Hint: Check AZURE_OPENAI_KEY and that you're using the correct header name 'api-key'.")
            if resp.status_code == 404:
                print("Hint: Check the deployment name and region endpoint. The URL path must include /openai/deployments/<name>/chat/completions?api-version=…")
            if resp.status_code == 429:
                print("Hint: You're rate limited. Retry after a short delay or reduce request rate.")
            if resp.status_code >= 500:
                print("Hint: Service issue or incorrect region. Try again later or verify the endpoint.")
            return 1
    except requests.exceptions.Timeout:
        print("FAIL: Request timed out. Check network/endpoint accessibility.")
        return 3
    except Exception as e:
        print("FAIL: Exception during request:", e)
        traceback.print_exc()
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
