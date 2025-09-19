"""
Web UI routes for CyberVantage V2.
This blueprint provides the user interface routes that match the V1 application.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response
from app.utils.auth import token_required
from app.forms import LoginForm, RegisterForm

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
        # In a real app, we would validate credentials here
        # For now, just set a session token and redirect to dashboard
        session['token'] = 'dummy_token'
        return redirect(url_for('web.dashboard'))
    
    return render_template('login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    """
    form = RegisterForm()
    
    if form.validate_on_submit():
        # In a real app, we would create the user here
        flash('Registration successful! Please log in.')
        return redirect(url_for('web.login'))
    
    return render_template('register.html', form=form)

@bp.route('/dashboard')
@token_required
def dashboard():
    """
    Render the user dashboard.
    """
    # Just check if the token exists in the session
    if not session.get('token'):
        # Redirect to login if no token
        return redirect(url_for('web.login'))
    
    return render_template('dashboard.html')

@bp.route('/learn')
@token_required
def learn():
    """
    Render the learning page.
    """
    return render_template('learn.html')

@bp.route('/simulate')
@token_required
def simulate():
    """
    Render the simulation page.
    """
    return render_template('simulate.html')

@bp.route('/analysis')
@token_required
def analysis():
    """
    Render the analysis page.
    """
    return render_template('analysis.html')

@bp.route('/check_threats')
@token_required
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
    session.clear()
    return redirect(url_for('web.welcome'))

@bp.route('/phishing_assignment')
@token_required
def phishing_assignment():
    """
    Render the phishing assignment page.
    """
    return render_template('phishing_assignment.html')

@bp.route('/phishing_evaluation', methods=['GET', 'POST'])
@token_required
def phishing_evaluation():
    """
    Render the phishing evaluation page.
    """
    return render_template('phishing_evaluation.html')