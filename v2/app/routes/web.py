"""
Web UI routes for CyberVantage V2.
This blueprint provides the user interface routes that match the V1 application.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app.utils.auth import token_required
from app.forms import LoginForm, RegisterForm
from app.models.user import User, db
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('web', __name__, url_prefix='')

@bp.route('/')
def welcome():
    """
    Render the welcome page.
    """
    return render_template('welcome.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    """
    form = LoginForm()
    
    if form.validate_on_submit():
        # Get form data
        email = form.email.data
        password = form.password.data
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        # Verify password
        if user and check_password_hash(user.password, password):
            # Log user in
            login_user(user)
            session['token'] = 'dummy_token'
            
            # Redirect to dashboard or next page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('web.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    """
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Get form data
        email = form.email.data
        username = form.username.data
        password = form.password.data
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password)
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        # Flash message and redirect to login
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('web.login'))
    
    return render_template('register.html', form=form)

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Render the user dashboard.
    """
    return render_template('dashboard.html')

@bp.route('/learn')
@login_required
def learn():
    """
    Render the learning page.
    """
    return render_template('learn.html')

@bp.route('/simulate')
@login_required
def simulate():
    """
    Redirect to the simulation page.
    """
    return redirect(url_for('web_simulation.simulate'))

@bp.route('/analysis')
@login_required
def analysis():
    """
    Render the analysis page.
    """
    return render_template('analysis.html')

@bp.route('/check_threats')
@login_required
def check_threats():
    """
    Render the threat checking page.
    """
    return render_template('check_threats.html')

@bp.route('/logout')
def logout():
    """
    Handle user logout.
    """
    logout_user()
    session.clear()
    return redirect(url_for('web.welcome'))

@bp.route('/phishing_assignment')
@login_required
def phishing_assignment():
    """
    Render the phishing assignment page.
    """
    return render_template('phishing_assignment.html')

@bp.route('/phishing_evaluation', methods=['GET', 'POST'])
@login_required
def phishing_evaluation():
    """
    Render the phishing evaluation page.
    """
    return render_template('phishing_evaluation.html')