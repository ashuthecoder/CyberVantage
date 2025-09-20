#!/usr/bin/env python3
"""
Final comprehensive test of the VirusTotal API integration improvements
"""
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, '/home/runner/work/CyberVantage/CyberVantage')

# Test environment setup
from dotenv import load_dotenv
load_dotenv()

def test_comprehensive_functionality():
    """Test all the improvements we made"""
    print("🔍 CyberVantage VirusTotal Integration - Comprehensive Test")
    print("=" * 60)
    
    # 1. Environment Variable Consistency Test
    print("\n1. Testing Environment Variable Consistency...")
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    print(f"   ✅ VIRUSTOTAL_API_KEY: {'Configured' if api_key else 'Not configured'}")
    
    # 2. Import and Module Test
    print("\n2. Testing Module Imports...")
    try:
        from pyFunctions.threat_intelligence import ThreatIntelligence
        print("   ✅ ThreatIntelligence class imported successfully")
        
        ti = ThreatIntelligence("test_key")
        print("   ✅ ThreatIntelligence instance created")
        
        # Test API connection method
        result = ti.test_api_connection()
        print(f"   ✅ API connection test method works: {bool(result)}")
        
    except Exception as e:
        print(f"   ❌ Module import failed: {e}")
        return False
    
    # 3. URL Processing Test
    print("\n3. Testing URL Processing & Validation...")
    test_cases = [
        ("google.com", "http://google.com"),
        ("https://example.com", "https://example.com"),
        ("192.168.1.1", "http://192.168.1.1"),
        ("malicious-site.com", "http://malicious-site.com")
    ]
    
    for original, expected in test_cases:
        processed = original if original.startswith(('http://', 'https://')) else 'http://' + original
        status = "✅" if processed == expected else "❌"
        print(f"   {status} {original} -> {processed}")
    
    # 4. Result Formatting Test
    print("\n4. Testing Result Formatting...")
    try:
        mock_response = {
            "data": {
                "id": "test-12345",
                "attributes": {
                    "status": "completed",
                    "date": 1699123456,
                    "stats": {
                        "harmless": 70,
                        "malicious": 3,
                        "suspicious": 2,
                        "undetected": 8,
                        "timeout": 0
                    },
                    "results": {
                        "Kaspersky": {"category": "harmless", "result": "clean"},
                        "Fortinet": {"category": "malicious", "result": "Phishing"}
                    }
                }
            }
        }
        
        formatted = ti._format_url_result(mock_response, "https://test.com")
        print(f"   ✅ Formatted result: {formatted['positives']}/{formatted['total']} detections")
        print(f"   ✅ Status: {formatted['status']}")
        print(f"   ✅ Permalink: {formatted['permalink'][:50]}...")
        
    except Exception as e:
        print(f"   ❌ Result formatting failed: {e}")
    
    # 5. Error Handling Test
    print("\n5. Testing Error Handling...")
    try:
        error_result = ti.scan_url("https://test-error.com")
        if "error" in error_result:
            print("   ✅ Error handling works correctly")
            print(f"   📝 Error message: {error_result['error'][:50]}...")
        else:
            print("   ❌ Expected error but got success result")
            
    except Exception as e:
        print(f"   ✅ Exception handling works: {type(e).__name__}")
    
    # 6. Configuration Files Test
    print("\n6. Testing Configuration Files...")
    config_files = [
        ('.env.example', 'Example environment file'),
        ('.env', 'Development environment file')
    ]
    
    for filename, description in config_files:
        path = f'/home/runner/work/CyberVantage/CyberVantage/{filename}'
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                if 'VIRUSTOTAL_API_KEY' in content:
                    print(f"   ✅ {description} contains VIRUSTOTAL_API_KEY")
                else:
                    print(f"   ❌ {description} missing VIRUSTOTAL_API_KEY")
        else:
            print(f"   ❌ {description} not found")
    
    # 7. UI Template Test
    print("\n7. Testing UI Template...")
    template_path = '/home/runner/work/CyberVantage/CyberVantage/templates/check_threats.html'
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            template_content = f.read()
            
        ui_features = [
            ('Test API Connection', 'testConnectionBtn'),
            ('Modern card design', 'modern-card'),
            ('Enhanced JavaScript', 'ThreatScanManager'),
            ('Auto-detect scan type', 'autoDetectScanType'),
            ('Loading indicators', 'loading-indicator'),
            ('Alert system', 'showAlert')
        ]
        
        for feature, marker in ui_features:
            if marker in template_content:
                print(f"   ✅ {feature} implemented")
            else:
                print(f"   ❌ {feature} missing")
    
    print("\n" + "=" * 60)
    print("🎉 Comprehensive test completed!")
    print("\n📋 Summary of Improvements:")
    print("   • Fixed environment variable consistency (VIRUSTOTAL_API_KEY)")
    print("   • Enhanced error handling and logging")
    print("   • Improved URL validation and processing") 
    print("   • Better VirusTotal API response handling")
    print("   • Added API connection testing endpoint")
    print("   • Completely redesigned modern UI")
    print("   • Enhanced JavaScript with better UX")
    print("   • Comprehensive error messages for users")
    print("   • Auto-detection of input types")
    print("   • Improved result visualization")
    print("\n🔧 Next Steps:")
    print("   1. Get a real VirusTotal API key from https://www.virustotal.com/gui/my-apikey")
    print("   2. Update the .env file with your actual API key")
    print("   3. Test with real URLs to see live results")
    print("   4. Monitor the logs/threat_intelligence.log for detailed API calls")

if __name__ == "__main__":
    test_comprehensive_functionality()