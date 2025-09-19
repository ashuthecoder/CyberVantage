CyberVantage/
├── app/
│   ├── __init__.py                # App initialization
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                # Authentication routes
│   │   ├── learning.py            # Learning phase routes
│   │   ├── simulation.py          # Simulation phase routes
│   │   ├── analysis.py            # Analysis phase routes
│   │   └── threats.py             # Threat checking routes
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py                # User model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py          # Azure OpenAI integration
│   │   ├── crypto_service.py      # Encryption/decryption
│   │   └── threat_service.py      # VirusTotal API integration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── auth.py                # JWT token handling
├── static/                        # Existing static files
├── templates/                     # Existing templates
├── config.py                      # Configuration
└── run.py                         # Application entry point