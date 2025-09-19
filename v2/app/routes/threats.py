"""
Threat checking routes for CyberVantage.
"""
from flask import Blueprint, request, jsonify
from app.utils.auth import token_required
from app.services.threat_service import check_url, check_file, get_threat_intel

bp = Blueprint('threats', __name__, url_prefix='/api/threats')

@bp.route('/url', methods=['POST'])
@token_required
def scan_url():
    """
    Scan a URL for potential threats.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    url = data['url']
    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': 'Please provide a valid URL starting with http:// or https://'}), 400
    
    # Scan URL using VirusTotal
    scan_result = check_url(url)
    
    return jsonify({'scan_result': scan_result, 'message': 'URL scan initiated'}), 200

@bp.route('/file', methods=['POST'])
@token_required
def scan_file():
    """
    Scan a file for malware.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save the uploaded file temporarily
    import tempfile
    import os
    
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # Scan file using VirusTotal
        scan_result = check_file(temp_file_path)
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return jsonify({'scan_result': scan_result, 'message': 'File scan initiated'}), 200
        
    except Exception as e:
        # Clean up on error
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        return jsonify({'error': 'File processing failed'}), 500

@bp.route('/intel', methods=['GET'])
@token_required
def get_intelligence():
    """
    Get latest threat intelligence information.
    """
    limit = request.args.get('limit', 10, type=int)
    
    # Get threat intelligence using VirusTotal or other sources
    intel_data = get_threat_intel(limit=limit)
    
    return jsonify({'intel': intel_data, 'count': len(intel_data)}), 200