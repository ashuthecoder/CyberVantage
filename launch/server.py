#!/usr/bin/env python3
import os, requests, subprocess, json
from flask import Flask, request, jsonify

app = Flask(__name__)
GOPHISH_KEY = os.getenv("GOPHISH_API_KEY")

def latest_template_id():
    url = f"http://localhost:3333/api/templates?api_key={GOPHISH_KEY}"
    return requests.get(url, timeout=5).json()[-1]["id"]

def group_id():
    url = f"http://localhost:3333/api/groups?api_key={GOPHISH_KEY}"
    gs = requests.get(url, timeout=5).json()
    if gs: return gs[0]["id"]
    raise RuntimeError("Create a Group with at least your address first.")

def sending_profile_id():
    url = f"http://localhost:3333/api/smtp?api_key={GOPHISH_KEY}"
    return requests.get(url, timeout=5).json()[0]["id"]

@app.post("/launch")
def launch():
    campaign = {
        "name": "Local Demo",
        "template": {"id": latest_template_id()},
        "groups": [{"id": group_id()}],
        "smtp": {"id": sending_profile_id()}
    }
    url = f"http://localhost:3333/api/campaigns?api_key={GOPHISH_KEY}"
    requests.post(url, json=campaign, timeout=5)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5000)
