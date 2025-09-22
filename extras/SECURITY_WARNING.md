# ⚠️ SECURITY WARNING ⚠️

## This directory contains legacy/testing code with SECURITY VULNERABILITIES

**DO NOT USE IN PRODUCTION**

### Dangerous Files Identified:
- `useless stuff/test.py` - Contains unprotected `/encrypt/<data>` and `/decrypt/<data>` routes
- `testing_new copy.py` - Contains similar dangerous encryption endpoints

### Security Issues:
1. **Unprotected Encryption/Decryption Endpoints**: These files expose encryption and decryption functionality via HTTP GET requests, allowing anyone to encrypt or decrypt data without authentication.

2. **Information Disclosure**: The routes could be used to extract sensitive information or perform cryptographic attacks.

### Safe Alternatives:
Use the main application (`main.py`) which has been security-hardened and does not contain these vulnerable endpoints.

### If You Must Use These Files:
1. Remove the dangerous routes:
   ```python
   @app.route('/encrypt/<string:data>')
   @app.route('/decrypt/<string:data>')
   ```
2. Add proper authentication to any encryption functionality
3. Never expose cryptographic operations via unprotected HTTP endpoints

---
**Last Updated**: 2024 Security Audit
**Status**: VULNERABLE - Do not use in production