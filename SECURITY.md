# CyberVantage Security Documentation

## Overview
CyberVantage is a cybersecurity education platform that implements multiple layers of security to protect user data and prevent common web application vulnerabilities.

## Security Protocols Implemented

### 1. Authentication & Session Management
- **JWT-based Authentication**: JSON Web Tokens with HS256 algorithm
- **Session Management**: Server-side session storage with secure token handling
- **Token Expiration**: 1-hour token lifetime with automatic refresh capability
- **Rate Limiting**: Protection against brute force attacks
  - Login attempts: Maximum 5 attempts per IP per 5 minutes
  - Registration attempts: Maximum 3 attempts per IP per 5 minutes
- **Timing Attack Prevention**: Random delays in authentication responses

### 2. Password Security
- **Password Hashing**: BCrypt with passlib library for secure password storage
- **Password Strength Requirements**:
  - Minimum 8 characters length
  - At least one uppercase letter
  - At least one lowercase letter  
  - At least one number
- **Password Confirmation**: Double-entry verification during registration

### 3. Data Encryption
- **Symmetric Encryption**: Fernet (AES 128) for sensitive data storage
- **Environment-based Key Management**: Encryption keys stored securely in environment variables
- **Database Field Encryption**: Sensitive user data encrypted at rest

### 4. Input Validation & Sanitization
- **Email Validation**: RFC-compliant email validation using email-validator library
- **Form Validation**: Server-side validation for all user inputs
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **XSS Prevention**: Template auto-escaping enabled

### 5. Security Headers
The application implements the following security headers:
- `X-Frame-Options: DENY` - Prevents clickjacking attacks
- `X-Content-Type-Options: nosniff` - Prevents MIME type confusion attacks
- `X-XSS-Protection: 1; mode=block` - Enables browser XSS filtering
- `Referrer-Policy: same-origin` - Controls referrer information leakage

### 6. Environment Configuration Security
- **Secure Defaults**: No hardcoded secrets in source code
- **Dynamic Secret Generation**: Secure random secrets generated if not provided
- **Environment Variable Validation**: Warnings for missing security-critical variables
- **Production Mode Detection**: Debug mode disabled in production environments

### 7. Database Security
- **SQL Injection Prevention**: SQLAlchemy ORM prevents SQL injection
- **Connection Security**: Secure database connection handling
- **Schema Updates**: Automated database schema migrations

## Security Configuration

### Required Environment Variables
```bash
# Flask Application Security
FLASK_SECRET=your-secure-random-secret-here
JWT_SECRET=your-jwt-secret-here
CSRF_SECRET=your-csrf-secret-here

# Database Configuration
DATABASE_URL=sqlite:///instance/app.db

# Data Encryption
ENCRYPTION_KEY=your-fernet-encryption-key-here

# Environment Setting
FLASK_ENV=production  # Set to 'development' for development
```

### Security Best Practices Implemented
1. **Secret Management**: All secrets stored in environment variables
2. **Error Handling**: Generic error messages to prevent information disclosure
3. **Logging**: Security events logged for monitoring
4. **Session Security**: Secure session configuration with proper cleanup
5. **Rate Limiting**: In-memory rate limiting (recommend Redis for production)

## Database Structure and Security

### Primary Database: SQLite
**Location**: `users.db` (configurable via DATABASE_URL)

#### Tables:
1. **User** - User account information
   - `id`: Primary key (Integer)
   - `name`: User display name (String, 50 chars)
   - `email`: Unique email address (String, 120 chars)
   - `password_hash`: BCrypt hashed password (String, 255 chars)
   - `encrypted_data`: Fernet-encrypted sensitive data (LargeBinary)

2. **SimulationResponse** - User responses to phishing simulations
   - `id`: Primary key (Integer)
   - `user_id`: Foreign key to User table
   - `email_id`: Simulation email identifier
   - `is_spam_actual`: Correct answer (Boolean)
   - `user_response`: User's response (Boolean)
   - `user_explanation`: User's explanation text
   - `ai_feedback`: AI evaluation feedback
   - `score`: AI-assigned score
   - `created_at`: Timestamp

3. **SimulationEmail** - Phishing simulation email content
   - `id`: Primary key (Integer)
   - `sender`: Email sender address
   - `subject`: Email subject line
   - `date`: Email date
   - `content`: Email body content
   - `is_spam`: Whether email is malicious
   - `is_predefined`: Whether email is template or AI-generated
   - `created_at`: Timestamp
   - `simulation_id`: Session identifier (String)

4. **SimulationSession** - User simulation session tracking
   - `id`: Primary key (Integer)
   - `user_id`: Foreign key to User table
   - `session_id`: UUID session identifier
   - `phase1_completed`: Phase 1 completion status
   - `phase2_completed`: Phase 2 completion status
   - `phase1_score`: Phase 1 score
   - `phase2_score`: Phase 2 score
   - `avg_phase2_score`: Average AI evaluation score
   - `started_at`: Session start time
   - `completed_at`: Session completion time

### Database Security Features:
- **Encrypted Storage**: Sensitive user data encrypted with Fernet
- **Foreign Key Constraints**: Data integrity maintained
- **Prepared Statements**: SQLAlchemy ORM prevents SQL injection
- **Schema Validation**: Automatic schema updates with validation

### Logging and Monitoring
**Location**: `logs/` directory

1. **API Logs**: API usage and performance metrics
2. **Simulation Activity Logs**: User simulation activity tracking
3. **Security Event Logs**: Authentication attempts and security events

## Vulnerability Assessments

### Fixed Security Issues:
1. ✅ **Removed dangerous encryption routes** - No longer exposing `/encrypt/<data>` and `/decrypt/<data>` endpoints
2. ✅ **Eliminated hardcoded secrets** - All secrets now environment-based with secure generation
3. ✅ **Enhanced JWT security** - Added timing attack protection and better error handling
4. ✅ **Implemented rate limiting** - Protection against brute force attacks
5. ✅ **Added security headers** - Comprehensive security header implementation
6. ✅ **Production mode security** - Debug mode automatically disabled in production
7. ✅ **Enhanced password policies** - Stronger password requirements implemented

### Security Recommendations for Production:
1. **Use HTTPS**: Enable SSL/TLS encryption for all communications
2. **Redis Rate Limiting**: Replace in-memory rate limiting with Redis for scalability
3. **Database Encryption**: Consider full database encryption for sensitive deployments
4. **Security Monitoring**: Implement comprehensive security event monitoring
5. **Regular Security Updates**: Keep all dependencies updated
6. **Penetration Testing**: Regular security assessments
7. **Backup Security**: Secure backup procedures for encrypted data

## Australian Essential Eight Compliance

CyberVantage implements security controls aligned with the Australian Cyber Security Centre's (ACSC) Essential Eight mitigation strategies. Below is our compliance mapping:

### 1. Application Control ✅
- **Implementation**: Access code system restricts platform entry to authorized users only
- **Controls**: 
  - Pre-authentication access code verification
  - Database-backed access code management with usage tracking
  - Master access code via environment variable for administrative access
  - Rate limiting on access code attempts (10 attempts per 5 minutes per IP)

### 2. Patch Applications ✅
- **Implementation**: Dependency management and regular updates
- **Controls**:
  - All dependencies specified in requirements.txt with version pinning
  - Regular dependency updates via pip
  - Automated dependency vulnerability scanning recommended

### 3. Configure Microsoft Office Macro Settings 🔶
- **Applicability**: Not applicable - web application without Office document processing
- **Note**: If future features require document upload, macros will be disabled

### 4. User Application Hardening ✅
- **Implementation**: Browser-based application with restricted execution environment
- **Controls**:
  - Content Security Policy headers
  - X-Frame-Options to prevent clickjacking
  - X-Content-Type-Options to prevent MIME sniffing
  - No execution of unvalidated user content

### 5. Restrict Administrative Privileges ✅
- **Implementation**: Role-based access control (RBAC)
- **Controls**:
  - Admin flag in user database model
  - `@admin_required` decorator for sensitive routes
  - Separate admin panel at `/admin/users`
  - Regular user accounts have minimal privileges

### 6. Patch Operating Systems ✅
- **Implementation**: Container and infrastructure level
- **Controls**:
  - Python environment with regular updates
  - Flask framework kept current
  - Operating system patches managed at deployment level

### 7. Multi-Factor Authentication (MFA) 🔶
- **Current Status**: Single-factor authentication (password-based)
- **Implemented Controls**:
  - JWT-based session tokens (1-hour expiry)
  - Access code as additional authentication layer
  - Rate limiting on login attempts
- **Future Enhancement**: TOTP-based MFA recommended for full compliance

### 8. Regular Backups ✅
- **Implementation**: Database backup procedures documented
- **Controls**:
  - SQLite database file backup procedures in admin documentation
  - Encrypted data backup considerations documented
  - Recovery procedures for encrypted data with key management

### Compliance Summary
- **Fully Implemented**: 6 of 8 strategies
- **Partially Implemented**: 2 of 8 strategies (MFA recommended, Office macros N/A)
- **Overall Assessment**: Strong alignment with Essential Eight framework

### Access Control Enhancement (NEW)
The access code system provides an additional security layer:
- **Selective Access**: Only users with valid access codes can reach login/registration
- **Code Management**: Admins can create codes with expiry dates and usage limits
- **Usage Tracking**: All access code usage is logged and monitored
- **Master Code**: Emergency access via environment-configured master code
- **Rate Limiting**: Protection against access code brute force attacks

## Contact
For security issues or questions, please contact the development team.

---
*Last updated: 2026*
*Security review: Complete*
*Essential Eight compliance mapping: Added*