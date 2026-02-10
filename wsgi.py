def handler(event, context):
"""Vercel WSGI entry point."""
from main import app

# Vercel looks for an 'app' or 'application' variable
application = app
