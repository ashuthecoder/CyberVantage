"""
JWT token handling utilities for CyberVantage.
"""
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

def create_token(user_id):
    """
    Create a JWT token for user authentication.
    
    Args:
        user_id (int): User ID to encode in the token
        
    Returns:
        str: JWT token
    """
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            os.getenv('SECRET_KEY', 'default-dev-key'),
            algorithm='HS256'
        )
    except Exception as e:
        current_app.logger.error(f"Token creation error: {str(e)}")
        return None

def validate_token(token):
    """
    Validate a JWT token.
    
    Args:
        token (str): JWT token to validate
        
    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        return jwt.decode(
            token,
            os.getenv('SECRET_KEY', 'default-dev-key'),
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """
    Decorator for routes that require token authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split('Bearer ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        # Validate token
        payload = validate_token(token)
        if not payload:
            return jsonify({'message': 'Invalid or expired token'}), 401
        
        # Add user_id to request context
        request.user_id = payload['sub']
        
        return f(*args, **kwargs)
    
    return decorated