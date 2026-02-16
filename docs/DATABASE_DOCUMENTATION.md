# CyberVantage Database Documentation

This document provides a comprehensive overview of all database tables used in the CyberVantage cybersecurity education platform, their purposes, relationships, and security features.

## Database Overview

CyberVantage uses **SQLite** as the primary database (configurable to PostgreSQL/MySQL for production). The database is located at:
- **Development**: `users.db` in the project root
- **Production**: Configurable via `DATABASE_URL` environment variable

## Database Tables

### 1. User Table
**Purpose**: Stores user account information, authentication data, and admin privileges.

**Fields**:
- `id` (Integer, Primary Key): Unique user identifier
- `name` (String, 50 chars): User display name
- `email` (String, 120 chars, Unique): User's email address (login credential)
- `password_hash` (String, 255 chars): BCrypt-hashed password with salt
- `encrypted_data` (LargeBinary, Optional): Fernet-encrypted sensitive user data
- `is_admin` (Boolean, Default: False): Admin privileges flag
- `created_at` (DateTime): Account creation timestamp
- `password_reset_token` (String, 255 chars, Optional): Secure token for password resets
- `password_reset_expires` (DateTime, Optional): Password reset token expiration

**Security Features**:
- Passwords are hashed using BCrypt with automatic salting
- Sensitive data encrypted using Fernet (AES-256)
- Password reset tokens are time-limited (1 hour expiration)
- Admin privileges tracked separately for authorization

**Relationships**:
- One-to-many with `SimulationResponse` (user responses to phishing emails)
- One-to-many with `SimulationSession` (user simulation attempts)

---

### 2. SimulationResponse Table
**Purpose**: Records user responses to phishing simulation emails, including their answers, explanations, and AI-generated feedback.

**Fields**:
- `id` (Integer, Primary Key): Unique response identifier
- `user_id` (Integer, Foreign Key): References User.id
- `email_id` (Integer): Identifier of the simulation email (1-5 for predefined, >5 for AI-generated)
- `is_spam_actual` (Boolean): The correct answer (whether email is spam/phishing)
- `user_response` (Boolean): User's answer (True = spam, False = legitimate)
- `user_explanation` (Text, Optional): User's written explanation for AI emails
- `ai_feedback` (Text, Optional): AI-generated evaluation of user's explanation
- `score` (Integer, Optional): AI-assigned score (1-10 scale)
- `created_at` (DateTime): Response timestamp

**Purpose in Education**:
- Tracks learning progress through simulation phases
- Enables performance analytics and personalized feedback
- Stores AI evaluations for adaptive learning paths

**Relationships**:
- Many-to-one with `User`
- Related to `SimulationEmail` via `email_id`

---

### 3. SimulationEmail Table
**Purpose**: Stores both predefined and AI-generated phishing emails used in simulations.

**Fields**:
- `id` (Integer, Primary Key): Unique email identifier
- `sender` (String, 120 chars): Email sender address
- `subject` (String, 255 chars): Email subject line
- `date` (String, 50 chars): Email date display
- `content` (Text): Full email content (HTML formatted)
- `is_spam` (Boolean): Whether email is phishing/spam (correct answer)
- `is_predefined` (Boolean): True for predefined emails, False for AI-generated
- `created_at` (DateTime): Email creation timestamp
- `simulation_id` (String, Optional): UUID linking emails to specific simulation sessions

**Content Types**:
- **Predefined Emails (ID 1-5)**: Curated examples covering common phishing techniques
  - PayPal phishing (ID 1)
  - Amazon delivery scam (ID 2) 
  - LinkedIn legitimate notification (ID 3)
  - Microsoft password expiry scam (ID 4)
  - New York Times newsletter legitimate (ID 5)
- **AI-Generated Emails (ID >5)**: Dynamic content created by Azure OpenAI

**Security Considerations**:
- All links in phishing emails are neutralized/contained within the platform
- Content is sanitized to prevent XSS attacks
- AI-generated content is filtered for appropriateness

---

### 4. SimulationSession Table
**Purpose**: Tracks complete user simulation attempts across both learning phases.

**Fields**:
- `id` (Integer, Primary Key): Unique session identifier
- `user_id` (Integer, Foreign Key): References User.id
- `session_id` (String, 36 chars): UUID for session tracking
- `phase1_completed` (Boolean, Default: False): Phase 1 completion status
- `phase2_completed` (Boolean, Default: False): Phase 2 completion status
- `phase1_score` (Integer, Optional): Phase 1 score out of 5
- `phase2_score` (Integer, Optional): Phase 2 score out of 5
- `avg_phase2_score` (Float, Optional): Average AI score for Phase 2 (out of 10)
- `started_at` (DateTime): Session start time
- `completed_at` (DateTime, Optional): Session completion time

**Learning Phase Structure**:
- **Phase 1**: Static predefined emails (IDs 1-5) testing basic recognition
- **Phase 2**: AI-generated emails with explanation requirements and feedback
- Tracks progression and performance across both phases

**Relationships**:
- Many-to-one with `User`
- Sessions link to responses via user_id and timing

---

## Database Security Features

### 1. Encryption at Rest
- **Fernet Encryption**: Sensitive user data encrypted using AES-256
- **Encryption Key Management**: Configurable via `ENCRYPTION_KEY` environment variable
- **Key Rotation**: Supports key rotation for enhanced security

### 2. Access Control
- **Admin Privileges**: Role-based access control via `is_admin` flag
- **User Isolation**: Users can only access their own simulation data
- **Session Security**: JWT tokens for stateless authentication

### 3. Data Integrity
- **Foreign Key Constraints**: Maintain referential integrity
- **Schema Validation**: Automatic schema updates with validation
- **Prepared Statements**: SQLAlchemy ORM prevents SQL injection

### 4. Audit Logging
- **Location**: `logs/` directory
- **Activity Tracking**: User simulation activities logged
- **Security Events**: Authentication attempts and admin actions logged
- **Performance Monitoring**: API usage and response times tracked

---

## Database Configuration

### Environment Variables
```bash
# Database URL (SQLite by default)
DATABASE_URL=sqlite:///users.db

# Encryption key for sensitive data
ENCRYPTION_KEY=your-fernet-key-here

# Application security
FLASK_SECRET=your-flask-secret
JWT_SECRET=your-jwt-secret
CSRF_SECRET=your-csrf-secret
```

### Schema Updates
- **Automatic Migration**: Schema updates handled automatically on startup
- **Backward Compatibility**: New columns added safely with defaults
- **Version Control**: Database changes tracked through code commits

---

## Data Flow and Relationships

```
User (Authentication & Profile)
├── SimulationSession (Learning Progress Tracking)
│   └── Links to SimulationResponse via user_id and session timing
├── SimulationResponse (Individual Email Responses)
│   └── References SimulationEmail via email_id
└── Admin Capabilities (if is_admin=True)
    ├── View all users and responses
    └── Promote users to admin status

SimulationEmail (Content Repository)
├── Predefined emails (IDs 1-5) for consistent baseline testing
└── AI-generated emails (IDs >5) for adaptive learning
```

---

## Performance Considerations

### Indexing Strategy
- Primary keys automatically indexed
- Foreign keys indexed for join performance
- Email lookups optimized via unique constraints

### Scalability Notes
- SQLite suitable for educational/development use
- Production deployments should use PostgreSQL/MySQL
- Consider read replicas for analytics queries

### Backup Strategy
- **Development**: File-based SQLite backups
- **Production**: Automated database backups with encryption
- **Recovery**: Point-in-time recovery capabilities needed for production

---

## Privacy and Compliance

### Data Protection
- **Minimal Data Collection**: Only necessary educational data stored
- **Encryption**: Sensitive data encrypted at rest and in transit
- **Retention Policy**: Consider data retention policies for educational records

### User Rights
- Users own their simulation responses and progress data
- Admin users can view aggregated analytics but individual privacy maintained
- Data export capabilities for user data portability

---

This database structure supports the core educational mission of CyberVantage while maintaining security, performance, and scalability for cybersecurity education at scale.