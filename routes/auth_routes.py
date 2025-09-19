"""
Authentication routes - login, register, logout
"""
import datetime
import jwt
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from models.database import User, db

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Token required decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        token = session.get('token')
        if not token:
            return redirect(url_for('auth.login'))

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return redirect(url_for('auth.login'))
        except:
            return redirect(url_for('auth.login'))

        return f(current_user, *args, **kwargs)

    return decorated

@auth_bp.route('/register', methods=['GET', 'POST'])
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

        return redirect(url_for('auth.login'))

    return render_template("register.html")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email").strip()
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT
        from flask import current_app
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            current_app.config['JWT_SECRET_KEY'],
            algorithm="HS256"
        )

        # Store token in session
        session['token'] = token
        session['user_name'] = user.name

        # Redirect to dashboard
        return redirect(url_for('dashboard'))

    return render_template("login.html")

@auth_bp.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('user_name', None)
    session.pop('simulation_phase', None)
    session.pop('current_email_id', None)
    session.pop('simulation_id', None)
    session.pop('phase2_emails_completed', None)
    session.pop('active_phase2_email_id', None)
    
    # Check if timeout parameter is present
    from flask import flash
    timeout = request.args.get('timeout', False)
    if timeout:
        flash("Your session has expired due to inactivity. Please login again.")
    
    return redirect(url_for('auth.login'))

@auth_bp.route('/extend_session', methods=['POST'])
@token_required
def extend_session(current_user):
    # Renew the JWT token with a fresh expiry
    from flask import current_app
    token = jwt.encode(
        {
            "user_id": current_user.id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        },
        current_app.config['JWT_SECRET_KEY'],
        algorithm="HS256"
    )
    
    # Update the session token
    session['token'] = token
    
    return jsonify({"success": True, "message": "Session extended"}), 200