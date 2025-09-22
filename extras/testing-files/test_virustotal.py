#!/usr/bin/env python3
"""
Test script to verify VirusTotal API integration
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.insert(0, '/home/runner/work/CyberVantage/CyberVantage')

from pyFunctions.threat_intelligence import ThreatIntelligence

# Load environment variables
load_dotenv()

def test_virustotal_api():
    """Test VirusTotal API functionality"""
    print("=== VirusTotal API Test ===")
    
    # Check environment variable
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    print(f"API Key configured: {'Yes' if api_key and api_key != 'dummy_api_key_for_testing' else 'No (using dummy key)'}")
    
    # Initialize ThreatIntelligence
    ti = ThreatIntelligence()
    
    # Test API connection
    print("\n1. Testing API connection...")
    connection_result = ti.test_api_connection()
    print(f"Connection result: {json.dumps(connection_result, indent=2)}")
    
    # Test with a safe URL (using dummy data since we don't have real API key)
    if api_key and api_key != 'dummy_api_key_for_testing':
        print("\n2. Testing URL scan...")
        test_url = "https://www.google.com"
        scan_result = ti.scan_url(test_url)
        print(f"Scan result: {json.dumps(scan_result, indent=2)}")
    else:
        print("\n2. Skipping URL scan (no real API key)")
        print("To test with real VirusTotal API:")
        print("1. Get your API key from https://www.virustotal.com/gui/my-apikey")
        print("2. Set VIRUSTOTAL_API_KEY in your .env file")
        
        # Test the URL formatting logic with mock data
        print("\n3. Testing URL formatting logic...")
        mock_vt_response = {
            "data": {
                "id": "test-analysis-id",
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
                        "Google Safebrowsing": {"category": "harmless", "result": "clean", "method": "blacklist", "engine_name": "Google Safebrowsing"}
                    }
                }
            }
        }
        
        formatted_result = ti._format_url_result(mock_vt_response, "https://example.com")
        print(f"Formatted result: {json.dumps(formatted_result, indent=2)}")

if __name__ == "__main__":
    test_virustotal_api()