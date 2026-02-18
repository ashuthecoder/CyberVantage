# CyberVantage

**CyberVantage** is an educational web platform designed to teach school students about spam emails, phishing, and basic cyber safety in a fun and interactive way.

## ⚠️ Prerequisites

**Azure PostgreSQL Database Required**: This application requires an Azure PostgreSQL database. SQLite is not supported.

- See [Database Setup Guide](docs/DATABASE_REQUIRED.md) for quick setup
- See [Azure Database Setup](docs/AZURE_DATABASE_SETUP.md) for detailed instructions

## 📚 Project Overview

The project is divided into **four phases**:  
1. **Learning** – Learn about spam emails through slides and MCQs.  
2. **Simulation** – Experience safe, AI-generated spam emails and test your skills.  
3. **Analysis** – Get personalized feedback and learning paths based on your performance.  
4. **Final Assignment** – Create your own fake spam email and let AI rate its realism.

---

## 🚀 Features

### **Phase 1: Learning**
- Interactive educational content about phishing, spam, and cyber safety
- PPT slides and cyber safety tips
- Multiple-choice quizzes with instant feedback
- Progress tracking to monitor student advancement

### **Phase 2: Simulation**
- Two-part phishing email simulation:
  - **Part 1:** Classify predefined emails as *Safe* ✅ or *Spam* 🚫
  - **Part 2:** Analyze AI-generated emails and explain your reasoning
- Realistic but safe email simulations powered by Google's Gemini AI
- Personalized feedback on each response
- All user activity is securely logged under their profile

### **Phase 3: Analysis**
- Comprehensive performance summaries showing accuracy and improvement areas
- Detailed statistics on your phishing detection abilities
- Personalized learning paths to address specific weak points
- Badges and certificates for achieving milestones

### **Phase 4: Final Assignment**
- Students create their own fake spam email to demonstrate understanding
- AI (Google Gemini) rates the email on a **1–10 scale**
- Detailed feedback on realism, tactics used, and missed opportunities
- Apply what you've learned in a creative, hands-on way

---

## 🛡 Security Features

- **JWT Authentication** for secure, stateless user sessions
- **Password hashing** with bcrypt and salting for secure credential storage
- **Input sanitization** for all forms to prevent injection attacks
- **CSRF protection** via Flask-WTF with csrf_token in all forms
- **Email validation** using `email-validator` library
- **Encrypted database** using AES-256 for sensitive data storage
- **HTML sanitization** using `bleach` for any rich text input
- All simulated phishing links are safely contained within the platform

---

## 🏗 Tech Stack

### Backend
- **Flask** (Python web framework)
- **SQLAlchemy** + Alembic (ORM & database migrations)
- **JWT** (pyjwt) for authentication tokens
- **bcrypt** for secure password hashing
- **cryptography** for data encryption

### Frontend
- **HTML/CSS/JavaScript** with Jinja2 templating
- **Responsive design** for desktop and mobile devices
- **Plotly/Matplotlib** for performance visualizations

### AI Integration
- **Google Gemini API** (`google-generativeai`)
  - Generates realistic phishing emails for training
  - Evaluates user explanations and provides feedback
  - Rates student-created phishing emails

### Database
- Configurable database backend:
  - PostgreSQL (production)
  - MySQL (alternative)
  - SQLite (development/testing)

- Google Gemini API key
- Git (for cloning the repository)
