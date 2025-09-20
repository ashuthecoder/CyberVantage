#!/usr/bin/env python3
"""
Test script to verify encryption key handling works correctly
"""

import os
import tempfile
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from cryptography.fernet import Fernet
from config.app_config import create_app

def test_valid_encryption_key():
    """Test with a valid Fernet key"""
    print("🧪 Testing with valid encryption key...")
    
    # Generate a valid key
    valid_key = Fernet.generate_key().decode()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write(f"ENCRYPTION_KEY={valid_key}\n")
        env_file = f.name
    
    try:
        # Set the environment
        os.environ['ENCRYPTION_KEY'] = valid_key
        
        app = create_app()
        
        # Check if Fernet instance was created successfully
        assert 'FERNET' in app.config
        assert isinstance(app.config['FERNET'], Fernet)
        
        print("✅ Valid encryption key test passed")
        
    finally:
        # Clean up
        os.unlink(env_file)
        if 'ENCRYPTION_KEY' in os.environ:
            del os.environ['ENCRYPTION_KEY']

def test_invalid_encryption_key():
    """Test with an invalid encryption key"""
    print("🧪 Testing with invalid encryption key...")
    
    # Use an invalid key (the original problem)
    invalid_key = "your_32_byte_encryption_key"
    
    try:
        os.environ['ENCRYPTION_KEY'] = invalid_key
        
        app = create_app()
        
        # Should still work but generate a new key
        assert 'FERNET' in app.config
        assert isinstance(app.config['FERNET'], Fernet)
        
        print("✅ Invalid encryption key test passed (fallback worked)")
        
    finally:
        if 'ENCRYPTION_KEY' in os.environ:
            del os.environ['ENCRYPTION_KEY']

def test_no_encryption_key():
    """Test with no encryption key provided"""
    print("🧪 Testing with no encryption key...")
    
    try:
        # Make sure no key is set
        if 'ENCRYPTION_KEY' in os.environ:
            del os.environ['ENCRYPTION_KEY']
        
        app = create_app()
        
        # Should generate a new key
        assert 'FERNET' in app.config
        assert isinstance(app.config['FERNET'], Fernet)
        
        print("✅ No encryption key test passed (generated new key)")
        
    finally:
        pass

def main():
    print("🔐 Testing CyberVantage encryption key handling")
    print("=" * 50)
    
    test_valid_encryption_key()
    test_invalid_encryption_key() 
    test_no_encryption_key()
    
    print("\n🎉 All encryption key tests passed!")

if __name__ == "__main__":
    main()