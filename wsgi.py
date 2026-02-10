"""
Vercel WSGI entry point
"""
from main import app

# Vercel looks for an 'app' or 'application' variable
application = app

# For Vercel serverless functions
def handler(event, context):
    return application
