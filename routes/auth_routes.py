"""
Authentication routes - login, register, logout
"""
import datetime
import jwt
import time
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from models.database import User, db
from collections import defaultdict, deque

auth_bp = Blueprint('auth', __name__)

# Simple in-memory rate limiting (for production, use Redis or database)
login_attempts = defaultdict(deque)
registration_attempts = defaultdict(deque)
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
MAX_LOGIN_ATTEMPTS = 5
MAX_REGISTRATION_ATTEMPTS = 3

def is_rate_limited(ip_address, attempts_dict, max_attempts):
    """Check if IP is rate limited"""
    now = time.time()
    # Clean old attempts
    while attempts_dict[ip_address] and attempts_dict[ip_address][0] < now - RATE_LIMIT_WINDOW:
        attempts_dict[ip_address].popleft()
    
    return len(attempts_dict[ip_address]) >= max_attempts

def record_attempt(ip_address, attempts_dict):
    """Record an attempt for rate limiting"""
    attempts_dict[ip_address].append(time.time())

def token_required(f):
    """Token required decorator with improved security"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        import time
        
        token = session.get('token')
        if not token:
            # Add small random delay to prevent timing attacks
            time.sleep(0.01 + (hash(str(time.time())) % 100) / 10000)
            return redirect(url_for('auth.login'))

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                # Add small random delay to prevent timing attacks
                time.sleep(0.01 + (hash(str(time.time())) % 100) / 10000)
                return redirect(url_for('auth.login'))
        except jwt.ExpiredSignatureError:
            # Token has expired
            session.clear()
            return redirect(url_for('auth.logout') + '?timeout=true')
        except (jwt.InvalidTokenError, Exception):
            # Invalid token or other JWT errors
            session.clear()
            time.sleep(0.01 + (hash(str(time.time())) % 100) / 10000)
            return redirect(url_for('auth.login'))

        return f(current_user, *args, **kwargs)

    return decorated

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check rate limiting
        if is_rate_limited(ip_address, registration_attempts, MAX_REGISTRATION_ATTEMPTS):
            return jsonify({"error": "Too many registration attempts. Please try again in 5 minutes."}), 429
        
        record_attempt(ip_address, registration_attempts)
        
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Input validation
        if not name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        # Email validation
        try:
            validate_email(email)
        except EmailNotValidError as e:
            return jsonify({"error": str(e)}), 400

        # Password match check
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        # Enhanced password strength check
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
        # Check for complexity
        if not any(c.isupper() for c in password):
            return jsonify({"error": "Password must contain at least one uppercase letter"}), 400
        
        if not any(c.islower() for c in password):
            return jsonify({"error": "Password must contain at least one lowercase letter"}), 400
        
        if not any(c.isdigit() for c in password):
            return jsonify({"error": "Password must contain at least one number"}), 400

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
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Check rate limiting
        if is_rate_limited(ip_address, login_attempts, MAX_LOGIN_ATTEMPTS):
            return jsonify({"error": "Too many login attempts. Please try again in 5 minutes."}), 429
        
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Input validation
        if not email or not password:
            record_attempt(ip_address, login_attempts)
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            record_attempt(ip_address, login_attempts)
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT with shorter expiration for security
        from flask import current_app
        token = jwt.encode(
            {
                "user_id": user.id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
                "iat": datetime.datetime.utcnow()
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

def admin_required(f):
    """Admin required decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # This should be called after token_required
        current_user = args[0] if args else None
        if not current_user or not current_user.is_admin_user():
            from flask import flash
            flash("Admin access required.", "error")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/admin/users')
@token_required
@admin_required
def admin_users(current_user):
    """Admin view to see all registered users"""
    users = User.query.all()
    return render_template('admin_users.html', 
                         users=users, 
                         username=current_user.name,
                         current_user=current_user)

@auth_bp.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@token_required 
@admin_required
def make_admin(current_user, user_id):
    """Make a user an admin"""
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    from flask import flash
    flash(f"Successfully made {user.name} an admin.", "success")
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            return jsonify({"error": "Email is required"}), 400
            
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.generate_reset_token()
            db.session.commit()
            
            # In a real application, you would send an email here
            # For demo purposes, we'll show the reset link
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Log the reset request for demo
            print(f"Password reset requested for {email}")
            print(f"Reset URL: {reset_url}")
            
            from flask import flash
            flash(f"Password reset instructions have been sent to {email}. Check the console for the reset link.", "info")
        else:
            # Don't reveal that email doesn't exist for security
            from flask import flash
            flash(f"If an account with {email} exists, password reset instructions have been sent.", "info")
            
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password_request.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user = User.query.filter_by(password_reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        from flask import flash
        flash("Invalid or expired password reset token.", "error")
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Password validation (same as registration)
        if not password:
            return jsonify({"error": "Password is required"}), 400
            
        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400
            
        # Enhanced password strength check
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400
        
        if not any(c.isupper() for c in password):
            return jsonify({"error": "Password must contain at least one uppercase letter"}), 400
        
        if not any(c.islower() for c in password):
            return jsonify({"error": "Password must contain at least one lowercase letter"}), 400
        
        if not any(c.isdigit() for c in password):
            return jsonify({"error": "Password must contain at least one number"}), 400
        
        # Update password and clear reset token
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        
        from flask import flash
        flash("Your password has been reset successfully. Please log in.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@auth_bp.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@token_required
@admin_required
def admin_reset_password(current_user, user_id):
    """Admin function to reset any user's password"""
    user = User.query.get_or_404(user_id)
    
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    # Validation
    if not new_password or not confirm_password:
        from flask import flash
        flash("Both password fields are required.", "error")
        return redirect(url_for('auth.admin_users'))
    
    if new_password != confirm_password:
        from flask import flash
        flash("Passwords do not match.", "error")
        return redirect(url_for('auth.admin_users'))
    
    # Enhanced password strength check
    if len(new_password) < 8:
        from flask import flash
        flash("Password must be at least 8 characters long.", "error")
        return redirect(url_for('auth.admin_users'))
    
    if not any(c.isupper() for c in new_password):
        from flask import flash
        flash("Password must contain at least one uppercase letter.", "error")
        return redirect(url_for('auth.admin_users'))
    
    if not any(c.islower() for c in new_password):
        from flask import flash
        flash("Password must contain at least one lowercase letter.", "error")
        return redirect(url_for('auth.admin_users'))
    
    if not any(c.isdigit() for c in new_password):
        from flask import flash
        flash("Password must contain at least one number.", "error")
        return redirect(url_for('auth.admin_users'))
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    from flask import flash
    flash(f"Password successfully reset for {user.name}.", "success")
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@token_required
@admin_required 
def delete_user(current_user, user_id):
    """Admin function to delete a user account"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        from flask import flash
        flash("You cannot delete your own account.", "error")
        return redirect(url_for('auth.admin_users'))
    
    # Store user name for confirmation message
    user_name = user.name
    
    # Delete related records first (to maintain referential integrity)
    from models.database import SimulationResponse, SimulationSession
    SimulationResponse.query.filter_by(user_id=user.id).delete()
    SimulationSession.query.filter_by(user_id=user.id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    from flask import flash
    flash(f"User {user_name} has been successfully deleted.", "success")
    return redirect(url_for('auth.admin_users'))