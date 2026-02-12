"""
Test Multi-AI Fallback System

This script tests the multi-AI fallback functionality without requiring actual API keys.
It validates the logic flow and provider selection.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_provider_configuration():
    """Test that providers are configured correctly"""
    print("=" * 70)
    print("TEST 1: Provider Configuration")
    print("=" * 70)
    
    # Set test environment
    os.environ['PRIMARY_AI_MODEL'] = 'azure'
    
    # Import after setting env vars
    from pyFunctions import ai_provider
    
    # Reload to pick up env changes
    import importlib
    importlib.reload(ai_provider)
    
    print(f"Primary Provider: {ai_provider.PRIMARY_PROVIDER}")
    print(f"Fallback Provider: {ai_provider.FALLBACK_PROVIDER}")
    
    assert ai_provider.PRIMARY_PROVIDER == 'azure', "Primary should be azure"
    assert ai_provider.FALLBACK_PROVIDER == 'gemini', "Fallback should be gemini"
    print("✓ PASSED: Azure primary, Gemini fallback\n")
    
    # Test reverse configuration
    os.environ['PRIMARY_AI_MODEL'] = 'gemini'
    importlib.reload(ai_provider)
    
    print(f"Primary Provider: {ai_provider.PRIMARY_PROVIDER}")
    print(f"Fallback Provider: {ai_provider.FALLBACK_PROVIDER}")
    
    assert ai_provider.PRIMARY_PROVIDER == 'gemini', "Primary should be gemini"
    assert ai_provider.FALLBACK_PROVIDER == 'azure', "Fallback should be azure"
    print("✓ PASSED: Gemini primary, Azure fallback\n")

def test_provider_validation():
    """Test that invalid providers default to azure"""
    print("=" * 70)
    print("TEST 2: Provider Validation")
    print("=" * 70)
    
    os.environ['PRIMARY_AI_MODEL'] = 'invalid_provider'
    
    from pyFunctions import ai_provider
    import importlib
    importlib.reload(ai_provider)
    
    print(f"Primary Provider (after invalid): {ai_provider.PRIMARY_PROVIDER}")
    assert ai_provider.PRIMARY_PROVIDER == 'azure', "Should default to azure"
    print("✓ PASSED: Invalid provider defaults to azure\n")

def test_provider_status():
    """Test getting provider status"""
    print("=" * 70)
    print("TEST 3: Provider Status")
    print("=" * 70)
    
    os.environ['PRIMARY_AI_MODEL'] = 'azure'
    
    from pyFunctions import ai_provider
    import importlib
    importlib.reload(ai_provider)
    
    status = ai_provider.get_provider_status()
    
    print(f"Status: {status}")
    
    assert 'primary_provider' in status, "Status should include primary_provider"
    assert 'fallback_provider' in status, "Status should include fallback_provider"
    assert 'providers' in status, "Status should include providers dict"
    assert 'azure' in status['providers'], "Status should include azure"
    assert 'gemini' in status['providers'], "Status should include gemini"
    
    print("✓ PASSED: Provider status structure is correct\n")

def test_only_two_providers():
    """Test that only Azure and Gemini are supported"""
    print("=" * 70)
    print("TEST 4: Only Two Providers (Azure & Gemini)")
    print("=" * 70)
    
    from pyFunctions import ai_provider
    import importlib
    importlib.reload(ai_provider)
    
    # Check provider constants
    assert hasattr(ai_provider, 'PROVIDER_AZURE'), "Should have PROVIDER_AZURE"
    assert hasattr(ai_provider, 'PROVIDER_GEMINI'), "Should have PROVIDER_GEMINI"
    assert not hasattr(ai_provider, 'PROVIDER_OPENAI'), "Should NOT have PROVIDER_OPENAI"
    
    assert ai_provider.PROVIDER_AZURE == 'azure', "PROVIDER_AZURE should be 'azure'"
    assert ai_provider.PROVIDER_GEMINI == 'gemini', "PROVIDER_GEMINI should be 'gemini'"
    
    print(f"Supported providers: {ai_provider.PROVIDER_AZURE}, {ai_provider.PROVIDER_GEMINI}")
    print("✓ PASSED: Only Azure and Gemini are supported\n")

def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("Multi-AI Fallback System - Test Suite")
    print("*" * 70)
    print("\n")
    
    tests = [
        test_only_two_providers,
        test_provider_configuration,
        test_provider_validation,
        test_provider_status,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
