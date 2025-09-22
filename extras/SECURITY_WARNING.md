# ⚠️ SECURITY WARNING ⚠️

## This directory contains legacy/testing code with SECURITY VULNERABILITIES

**DO NOT USE IN PRODUCTION**

### Directory Structure & Status
```
extras/
├── SECURITY_WARNING.md          # This file
├── testing-files/               # Safe testing files (moved from root)
│   ├── test_*.py               # Unit tests and integration tests
│   ├── final_test.py           # Final application tests
│   └── main_original.py        # Original backup of main application
├── legacy-vulnerable/          # DANGEROUS FILES - DO NOT USE
│   ├── testing_new copy.py     # Contains vulnerable encryption routes
│   └── test.py                 # Contains vulnerable encryption routes
└── legacy-misc/                # Legacy miscellaneous files
    ├── api_chk.py
    ├── env_test.md
    └── other legacy files
```

### Dangerous Files Identified:
- `legacy-vulnerable/test.py` - Lines 171-176: Unprotected `/encrypt/<data>` and `/decrypt/<data>` routes
- `legacy-vulnerable/testing_new copy.py` - Lines 902-910: Similar dangerous encryption endpoints

### Security Issues:
1. **Unprotected Encryption/Decryption Endpoints**: These files expose encryption and decryption functionality via HTTP GET requests, allowing anyone to encrypt or decrypt data without authentication.

2. **Information Disclosure**: The routes could be used to extract sensitive information or perform cryptographic attacks.

3. **Remote Code Execution Potential**: Direct exposure of cryptographic functions can lead to security breaches.

### Safe Alternatives:
Use the main application (`main.py`) which has been security-hardened and does not contain these vulnerable endpoints.

### Security Improvements Made:
- [x] Moved vulnerable files to clearly marked `legacy-vulnerable/` directory
- [x] Organized testing files in proper `testing-files/` directory  
- [x] Updated main application with comprehensive security hardening
- [x] Added SQL injection protection via SQLAlchemy ORM
- [x] Implemented proper input validation and sanitization
- [x] Added CSRF protection and security headers
- [x] Removed all dangerous unprotected encryption endpoints

### If You Must Use These Files:
1. Remove the dangerous routes:
   ```python
   @app.route('/encrypt/<string:data>')
   @app.route('/decrypt/<string:data>')
   ```
2. Add proper authentication to any encryption functionality
3. Never expose cryptographic operations via unprotected HTTP endpoints
4. Use proper input validation and rate limiting

---
**Last Updated**: 2025-09-22 Security Reorganization  
**Status**: VULNERABLE FILES ISOLATED - Main app is secure