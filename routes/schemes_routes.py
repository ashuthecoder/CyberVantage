"""
Government Schemes routes - search and display government schemes
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from routes.auth_routes import token_required
from models.database import User, GovernmentScheme, db
from sqlalchemy import or_, and_

schemes_bp = Blueprint('schemes', __name__)

@schemes_bp.route('/schemes')
@token_required
def schemes_search(current_user):
    """Main schemes search page"""
    return render_template('schemes_search.html', username=current_user.name, current_user=current_user)

@schemes_bp.route('/api/schemes/search')
@token_required
def api_schemes_search(current_user):
    """API endpoint for searching schemes"""
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '')
    
    # Build base query
    schemes_query = GovernmentScheme.query.filter(GovernmentScheme.is_active == True)
    
    # Apply text search if query provided
    if query:
        schemes_query = schemes_query.filter(
            or_(
                GovernmentScheme.title.ilike(f'%{query}%'),
                GovernmentScheme.description.ilike(f'%{query}%'),
                GovernmentScheme.category.ilike(f'%{query}%'),
                GovernmentScheme.target_audience.ilike(f'%{query}%')
            )
        )
    
    # Apply category filter
    if category:
        schemes_query = schemes_query.filter(GovernmentScheme.category == category)
    
    # Get personalized results based on user profile
    personalized_schemes = []
    general_schemes = []
    
    all_schemes = schemes_query.all()
    
    for scheme in all_schemes:
        is_personalized = False
        
        # Check if scheme matches user's location
        if current_user.location and scheme.location:
            if (current_user.location.lower() in scheme.location.lower() or 
                scheme.location.lower() == 'all' or 
                scheme.location.lower() == 'national'):
                is_personalized = True
        
        # Check if scheme matches user's role
        if current_user.role and scheme.target_audience:
            if current_user.role.lower() in scheme.target_audience.lower():
                is_personalized = True
        
        scheme_data = {
            'id': scheme.id,
            'title': scheme.title,
            'description': scheme.description,
            'category': scheme.category,
            'target_audience': scheme.target_audience,
            'location': scheme.location,
            'eligibility': scheme.eligibility,
            'benefits': scheme.benefits,
            'how_to_apply': scheme.how_to_apply,
            'official_url': scheme.official_url,
            'source_website': scheme.source_website
        }
        
        if is_personalized:
            personalized_schemes.append(scheme_data)
        else:
            general_schemes.append(scheme_data)
    
    return jsonify({
        'personalized_schemes': personalized_schemes,
        'general_schemes': general_schemes,
        'user_profile': {
            'location': current_user.location,
            'role': current_user.role
        },
        'total_results': len(all_schemes)
    })

@schemes_bp.route('/schemes/<int:scheme_id>')
@token_required
def scheme_details(current_user, scheme_id):
    """Show detailed view of a specific scheme"""
    scheme = GovernmentScheme.query.get_or_404(scheme_id)
    return render_template('scheme_details.html', scheme=scheme, username=current_user.name)

@schemes_bp.route('/profile/update', methods=['POST'])
@token_required
def update_profile(current_user):
    """Update user's profile information for better scheme recommendations"""
    try:
        location = request.form.get('location', '').strip()
        role = request.form.get('role', '').strip()
        
        current_user.location = location if location else None
        current_user.role = role if role else None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully!',
            'location': current_user.location,
            'role': current_user.role
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating profile: {str(e)}'
        }), 500