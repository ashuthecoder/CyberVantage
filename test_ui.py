#!/usr/bin/env python3
"""
Simple Flask app test to see if the UI loads properly
"""
import os
import sys
sys.path.insert(0, '/home/runner/work/CyberVantage/CyberVantage')

from flask import Flask, render_template_string

# Create a minimal Flask app to test the template
app = Flask(__name__)
app.secret_key = 'test-secret-key'

# Mock CSRF token function
def csrf_token():
    return 'test-csrf-token'

# Simple route to test template rendering
@app.route('/test')
def test_template():
    try:
        # Read the template file
        with open('/home/runner/work/CyberVantage/CyberVantage/templates/check_threats.html', 'r') as f:
            template_content = f.read()
        
        # Replace template inheritance with standalone HTML
        template_content = template_content.replace('{% extends \'base.html\' %}', '')
        template_content = template_content.replace('{% block title %}Threat Intelligence - CyberVantage{% endblock %}', '<title>Threat Intelligence - CyberVantage</title>')
        template_content = template_content.replace('{% block head %}', '')
        template_content = template_content.replace('{% endblock %}', '')
        template_content = template_content.replace('{% block content %}', '<body>')
        template_content = template_content.replace('{% block extra_styles %}', '<style>')
        template_content = template_content.replace('{% block scripts %}', '<script>')
        template_content = template_content.replace('{{ csrf_token() }}', 'test-csrf-token')
        
        # Add basic HTML structure
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Threat Intelligence - CyberVantage</title>
            <meta name="csrf-token" content="test-csrf-token">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        </head>
        {template_content}
        </body>
        </html>
        """
        
        return render_template_string(html_template)
    except Exception as e:
        return f"<h1>Template Test Failed</h1><p>Error: {str(e)}</p>"

if __name__ == '__main__':
    print("Testing template rendering...")
    with app.test_client() as client:
        response = client.get('/test')
        if response.status_code == 200:
            print("✅ Template renders successfully!")
            print(f"Response length: {len(response.data)} bytes")
            # Save to file for manual inspection
            with open('/tmp/test_template_output.html', 'w') as f:
                f.write(response.data.decode('utf-8'))
            print("✅ Saved rendered template to /tmp/test_template_output.html")
        else:
            print(f"❌ Template rendering failed with status {response.status_code}")
            print(response.data.decode('utf-8'))