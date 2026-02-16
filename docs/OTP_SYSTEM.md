# OTP Password Reset System

This document explains the OTP (One-Time Password) system for password resets in CyberVantage.

## Overview

The OTP system provides a secure, user-friendly way to reset passwords using a 6-digit code sent via email.

## Environment Variables Required

```bash
RESEND_API_KEY=your-resend-api-key-here
RESEND_FROM_EMAIL=noreply@yourdomain.com
APP_URL=http://localhost:5000
```

Get your Resend API key from: https://resend.com/api-keys

## User Flow

1. **Request Reset** → Enter email → Receive OTP
2. **Verify OTP** → Enter 6-digit code → Validated
3. **New Password** → Set secure password → Complete

## Features

✅ 6-digit OTP (easy to read)
✅ 15-minute expiration
✅ 5 verification attempts max
✅ Beautiful email templates
✅ Terminal/SOC design theme
✅ Password strength meter

## Database Reset

To wipe and recreate the database:

```bash
python scripts/reset_database.py
```

Type `RESET` to confirm. This will delete ALL data.
