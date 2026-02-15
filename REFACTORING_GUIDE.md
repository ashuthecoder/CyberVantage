# CyberVantage - Complete Refactoring Guide

## Overview

This document describes the complete refactoring of CyberVantage from Flask + Jinja2 templates to FastAPI + React.

## Architecture

### Backend: FastAPI
- **Framework**: FastAPI 0.115+
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **Authentication**: JWT tokens with OAuth2 password bearer
- **API**: RESTful API with automatic OpenAPI documentation

### Frontend: React + Vite
- **Framework**: React 19
- **Build Tool**: Vite 7
- **Routing**: React Router DOM
- **State Management**: Context API (Auth & Theme)
- **HTTP Client**: Axios

## Project Structure

```
CyberVantage/
├── api/                          # FastAPI Backend
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   └── auth.py              # JWT authentication
│   ├── models/
│   │   ├── database.py          # ORM models
│   │   └── schemas.py           # Pydantic schemas
│   └── routers/
│       ├── auth.py              # Authentication endpoints
│       ├── simulation.py        # Simulation endpoints
│       ├── analysis.py          # Analytics endpoints
│       └── threats.py           # Threat detection endpoints
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js        # Axios API client
│   │   ├── context/
│   │   │   ├── AuthContext.jsx  # Authentication state
│   │   │   └── ThemeContext.jsx # Theme state (SOC/Modern)
│   │   ├── components/
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── App.jsx              # Router setup
│   │   └── main.jsx             # Entry point
│   ├── package.json
│   └── vite.config.js
├── app.py                        # FastAPI main application
├── pyFunctions/                  # Shared Python utilities
├── models/                       # Legacy Flask models (to be removed)
├── routes/                       # Legacy Flask routes (to be removed)
└── templates/                    # Legacy templates (to be removed)
```

## Running the Application

### Development Mode

**Backend (FastAPI)**:
```bash
# Install dependencies
pip install fastapi uvicorn python-multipart python-jose passlib sqlalchemy pydantic-settings email-validator

# Run server
python app.py
# or
uvicorn app:app --reload --port 8000
```

Access API docs: http://localhost:8000/docs

**Frontend (React)**:
```bash
cd frontend

# Install dependencies
npm install

# Development server with hot reload
npm run dev
```

Access frontend: http://localhost:5173

### Production Build

**Backend**:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run build

# Serves from frontend/dist/
# FastAPI will automatically serve these files
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (OAuth2 form)
- `POST /api/auth/login/json` - Login (JSON body)
- `GET /api/auth/me` - Get current user
- `POST /api/auth/password-reset-request` - Request password reset
- `POST /api/auth/password-reset` - Reset password with token

### Simulation
- `GET /api/simulation/emails` - Get simulation emails
- `POST /api/simulation/responses` - Submit response
- `GET /api/simulation/sessions` - Get user sessions
- `POST /api/simulation/sessions` - Create new session

### Analysis
- `GET /api/analysis/performance` - Get performance stats
- `GET /api/analysis/history` - Get session history

### Threats
- `POST /api/threats/check` - Check URL for threats

### Health
- `GET /api/health` - Health check endpoint

## Features

### Backend Features
✅ JWT authentication with secure token handling
✅ Pydantic validation for all inputs
✅ Async/await support
✅ CORS middleware for React frontend
✅ Automatic API documentation (Swagger UI)
✅ Database session management
✅ Password hashing with bcrypt
✅ Email integration (Resend API)
✅ Environment-based configuration

### Frontend Features
✅ React Router for navigation
✅ Protected routes with authentication
✅ JWT token management (localStorage)
✅ Automatic token refresh
✅ SOC/Modern theme toggle with persistence
✅ Responsive design
✅ Terminal-style UI (SOC theme)
✅ Clean modern UI (Modern theme)

## Theme System

The application supports two themes:

### SOC Theme
- Dark background (#0a0e27)
- Terminal green text (#00ff41)
- Cyan highlights (#00d9ff)
- JetBrains Mono font
- Scanline effects
- Grid background overlay

### Modern Theme
- Light background (#ffffff)
- Blue accents (#3b82f6)
- Inter font family
- Rounded corners
- Clean, minimal design

Theme preference is stored in localStorage and persists across sessions.

## Environment Variables

Create a `.env` file:

```bash
# Application
ENVIRONMENT=development
DEBUG=true

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=sqlite:///./users.db

# Email (Resend)
RESEND_API_KEY=your-resend-api-key
RESEND_FROM_EMAIL=noreply@yourdomain.com

# AI Services (Optional)
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment

# Application URL
APP_URL=http://localhost:8000
```

## Migration from Old Codebase

### What's Removed
- ❌ Flask application (main.py with Flask)
- ❌ Jinja2 templates (templates/)
- ❌ Flask routes (routes/)
- ❌ Flask-specific dependencies
- ❌ Server-side rendering

### What's Kept
- ✅ Database models (migrated to FastAPI)
- ✅ Email service (pyFunctions/email_service.py)
- ✅ Business logic utilities
- ✅ Existing database (compatible)

### What's New
- 🆕 FastAPI backend (api/)
- 🆕 React frontend (frontend/src/)
- 🆕 Modern architecture
- 🆕 API-first design
- 🆕 Theme system

## Testing

### Backend Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"TestPass123"}'

# Test login
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'
```

### Frontend Testing
- Visit http://localhost:5173
- Register new account
- Login with credentials
- Navigate to dashboard
- Test theme toggle
- Test logout

## Deployment

### Vercel Deployment

**Frontend**:
```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "framework": "vite"
}
```

**Backend** (separate deployment):
```json
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### Docker Deployment

**Backend Dockerfile**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements-fastapi.txt .
RUN pip install -r requirements-fastapi.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile**:
```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

## Security

- ✅ JWT tokens with expiration
- ✅ Password hashing with bcrypt
- ✅ SQL injection protection (ORM)
- ✅ CORS configuration
- ✅ Input validation (Pydantic)
- ✅ Rate limiting (to be added)
- ✅ HTTPS in production

## Performance

- ⚡ Async FastAPI for high concurrency
- ⚡ React with Vite for fast builds
- ⚡ Code splitting
- ⚡ Lazy loading
- ⚡ Database connection pooling
- ⚡ Static file caching

## Next Steps

1. **Remove Legacy Code**
   - Delete old Flask routes
   - Delete Jinja2 templates
   - Clean up unused dependencies

2. **Add Features**
   - Implement all simulation endpoints
   - Add real-time updates (WebSockets)
   - Implement file uploads
   - Add more analytics

3. **Testing**
   - Add unit tests (pytest)
   - Add integration tests
   - Add E2E tests (Playwright)

4. **Documentation**
   - API documentation
   - Component documentation
   - Deployment guides

## Troubleshooting

**Backend won't start**:
- Check if all dependencies are installed
- Verify database file exists and is accessible
- Check environment variables
- Review app.py for import errors

**Frontend won't load**:
- Check if backend is running on port 8000
- Verify VITE_API_URL is correct
- Check browser console for errors
- Clear localStorage if auth issues

**Database errors**:
- Delete users.db and restart (development only)
- Check SQLAlchemy connection string
- Verify database permissions

## Support

For issues, check:
- FastAPI docs: https://fastapi.tiangolo.com/
- React docs: https://react.dev/
- Vite docs: https://vite.dev/

## License

Same as CyberVantage main project.
