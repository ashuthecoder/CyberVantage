from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import bcrypt
import jwt
import datetime
from email_validator import validate_email, EmailNotValidError
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Config
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET", "dev_secret")
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET", "jwt_secret")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv("CSRF_SECRET", "csrf_secret")

# Init
db = SQLAlchemy(app)
csrf = CSRFProtect(app)

# Encryption key for sensitive DB fields
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
fernet = Fernet(ENCRYPTION_KEY)

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    encrypted_data = db.Column(db.LargeBinary, nullable=True)  # For sensitive info

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

# Token required decorator for protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return redirect(url_for('login'))
        
        try:
            # Decode the token
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return redirect(url_for('login'))
        except:
            return redirect(url_for('login'))
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def welcome():
    return render_template("welcome.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get("name").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Email validation
        try:
            validate_email(email)
        except EmailNotValidError as e:
            return jsonify({"error": str(e)}), 400

        # Password match check
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # Password strength check
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        # Check if email exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        # Create user
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )
        
        # Store token in session instead of returning it
        session['token'] = token
        session['user_name'] = user.name
        
        # Redirect to dashboard
        return redirect(url_for('dashboard'))

    return render_template("login.html")

# Dashboard route
@app.route('/dashboard')
@token_required
def dashboard(current_user):
    return render_template('dashboard.html', username=current_user.name)

# Learn section route
@app.route('/learn')
@token_required
def learn(current_user):
    return render_template('learn.html', username=current_user.name)

# Simulate section route
@app.route('/simulate')
@token_required
def simulate(current_user):
    return render_template('simulate.html', username=current_user.name)

# Analysis section route
@app.route('/analysis')
@token_required
def analysis(current_user):
    return render_template('analysis.html', username=current_user.name)

# Logout route
@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('user_name', None)
    return redirect(url_for('login'))

# Utility route to encrypt sensitive data
@app.route('/encrypt/<string:data>')
def encrypt_data(data):
    encrypted = fernet.encrypt(data.encode())
    return {"encrypted": encrypted.decode()}

@app.route('/decrypt/<string:data>')
def decrypt_data(data):
    decrypted = fernet.decrypt(data.encode()).decode()
    return {"decrypted": decrypted}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)