# Extras Directory

This directory contains testing files, legacy code, and other miscellaneous files that are not part of the main CyberVantage application.

## Directory Structure

### 📁 `testing-files/`
**Safe testing and development files**
- `test_*.py` - Unit tests and integration tests for various components
- `final_test.py` - Final application testing suite
- `main_original.py` - Original backup of main application file

### 🚨 `legacy-vulnerable/` 
**DANGEROUS - Contains security vulnerabilities**
- Files with unprotected encryption/decryption endpoints
- **DO NOT USE IN PRODUCTION**
- See `SECURITY_WARNING.md` for details

### 📂 `legacy-misc/`
**Legacy miscellaneous files**
- Old development files and utilities
- Environment testing files
- API check utilities

## Important Security Notes

⚠️ **WARNING**: Files in the `legacy-vulnerable/` directory contain serious security vulnerabilities including unprotected encryption endpoints. These files should never be used in production.

✅ **SAFE**: Files in `testing-files/` are safe development and testing utilities.

## Usage Guidelines

1. **For Development**: Use files in `testing-files/` directory
2. **For Production**: Use only the main application files in the root directory
3. **Never Use**: Files in `legacy-vulnerable/` directory

## File Organization

All testing files have been moved from the root directory to maintain a clean project structure while preserving development history and ensuring security by isolating vulnerable legacy code.