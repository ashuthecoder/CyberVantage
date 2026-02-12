# Access Code Setup Guide

CyberVantage now includes an access code system that provides selective access control before users can reach the login or registration pages.

## Flow

```
Landing Page → Access Code Page → Login/Register → Dashboard
```

Users must enter a valid access code before they can proceed to login or register.

## Master Access Code

The simplest way to provide access is through the master access code set via environment variable:

```bash
export MASTER_ACCESS_CODE=YOUR_CODE_HERE
```

The master code:
- Always works and never expires
- Is not tracked in the database
- Should be kept secure
- Can be changed at any time by updating the environment variable

**Example:**
```bash
export MASTER_ACCESS_CODE=DEMO2026
```

## Database Access Codes

For more granular control, you can create access codes in the database with the following features:

### Code Properties
- **code**: Unique access code string (automatically uppercased)
- **description**: Optional description of the code's purpose
- **is_active**: Boolean to enable/disable the code
- **max_uses**: Maximum number of times the code can be used (NULL = unlimited)
- **current_uses**: Counter for tracking usage
- **expires_at**: Optional expiration datetime

### Creating Access Codes

You can create access codes programmatically using Python:

```python
from models.database import AccessCode, db
from datetime import datetime, timedelta

# Create unlimited access code
code = AccessCode(
    code="STUDENT2026",
    description="Student access for 2026",
    is_active=True,
    max_uses=None,  # Unlimited
    expires_at=None  # Never expires
)
db.session.add(code)
db.session.commit()

# Create limited-use code
limited_code = AccessCode(
    code="TRIAL50",
    description="Trial code - 50 uses",
    is_active=True,
    max_uses=50,
    expires_at=datetime.utcnow() + timedelta(days=30)
)
db.session.add(limited_code)
db.session.commit()

# Create temporary code
temp_code = AccessCode(
    code="WORKSHOP2026",
    description="Workshop on Feb 15, 2026",
    is_active=True,
    max_uses=100,
    expires_at=datetime(2026, 2, 15, 23, 59, 59)
)
db.session.add(temp_code)
db.session.commit()
```

### Managing Access Codes

To deactivate a code:

```python
code = AccessCode.query.filter_by(code="STUDENT2026").first()
code.is_active = False
db.session.commit()
```

To check code usage:

```python
code = AccessCode.query.filter_by(code="TRIAL50").first()
print(f"Used {code.current_uses} of {code.max_uses} times")
```

## Security Features

1. **Rate Limiting**: Maximum 10 access code attempts per IP per 5 minutes
2. **Case Insensitive**: Access codes are automatically converted to uppercase
3. **Session Tracking**: Access verification is stored in session, not cookies
4. **Usage Tracking**: All code usage is logged in the database
5. **Validation**: Codes are checked for:
   - Active status
   - Expiration date
   - Usage limit

## Testing

To test the access code system:

1. Set the master access code:
   ```bash
   export MASTER_ACCESS_CODE=DEMO2026
   ```

2. Start the application:
   ```bash
   python main.py
   ```

3. Navigate to `http://localhost:5000`
4. Click "Get Started" or "Login"
5. Enter the access code `DEMO2026`
6. You should be redirected to the login page

## Production Deployment

For production environments:

1. **Set Master Code**: Always set a strong master access code
   ```bash
   export MASTER_ACCESS_CODE=$(python -c "import secrets; print(secrets.token_urlsafe(16).upper())")
   ```

2. **Create Database Codes**: Create specific codes for different user groups
3. **Monitor Usage**: Regularly check code usage and disable compromised codes
4. **Rotate Codes**: Periodically change access codes for better security
5. **Secure Storage**: Never commit access codes to version control

## Australian Essential 8 Compliance

The access code system contributes to Essential 8 compliance by:

- **Application Control**: Restricts platform access to authorized users
- **Restrict Administrative Privileges**: Separates initial access from authentication
- **Multi-layered Security**: Adds an additional security layer before authentication

See `SECURITY.md` for complete Essential 8 compliance mapping.

## Troubleshooting

### "Invalid or expired access code"
- Verify the code is correct (case-insensitive)
- Check if the code has expired
- Check if the code has reached its usage limit
- Verify the code is still active in the database

### "Too many access code attempts"
- Wait 5 minutes before trying again
- This is a security feature to prevent brute force attacks

### Session Issues
- Clear browser cookies and try again
- Access codes are session-based, not cookie-based
- Closing the browser will clear the session

## Future Enhancements

Potential future improvements:
- Admin UI for managing access codes
- Access code generation API
- Email-based access code distribution
- Time-limited single-use codes
- Integration with user registration (track which code was used)
