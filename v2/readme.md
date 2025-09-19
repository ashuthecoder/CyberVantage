CyberVantage/
├── app/
│   ├── __init__.py                # App initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication routes
│   │   ├── learning.py            # Learning phase routes
│   │   ├── simulation.py          # Simulation phase API routes
│   │   ├── web_simulation.py      # Simulation phase web routes
│   │   ├── analysis.py            # Analysis phase routes
│   │   ├── threats.py             # Threat checking routes
│   │   └── web.py                 # Web UI routes
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   └── simulation.py          # Simulation models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py          # Azure OpenAI integration
│   │   ├── crypto_service.py      # Encryption/decryption
│   │   └── threat_service.py      # VirusTotal API integration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── auth.py                # JWT token handling
│   ├── extensions.py              # Flask extensions
│   └── forms.py                   # WTForms definitions
├── static/                        # Static files (CSS, JS)
├── templates/                     # HTML templates
├── config.py                      # Configuration
└── run.py                         # Application entry point

## Simulation Feature

The simulation feature allows users to practice identifying phishing emails. It uses Azure OpenAI to generate realistic email scenarios and evaluate user responses.

### How it works:

1. User selects a difficulty level (easy, medium, hard)
2. System generates a simulated email using Azure OpenAI
3. User determines if the email is legitimate or phishing
4. System evaluates the user's assessment and provides feedback
5. Results are stored for future analysis

### Implementation Notes:

- Uses the Azure OpenAI ChatCompletion API
- Emails can be either phishing or legitimate
- User must provide reasoning for their assessment
- AI provides educational feedback on user responses