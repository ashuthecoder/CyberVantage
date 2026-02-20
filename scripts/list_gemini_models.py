#!/usr/bin/env python3
"""List available Google Gemini (Generative AI) models using google-generativeai SDK.

Usage:
  - Ensure `GOOGLE_API_KEY` is set in your environment or in a .env file
  - Run: `python scripts/list_gemini_models.py`
  - Optional: `python scripts/list_gemini_models.py --json`

The script prints a concise table of model id, display name and description.
"""
from __future__ import annotations
import os
import sys
import json
import argparse
from textwrap import shorten

try:
    import google.generativeai as genai
except Exception as e:
    print("ERROR: google-generativeai package not available. Install with: pip install google-generativeai")
    raise

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv optional
    pass


def list_models(api_key: str | None = None) -> list:
    """Return list of available Gemini models via google-generativeai SDK."""
    if api_key:
        genai.configure(api_key=api_key)
    else:
        # If not provided, assume genai already configured or GOOGLE_API_KEY present in env
        env_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if env_key:
            genai.configure(api_key=env_key)
        else:
            raise RuntimeError("No API key provided and GOOGLE_API_KEY not set in environment")

    # SDK exposes `list_models()` which returns an iterable of model descriptions
    models = genai.list_models()
    # Normalize to plain dicts
    normalized = []
    for m in models:
        # m may be a simple dict-like object
        try:
            md = {k: getattr(m, k) for k in dir(m) if not k.startswith("_") and k.isidentifier()}
        except Exception:
            try:
                md = dict(m)
            except Exception:
                md = {"raw": str(m)}
        normalized.append(md)
    return normalized


def pretty_print(models: list, json_out: bool = False) -> None:
    if json_out:
        print(json.dumps(models, indent=2, default=str))
        return

    # Print table header
    print(f"Found {len(models)} models:\n")
    print(f"{'MODEL ID':40} {'DISPLAY NAME':30} {'DESCRIPTION'}")
    print('-' * 110)
    for m in models:
        # model id can be 'name' or 'model' or 'id'
        model_id = m.get('name') or m.get('model') or m.get('id') or m.get('model_name') or '<unknown>'
        display = m.get('displayName') or m.get('display_name') or m.get('title') or ''
        desc = m.get('description') or m.get('summary') or ''
        print(f"{model_id:40} {display[:30]:30} {shorten(desc, width=60, placeholder='...')}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="List available Google Gemini models (via google-generativeai)")
    p.add_argument('--api-key', '-k', help='Gemini / Google API key (overrides env GOOGLE_API_KEY)')
    p.add_argument('--json', action='store_true', help='Output raw JSON')
    args = p.parse_args(argv)

    try:
        models = list_models(api_key=args.api_key)
    except Exception as e:
        print(f"Error listing models: {e}")
        return 2

    pretty_print(models, json_out=args.json)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
