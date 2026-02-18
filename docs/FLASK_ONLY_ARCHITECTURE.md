# Flask-Only Architecture

## Overview

CyberVantage has been converted to a **Flask-only** application. All React components have been backed up to the `react-ui-backup/` directory, and the application now exclusively uses Flask templates for rendering all pages.

## Landing Page

The landing page has been completely redesigned with a **Terminal/SOC (Security Operations Center)** theme to better reflect the cybersecurity nature of the platform.

### New Terminal Theme Features

- **Authentic SOC Aesthetic**: Dark terminal interface with cyan (#00d9ff), neon green (#00ff41), and amber (#ffb800) color scheme
- **Animated Effects**: 
  - Scan line animation simulating CRT displays
  - Grid overlay for terminal-like background
  - Typing animation effect for dynamic text
  - Floating background blobs
  - Flickering text effects
- **Real-time UTC Clock**: Displays current time in UTC, updating every second
- **Terminal Window**: Interactive terminal preview showing system initialization
- **Phase Cards**: Four-phase training protocol (Learn, Simulate, Analyze, Demonstrate)
- **Enterprise Features**: Six enterprise-grade features with icons
- **Stats Dashboard**: Real-time statistics (users, threats, accuracy, uptime)
- **Responsive Design**: Fully responsive across all device sizes

### Files

**HTML Template:**
- `templates/landing_terminal.html` - Main landing page with terminal theme

**Styles:**
- `static/landing_terminal.css` - Terminal/SOC theme styles (18KB)
  - Custom animations (flicker, pulse, slideUp, float, glow, scanLine)
  - Terminal navigation with blur effect
  - Hero section with animated elements
  - Phase cards with hover effects
  - Enterprise features grid
  - Footer with four-column layout

**JavaScript:**
- `static/landing_terminal.js` - Interactive features (5KB)
  - Real-time UTC clock
  - Typing animation effect
  - Smooth scrolling
  - Scroll-based animations
  - Navigation background on scroll
  - Easter egg (Konami code)

### Old Landing Page

The previous glassmorphism-themed landing page is still available at `/landing-old` route serving `templates/index.html` with `static/landing.css` and `static/landing.js`.

## Flask Templates

All pages are now rendered server-side using Flask templates:

### Public Pages
- `/` and `/landing` → `landing_terminal.html` (new terminal theme)
- `/landing-old` → `index.html` (old glassmorphism theme)
- `/login` → `login.html`
- `/register` → `register.html`
- `/about` → `about.html`
- `/reset-password` routes → `reset_password_request.html`, `reset_password.html`

### Protected Pages (require authentication)
- `/dashboard` → `dashboard.html`
- `/learn` → `learn.html`
- `/learn-phishing` → `learn_phishing.html`
- `/learn-compliances` → `learn_compliances.html`
- `/simulate` → `simulate.html`
- `/simulation-results` → `simulation_results.html`
- `/analysis` → `analysis.html`
- `/check-threats` → `check_threats.html`
- `/profile` → `profile.html`
- `/demographics` → `demographics.html`

### Admin Pages
- `/admin/users` → `admin_users.html`

## React Backup

The React frontend has been backed up to:
- `react-ui-backup/frontend-YYYYMMDD/` (dated backup)

These files are excluded from git via `.gitignore` and should not be committed.

## Running the Application

```bash
# Set environment variables (or use .env file)
export DATABASE_URL="your_database_url"

# Install dependencies
pip install -r requirements.txt

# Run Flask application
python main.py
```

The application will start on `http://127.0.0.1:5000` by default.

## Benefits of Flask-Only Architecture

1. **Simplified Deployment**: No need to build React frontend separately
2. **Server-Side Rendering**: Better SEO and faster initial page load
3. **Single Technology Stack**: Easier to maintain and develop
4. **Direct Template Control**: Full control over HTML output
5. **No Build Step**: Changes to templates are immediately visible
6. **Reduced Complexity**: Fewer moving parts in the deployment pipeline

## Development Workflow

1. Edit templates in `templates/` directory
2. Edit styles in `static/` directory  
3. Edit routes in `routes/` directory
4. Restart Flask server to see changes (no build step required)

## Template Structure

Templates use Jinja2 templating engine with features like:
- Template inheritance (`{% extends "base.html" %}`)
- Include partials (`{% include "header.html" %}`)
- URL generation (`{{ url_for('route_name') }}`)
- Variable interpolation (`{{ username }}`)
- Conditional rendering (`{% if condition %}`)
- Loops (`{% for item in items %}`)

## Static Assets

Static files are served from the `static/` directory:
- CSS files: `static/*.css`
- JavaScript files: `static/*.js`
- Images: `static/images/`

Access in templates: `{{ url_for('static', filename='landing_terminal.css') }}`

## Authentication

Authentication is handled via:
- JWT tokens stored in session
- `@token_required` decorator for protected routes
- Session management with Flask sessions

## API Routes

Some routes return JSON for AJAX requests:
- `/api/stats` - Get API statistics
- `/extend_session` - Extend user session
- `/logout` - Logout user

## Future Considerations

If React is needed again in the future:
1. React UI is safely backed up in `react-ui-backup/`
2. Can be restored or integrated as needed
3. Could serve React as SPA with Flask as API backend
4. Current templates can be used as reference for content/structure
