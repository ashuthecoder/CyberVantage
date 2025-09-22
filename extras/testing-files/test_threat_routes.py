#!/usr/bin/env python3
"""
Simple test for the threat intelligence class only
"""
import sys
import json
sys.path.insert(0, '/home/runner/work/CyberVantage/CyberVantage')

# Test the ThreatIntelligence class directly
import os
import requests
import hashlib
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Mock the logger to avoid import issues
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def exception(self, msg): print(f"EXCEPTION: {msg}")

# Copy the ThreatIntelligence class locally to test
class ThreatIntelligence:
    """Test version of ThreatIntelligence class"""
    def __init__(self, api_key: str = None):
        """Initialize with API key from parameters or environment"""
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        self.logger = MockLogger()
        if not self.api_key:
            self.logger.warning("VirusTotal API key not found. Please add VIRUSTOTAL_API_KEY to your .env file")
        
        self.base_url = 'https://www.virustotal.com/api/v3/'
        self.headers = {
            'x-apikey': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Cache to store recent results
        self.cache = {}
        self.scan_history = []
    
    def _format_url_result(self, vt_result, url):
        """Format the VirusTotal URL result into a standardized format"""
        try:
            data = vt_result.get('data', {})
            attributes = data.get('attributes', {})
            stats = attributes.get('stats', {})
            
            # Handle different response formats based on analysis status
            status = attributes.get('status', 'unknown')
            
            if status == 'queued':
                return {
                    "resource": url,
                    "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "permalink": f"https://www.virustotal.com/gui/url/{hashlib.sha256(url.encode()).hexdigest()}/detection",
                    "positives": 0,
                    "total": 0,
                    "status": "queued",
                    "message": "URL is queued for analysis. Please try again in a few moments.",
                    "scans": {}
                }
            
            # For completed analysis
            analysis_date = attributes.get('date', datetime.now().timestamp())
            if isinstance(analysis_date, (int, float)):
                scan_date = datetime.fromtimestamp(analysis_date).strftime("%Y-%m-%d %H:%M:%S")
            else:
                scan_date = str(analysis_date)
            
            # Calculate URL ID for permalink
            url_id = data.get('id') or hashlib.sha256(url.encode()).hexdigest()
            
            return {
                "resource": url,
                "scan_date": scan_date,
                "permalink": f"https://www.virustotal.com/gui/url/{url_id}/detection",
                "positives": stats.get('malicious', 0),
                "total": sum(stats.values()) if stats else 0,
                "status": status,
                "harmless": stats.get('harmless', 0),
                "suspicious": stats.get('suspicious', 0),
                "undetected": stats.get('undetected', 0),
                "timeout": stats.get('timeout', 0),
                "scans": attributes.get('results', {})
            }
        except Exception as e:
            self.logger.exception(f"Error formatting URL result: {str(e)}")
            return {
                "error": "Failed to process scan results", 
                "raw": vt_result,
                "resource": url,
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "positives": 0,
                "total": 0
            }

def test_threat_intelligence_directly():
    """Test ThreatIntelligence class directly"""
    print("=== Testing ThreatIntelligence Class ===")
    
    # Test with dummy API key
    ti = ThreatIntelligence("test_api_key")
    
    # Test URL validation and processing
    print("\n1. Testing URL validation...")
    test_urls = [
        "google.com",
        "http://example.com", 
        "https://malicious-site.com",
        "not-a-url"
    ]
    
    for url in test_urls:
        # This will add http:// prefix if needed
        processed_url = url if url.startswith(('http://', 'https://')) else 'http://' + url
        print(f"Original: {url} -> Processed: {processed_url}")
    
    print("\n2. Testing URL result formatting...")
    # Test the URL formatting logic with mock data
    mock_vt_response = {
        "data": {
            "id": "test-analysis-id-12345",
            "attributes": {
                "status": "completed",
                "date": 1699123456,
                "stats": {
                    "harmless": 75,
                    "malicious": 2,
                    "suspicious": 1,
                    "undetected": 5,
                    "timeout": 0
                },
                "results": {
                    "Kaspersky": {"category": "harmless", "result": "clean", "method": "blacklist", "engine_name": "Kaspersky"},
                    "Google Safebrowsing": {"category": "harmless", "result": "clean", "method": "blacklist", "engine_name": "Google Safebrowsing"},
                    "Fortinet": {"category": "malicious", "result": "Phishing", "method": "blacklist", "engine_name": "Fortinet"},
                    "ESET": {"category": "malicious", "result": "HTML/Phishing.Gen", "method": "blacklist", "engine_name": "ESET"}
                }
            }
        }
    }
    
    formatted_result = ti._format_url_result(mock_vt_response, "https://suspicious-site.com")
    print(f"Formatted result: {json.dumps(formatted_result, indent=2)}")
    
    # Test queued status
    print("\n3. Testing queued status formatting...")
    mock_queued_response = {
        "data": {
            "id": "queued-analysis-id",
            "attributes": {
                "status": "queued"
            }
        }
    }
    
    queued_result = ti._format_url_result(mock_queued_response, "https://new-url.com")
    print(f"Queued result: {json.dumps(queued_result, indent=2)}")
    
    print("\n4. Testing environment variable reading...")
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    print(f"API Key from env: {'[CONFIGURED]' if api_key and api_key != 'dummy_api_key_for_testing' else '[NOT CONFIGURED]'}")

if __name__ == "__main__":
    test_threat_intelligence_directly()