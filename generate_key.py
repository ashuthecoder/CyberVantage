#!/usr/bin/env python3
"""
CyberVantage Encryption Key Generator

This utility generates a proper Fernet encryption key for use in the .env file.
Run this script and copy the generated key to your ENCRYPTION_KEY variable.
"""

from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a new Fernet encryption key"""
    key = Fernet.generate_key()
    return key.decode()

def main():
    print("🔐 CyberVantage Encryption Key Generator")
    print("=" * 50)
    
    key = generate_encryption_key()
    
    print("Generated a new encryption key:")
    print(f"ENCRYPTION_KEY={key}")
    print()
    print("📋 Copy the line above to your .env file")
    print("⚠️  Keep this key secure - losing it means you cannot decrypt existing data!")
    print("💡 This key is used to encrypt sensitive database fields")

if __name__ == "__main__":
    main()