"""
VirusTotal API integration service for CyberVantage.
"""
import os
import requests
from flask import current_app

class ThreatService:
    """
    Service for checking URLs and files for potential threats using VirusTotal API.
    """
    
    def __init__(self):
        """
        Initialize the threat service with API key.
        """
        self.api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = 'https://www.virustotal.com/api/v3'
        self.headers = {
            'x-apikey': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def check_url(self, url):
        """
        Check a URL for potential threats using VirusTotal API.
        
        Args:
            url (str): The URL to check
            
        Returns:
            dict: Scan results from VirusTotal
        """
        try:
            # URL ID must be in base64 format
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')
            
            # Check if URL analysis already exists
            response = requests.get(
                f"{self.base_url}/urls/{url_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json().get('data', {}).get('attributes', {})
            
            # If URL not previously scanned, submit for analysis
            response = requests.post(
                f"{self.base_url}/urls",
                headers=self.headers,
                data={'url': url}
            )
            
            if response.status_code == 200:
                # Return URL ID so client can poll for results
                return {'scan_id': url_id, 'message': 'URL submitted for analysis'}
            
            return {'error': 'Failed to scan URL', 'status_code': response.status_code}
        
        except Exception as e:
            current_app.logger.error(f"VirusTotal API error: {str(e)}")
            return {'error': str(e)}
    
    def check_file(self, file_path):
        """
        Check a file for malware using VirusTotal API.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            dict: Scan results from VirusTotal
        """
        try:
            # Get upload URL
            response = requests.get(
                f"{self.base_url}/files/upload_url",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {'error': 'Failed to get upload URL', 'status_code': response.status_code}
            
            upload_url = response.json().get('data')
            
            # Upload file
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(
                    upload_url,
                    headers={'x-apikey': self.api_key},
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                file_id = data.get('data', {}).get('id')
                return {'scan_id': file_id, 'message': 'File submitted for analysis'}
            
            return {'error': 'Failed to upload file', 'status_code': response.status_code}
        
        except Exception as e:
            current_app.logger.error(f"VirusTotal API error: {str(e)}")
            return {'error': str(e)}
    
    def get_threat_intel(self, limit=10):
        """
        Get latest threat intelligence information.
        
        Args:
            limit (int): Number of threat reports to retrieve
            
        Returns:
            list: Recent threat reports
        """
        try:
            # This is a placeholder as VirusTotal doesn't have a direct "threat intel" endpoint
            # In a real implementation, you might use other endpoints or services
            return [
                {
                    'type': 'ransomware',
                    'name': 'Sample Threat',
                    'severity': 'high',
                    'date_reported': '2023-01-01',
                    'description': 'This is a sample threat description.'
                }
            ]
        except Exception as e:
            current_app.logger.error(f"Threat intelligence error: {str(e)}")
            return []

# Create service instance
threat_service = ThreatService()

# Export functions
check_url = threat_service.check_url
check_file = threat_service.check_file
get_threat_intel = threat_service.get_threat_intel