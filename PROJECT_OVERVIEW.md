# CyberVantage — Complete Project Overview

CyberVantage is a Flask-based educational cybersecurity platform that teaches users how to detect phishing and spam through guided lessons, simulations, analytics, and practical assignments. It combines secure web engineering practices with AI-assisted content generation/evaluation.

## 1) What the platform does

CyberVantage is structured as a learning journey:

1. **Learn**: Users complete educational content and compliance/cyber awareness materials.
2. **Simulate**: Users classify phishing emails (predefined + AI-generated) and explain their reasoning.
3. **Analyze**: Users receive performance summaries and progression insights.
4. **Demonstrate**: Users craft phishing examples and receive AI evaluation.

The app is designed for safe training: realistic phishing patterns are simulated in a controlled environment.

## 2) High-level architecture

- **Backend**: Flask app (`main.py`) with modular blueprints
- **Database layer**: SQLAlchemy models in `models/database.py`
- **Config layer**: App/security/database config in `config/app_config.py`, AI provider config in `config/ai_config.py`
- **Business logic/services**: `pyFunctions/` (AI provider routing, simulation generation, threat intelligence, logging, assignment scoring)
- **Presentation layer**: Jinja2 templates in `templates/` + static CSS/JS in `static/`
- **Runtime entry points**: `main.py` (local run), `wsgi.py` (deployment)

## 3) Core backend modules

### `main.py`
- Creates Flask app via `create_app()`
- Configures AI providers (Azure OpenAI + Gemini fallback model strategy)
- Registers route blueprints:
  - `auth_bp` (`routes/auth_routes.py`)
  - `simulation_bp` (`routes/simulation_routes.py`)
  - `analysis_bp` (`routes/analysis_routes.py`)
  - `threat_bp` (`routes/threat_routes.py`)
- Exposes primary pages (`/`, `/about`, `/dashboard`)
- Initializes DB tables and schema updates at startup

### `config/app_config.py`
- Initializes Flask extensions:
  - `SQLAlchemy`
  - `CSRFProtect`
- Loads env vars and sets:
  - `SECRET_KEY`
  - `JWT_SECRET_KEY`
  - DB URI (`SQLALCHEMY_DATABASE_URI`)
  - CSRF secret
- Adds security headers on each response:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection`
  - `Referrer-Policy`
- Configures Fernet encryption key for sensitive data

### `config/ai_config.py`
- Configures Azure OpenAI (if present)
- Configures Google Gemini key (if present)
- Sets **primary** and **fallback** AI model strategy via env
- Initializes provider abstraction in `pyFunctions/ai_provider.py`

## 4) Route blueprints and responsibilities

### `routes/auth_routes.py`
Handles identity and account management:
- Register, login, logout
- JWT session token generation/validation
- Session extension endpoint
- In-memory rate limiting for login/registration attempts
- Password reset flow (request + token-based reset)
- Admin-only user management routes
- Demographics/profile capture used for personalized learning

### `routes/simulation_routes.py`
Handles phishing simulation lifecycle:
- Simulation start and state management in Flask session
- Phase 1: predefined email classification
- Phase 2: AI-generated email classification + explanation scoring
- AI feedback screens and progression flow
- Restart/skip/recovery support for interrupted simulation state
- Links email artifacts to simulation sessions

### `routes/analysis_routes.py`
Handles learning progress and observability:
- Learn pages (general, phishing, compliances)
- Performance analytics page from stored responses
- Session grouping for historical analysis
- API usage monitor endpoints
- Debug and schema utility endpoints

### `routes/threat_routes.py`
Handles threat intelligence and assignment workflows:
- URL/IP/hash scan integrations via VirusTotal wrapper
- Deep scan endpoint
- Threat scan history endpoint
- Final phishing creation assignment + AI evaluation

## 5) Data model (`models/database.py`)

### Main entities
- **User**
  - identity fields, bcrypt password hash
  - admin flag
  - demographics fields for personalization
  - password reset token/expiry fields
- **SimulationEmail**
  - stored email artifacts used in simulations
  - predefined vs AI-generated flag
- **SimulationResponse**
  - user decisions, explanations, AI feedback, score
- **SimulationSession**
  - session tracking across phase completion and scores

### Helpers in this module
- Schema migration helper (`update_database_schema`)
- Session grouping logic (`group_responses_into_sessions`)
- Simulation activity logging
- Mapping helpers for simulation/email linkage
- Seeded `predefined_emails` for phase 1

## 6) Frontend structure

### Templates (`templates/`)
Jinja pages include:
- Auth: `login.html`, `register.html`, reset templates
- Core flow: `dashboard.html`, `learn*.html`, `simulate.html`, `analysis.html`
- Assignment: `phishing_assignment.html`, `phishing_evaluation.html`
- Threat tools: `check_threats.html`, `deep_search.html`
- Supporting pages: `about.html`, `profile.html`, `admin_users.html`, `system_message.html`

### Static assets (`static/`)
- Shared style systems and page styles (`modern_styles.css`, `style.css`, etc.)
- UI scripts for interaction and dashboard behavior
- Image assets

## 7) Security posture implemented in code

- JWT-based auth with expiration
- Bcrypt password hashing
- CSRF protection on forms
- Input validation (including `email-validator`)
- Basic brute-force mitigation via rate limiting
- Security response headers
- Environment-based secret management
- Fernet encryption key support for sensitive storage fields

## 8) AI and external integrations

### AI
- **Azure OpenAI** and **Google Gemini** supported
- Primary/fallback provider selection at runtime
- Used for:
  - generating realistic phishing simulations
  - evaluating user reasoning
  - scoring user-created phishing assignment submissions

### Threat Intelligence
- VirusTotal API integration for URL/IP/file-hash scanning
- Optional deep scan flow and history retrieval

## 9) Dependencies and runtime stack

From `requirements.txt`:
- Flask ecosystem: `flask`, `jinja2`, `werkzeug`, `flask-wtf`
- Security: `pyjwt`, `bcrypt`, `cryptography`, `email-validator`
- AI: `openai`, `google-generativeai`
- DB: `sqlalchemy`, `flask-sqlalchemy`, `psycopg2-binary`
- Utility: `python-dotenv`, `requests`, `markdown`

## 10) Configuration and environment variables

Commonly used environment variables include:
- App/security: `FLASK_SECRET`, `JWT_SECRET`, `CSRF_SECRET`, `ENCRYPTION_KEY`
- Database: `DATABASE_URL` (or Postgres variants)
- AI: `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `GOOGLE_API_KEY`, `PRIMARY_AI_MODEL`
- Threat intel: `VIRUSTOTAL_API_KEY`
- Runtime: `FLASK_ENV`, `FLASK_HOST`, `FLASK_PORT`, optional `FLASK_INSTANCE_PATH`

## 11) Deployment and execution

- Local execution: `python main.py`
- Production/runtime adapters: `wsgi.py`, `vercel.json`
- DB tables auto-initialize on startup with schema compatibility checks

## 12) Testing and auxiliary content

- `extras/` contains integration and troubleshooting scripts/tests
- Additional markdown docs in root provide focused documentation:
  - security
  - database
  - admin and implementation summaries

## 13) Directory map (quick reference)

- `config/` — App and AI setup
- `models/` — ORM models + DB helpers
- `routes/` — Flask blueprints (auth, simulation, analysis, threat)
- `pyFunctions/` — Service/business logic modules
- `templates/` — Jinja frontend pages
- `static/` — CSS/JS/images
- `logs/` — runtime/app logs
- `instance/` — Flask instance data
- `extras/` — experiments/tests/support scripts

---

## Summary

CyberVantage is a modular, security-focused educational SaaS-style web app that teaches phishing awareness through practical simulation. Its architecture combines Flask blueprint modularity, SQLAlchemy persistence, strong baseline security controls, and multi-provider AI integrations to deliver interactive cybersecurity learning end-to-end.
