# Configuration Files

## predefined_emails.json

This file contains the 5 predefined phishing emails used in Phase 1 of the simulation.

**Format:**
```json
[
  {
    "id": 1,
    "sender": "email@domain.com",
    "subject": "Email subject",
    "date": "Month Day, Year",
    "content": "HTML content of the email",
    "is_spam": true/false
  }
]
```

**Important Notes:**
- IDs must be sequential (1-5)
- `is_spam` must be boolean (true/false)
- `content` should be HTML formatted
- Keep sender addresses realistic for training purposes
- Each email is used exactly once in Phase 1

**Editing:**
To modify the predefined emails, edit this JSON file directly. Changes will take effect on the next application restart.

## predefined_emails.json

This file contains the 5 predefined phishing emails used in Phase 1 of the simulation.

**Format:**
```json
[
  {
    "id": 1,
    "sender": "email@domain.com",
    "subject": "Email subject",
    "date": "Month Day, Year",
    "content": "HTML content of the email",
    "is_spam": true/false
  }
]
```

**Important Notes:**
- IDs must be sequential (1-5)
- `is_spam` must be boolean (true/false)
- `content` should be HTML formatted
- Keep sender addresses realistic for training purposes
- Each email is used exactly once in Phase 1

**Editing:**
To modify the predefined emails, edit this JSON file directly. Changes will take effect on the next application restart.
