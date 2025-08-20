# This file makes the pyFunctions directory a Python package
# It exposes specific functions for import
from .email_generation import generate_ai_email, evaluate_explanation
from .template_emails import get_template_email
from .simulation import generate_unique_simulation_email

__all__ = [
    'generate_ai_email', 
    'evaluate_explanation',
    'get_template_email',
    'generate_unique_simulation_email'
]