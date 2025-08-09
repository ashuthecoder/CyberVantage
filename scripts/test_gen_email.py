#!/usr/bin/env python3
import os, json, openai, requests

openai.api_key = os.getenv("OPENAI_API_KEY")
GOPHISH_KEY = os.getenv("GOPHISH_API_KEY")
GOPHISH_URL = f"http://localhost:3333/api/templates?api_key={GOPHISH_KEY}"

prompt = (
  "Write a short, HTML-only phishing email aimed at university students. "
  "Theme: urgent password reset. Use a friendly but urgent tone, include a "
  "button that says 'Reset Now' linking to http://localhost:8000/educate.html."
)

html = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}]
)["choices"][0]["message"]["content"]

template = {
    "name": "AI Student Reset",
    "subject": "ACTION REQUIRED: University Password Reset",
    "html": html
}

r = requests.post(GOPHISH_URL, json=template, timeout=10)
r.raise_for_status()
print("📧  Template created in Gophish!")
