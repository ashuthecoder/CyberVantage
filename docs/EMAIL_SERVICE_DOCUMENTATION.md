# Email Service Documentation

## Overview

CyberVantage uses [Resend](https://resend.com/) for transactional email delivery. The email service is implemented in `pyFunctions/email_service.py`.

## Setup

### 1. Get Resend API Key

1. Sign up at [resend.com](https://resend.com/)
2. Verify your domain or use Resend's test domain
3. Generate an API key from the dashboard

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Resend Email Configuration
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=noreply@yourdomain.com
APP_URL=http://localhost:5000
```

For production, update `APP_URL` to your production domain.

### 3. Install Dependencies

```bash
pip install resend==2.6.0
```

## Available Functions

### `send_email(to_email, subject, html_content, from_email=None)`

Send a generic email with custom HTML content.

**Parameters:**
- `to_email` (str): Recipient email address
- `subject` (str): Email subject line
- `html_content` (str): HTML body of the email
- `from_email` (str, optional): Sender email (defaults to RESEND_FROM_EMAIL env var)

**Returns:**
- dict with `success` (bool) and `message` (str) keys

**Example:**
```python
from pyFunctions.email_service import send_email

result = send_email(
    to_email="user@example.com",
    subject="Welcome!",
    html_content="<h1>Hello!</h1><p>Welcome to CyberVantage</p>"
)

if result['success']:
    print(f"Email sent! ID: {result['id']}")
else:
    print(f"Failed: {result['message']}")
```

### `send_password_reset_email(to_email, reset_token, username)`

Send a password reset email with a secure reset link.

**Parameters:**
- `to_email` (str): User's email address
- `reset_token` (str): Password reset token from database
- `username` (str): User's username for personalization

**Returns:**
- dict with `success` and `message` keys

**Email Template:**
- Professional gradient header
- Clear call-to-action button
- Copy-pasteable reset link as fallback
- 1-hour expiry notice
- Security tips

**Example:**
```python
from pyFunctions.email_service import send_password_reset_email

result = send_password_reset_email(
    to_email="user@example.com",
    reset_token="abc123def456",
    username="John Doe"
)
```

### `send_welcome_email(to_email, username)`

Send a welcome email to newly registered users.

**Parameters:**
- `to_email` (str): User's email address  
- `username` (str): User's username

**Returns:**
- dict with `success` and `message` keys

**Email Template:**
- Welcome message with user's name
- Overview of all 4 training phases
- Getting started instructions
- Professional branding

**Example:**
```python
from pyFunctions.email_service import send_welcome_email

result = send_welcome_email(
    to_email="newuser@example.com",
    username="Jane Smith"
)
```

### `send_notification_email(to_email, username, notification_type, message)`

Send a general notification email.

**Parameters:**
- `to_email` (str): User's email address
- `username` (str): User's username
- `notification_type` (str): Type/category of notification
- `message` (str): HTML message content

**Returns:**
- dict with `success` and `message` keys

**Example:**
```python
from pyFunctions.email_service import send_notification_email

result = send_notification_email(
    to_email="user@example.com",
    username="John Doe",
    notification_type="Achievement Unlocked",
    message="<p>Congratulations! You've completed Phase 1.</p>"
)
```

## Integration Points

### User Registration (`routes/auth_routes.py`)

When a new user registers, a welcome email is automatically sent:

```python
# After user creation
try:
    email_result = send_welcome_email(email, name)
    if not email_result['success']:
        print(f"Warning: Failed to send welcome email: {email_result['message']}")
except Exception as e:
    print(f"Warning: Error sending welcome email: {str(e)}")
```

### Password Reset (`routes/auth_routes.py`)

When a user requests a password reset:

```python
try:
    email_result = send_password_reset_email(email, token, user.name)
    if email_result['success']:
        flash(f"Password reset instructions have been sent to {email}.", "info")
    else:
        # Fallback to console logging
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        print(f"Reset URL: {reset_url}")
        flash(f"Password reset link generated. Check console.", "info")
except Exception as e:
    # Graceful degradation
    print(f"Email service error: {str(e)}")
```

## Error Handling

All email functions include comprehensive error handling:

1. **Missing API Key**: Returns error without crashing
2. **Network Errors**: Catches and reports connection issues
3. **Invalid Email**: Validates format before sending
4. **Rate Limits**: Respects Resend's rate limits

**Graceful Degradation:**
- If email sending fails, the application continues to work
- Error messages are logged for debugging
- Users see appropriate feedback messages
- Critical functions (like password reset) fall back to console logging

## Testing

### Development/Testing

For local development without Resend:

1. Don't set `RESEND_API_KEY` in `.env`
2. Email functions will return failure but won't crash
3. Password reset links will be printed to console

### Production

1. Set valid `RESEND_API_KEY`
2. Configure `RESEND_FROM_EMAIL` with verified domain
3. Update `APP_URL` to production domain
4. Monitor Resend dashboard for delivery metrics

## Email Templates

All emails use responsive HTML templates with:

- Professional gradient header (purple/blue)
- Mobile-friendly design
- Clear call-to-action buttons
- Consistent branding
- Footer with legal information

### Customizing Templates

To customize email templates, edit the HTML strings in `pyFunctions/email_service.py`:

- Modify colors in `<style>` blocks
- Update header gradient colors
- Change button styles
- Add your logo/branding

## Rate Limits

Resend free tier includes:
- 3,000 emails/month
- 100 emails/day

For higher volumes, upgrade your Resend plan.

## Security Best Practices

1. **Never commit API keys** - Use environment variables
2. **Verify domains** - Use verified sending domains in production
3. **HTTPS only** - Always use HTTPS for reset links
4. **Token expiry** - Password reset tokens expire after 1 hour
5. **Rate limiting** - Implement rate limiting on auth routes (already done)

## Troubleshooting

### Emails not sending?

1. Check `RESEND_API_KEY` is set correctly
2. Verify sender email domain is verified in Resend
3. Check Resend dashboard for error logs
4. Ensure you haven't hit rate limits

### Emails going to spam?

1. Verify your sending domain with SPF/DKIM
2. Use a professional sender email (not @gmail.com)
3. Avoid spam trigger words in subject/content
4. Include unsubscribe links for marketing emails

### Debug Mode

Add debug logging:

```python
import os
os.environ['RESEND_DEBUG'] = 'true'
```

## Future Enhancements

Potential additions to email service:

- Email templates with Jinja2
- HTML email previews
- Email verification on signup
- Digest/summary emails
- Achievement notification emails
- Weekly progress reports
- Team collaboration invites
