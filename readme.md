# CyberVantage

**CyberVantage** is an educational web platform designed to teach school students about spam emails, phishing, and basic cyber safety in a fun and interactive way.  
The project is divided into **four phases**:  
1. **Learning** – Learn about spam emails through slides and MCQs.  
2. **Simulation** – Experience safe, AI-generated spam emails and test your skills.  
3. **Analysis** – Get personalized feedback and learning paths based on your performance.  
4. **Final Assignment** – Create your own fake spam email and let AI rate its realism.

---

## 🚀 Features

### **Phase 1: Learning**
- PPT slides and cyber safety tips.
- Multiple-choice quizzes with instant feedback.
- Progress tracking.

### **Phase 2: Simulation**
- **Part 1:** Classify emails as *Safe* ✅ or *Spam* 🚫.
- **Part 2:** Emails contain safe hyperlinks; track if the user clicks them.
- All click data is logged (encrypted) under the user profile.

### **Phase 3: Analysis**
- View performance summaries, accuracy, and mistakes.
- Personalized learning paths to address weak points.
- Badges and certificates for achievements.

### **Phase 4: Final Assignment**
- Students create their own fake spam email.
- AI (Gemini API) rates the email on a **1–10 scale**.
- Feedback on realism, tactics, and missed opportunities.

---

## 🛡 Security Features
- **JWT Authentication** for secure login.
- **Password hashing** with bcrypt.
- **Input sanitization** for all forms.
- **Encrypted database** using AES-256 for sensitive data.
- All clickable links in simulation are routed through a safe server-side handler.

---

## 🏗 Tech Stack

**Backend:**
- Flask (Python)
- SQLAlchemy + Alembic (ORM & migrations)
- JWT (pyjwt)
- bcrypt (password hashing)
- cryptography (data encryption)

**Frontend:**
- HTML, CSS, JavaScript (Jinja2 templates)
- Plotly/Matplotlib for visualizations

**AI:**
- Google Gemini API (`google-generativeai`) for spam email generation & scoring.

**Database:**
- PostgreSQL / MySQL / SQLite (configurable)
