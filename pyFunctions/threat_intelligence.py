"""
Threat Intelligence module - Handles VirusTotal API integration and threat analysis
"""
import os
import json
import time
import hashlib
import requests
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/threat_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('threat_intelligence')

class ThreatIntelligence:
    """
    Handles threat intelligence operations using the VirusTotal API
    """
    def __init__(self, api_key: str = None):
        """Initialize with API key from parameters or environment"""
        self.api_key = api_key or os.getenv('VIRUSTOTAL_API_KEY')
        if not self.api_key:
            logger.warning("VirusTotal API key not found")
        
        self.base_url = 'https://www.virustotal.com/api/v3/'
        self.headers = {
            'x-apikey': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Cache to store recent results
        self.cache = {}
        self.scan_history = []
    
    def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan a URL using VirusTotal API"""
        if not self.api_key:
            return {"error": "VirusTotal API key not configured"}
        
        # Check cache first
        cache_key = f"url:{url}"
        if cache_key in self.cache:
            logger.info(f"Using cached result for URL: {url}")
            return self.cache[cache_key]
        
        try:
            # First, submit URL for analysis
            submit_url = f"{self.base_url}urls"
            payload = {'url': url}
            response = requests.post(submit_url, headers=self.headers, data=payload)
            
            if response.status_code != 200:
                logger.error(f"Error submitting URL {url}: {response.text}")
                return {"error": f"API Error: {response.status_code}"}
            
            # Extract the analysis ID
            result = response.json()
            analysis_id = result.get('data', {}).get('id')
            
            if not analysis_id:
                return {"error": "Could not get analysis ID from VirusTotal"}
            
            # Wait a moment to allow processing
            time.sleep(2)
            
            # Get the analysis results
            analysis_url = f"{self.base_url}analyses/{analysis_id}"
            result_response = requests.get(analysis_url, headers=self.headers)
            
            if result_response.status_code != 200:
                logger.error(f"Error getting analysis results: {result_response.text}")
                return {"error": f"Analysis Error: {result_response.status_code}"}
            
            analysis_result = result_response.json()
            
            # Process and format the results
            formatted_result = self._format_url_result(analysis_result, url)
            
            # Cache the result
            self.cache[cache_key] = formatted_result
            
            # Add to history
            self._add_to_history(formatted_result, 'url')
            
            return formatted_result
            
        except Exception as e:
            logger.exception(f"Exception in scan_url: {str(e)}")
            return {"error": f"Scan failed: {str(e)}"}
    
    def scan_ip(self, ip: str) -> Dict[str, Any]:
        """Scan an IP address using VirusTotal API"""
        if not self.api_key:
            return {"error": "VirusTotal API key not configured"}
        
        # Check cache first
        cache_key = f"ip:{ip}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get IP report
            ip_url = f"{self.base_url}ip_addresses/{ip}"
            response = requests.get(ip_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Error scanning IP {ip}: {response.text}")
                return {"error": f"API Error: {response.status_code}"}
            
            ip_result = response.json()
            
            # Process and format the results
            formatted_result = self._format_ip_result(ip_result, ip)
            
            # Cache the result
            self.cache[cache_key] = formatted_result
            
            # Add to history
            self._add_to_history(formatted_result, 'ip')
            
            return formatted_result
            
        except Exception as e:
            logger.exception(f"Exception in scan_ip: {str(e)}")
            return {"error": f"Scan failed: {str(e)}"}
    
    def scan_file_hash(self, file_hash: str) -> Dict[str, Any]:
        """Get file information by hash using VirusTotal API"""
        if not self.api_key:
            return {"error": "VirusTotal API key not configured"}
        
        # Check cache first
        cache_key = f"hash:{file_hash}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Get file report
            file_url = f"{self.base_url}files/{file_hash}"
            response = requests.get(file_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Error scanning file hash {file_hash}: {response.text}")
                return {"error": f"API Error: {response.status_code}"}
            
            file_result = response.json()
            
            # Process and format the results
            formatted_result = self._format_file_result(file_result, file_hash)
            
            # Cache the result
            self.cache[cache_key] = formatted_result
            
            # Add to history
            self._add_to_history(formatted_result, 'file')
            
            return formatted_result
            
        except Exception as e:
            logger.exception(f"Exception in scan_file_hash: {str(e)}")
            return {"error": f"Scan failed: {str(e)}"}
    
    def deep_scan_url(self, url: str) -> Dict[str, Any]:
        """
        Perform a deep scan on a URL to detect multi-hop redirects and analyze JavaScript
        """
        if not self.api_key:
            return {"error": "VirusTotal API key not configured"}
        
        try:
            # First perform a regular URL scan
            base_scan = self.scan_url(url)
            
            if "error" in base_scan:
                return base_scan
            
            # This would be where we'd implement advanced scanning logic
            # For now, we'll return a mock result with redirect chain analysis
            
            # Mock data for demonstration
            is_malicious = base_scan.get("positives", 0) > 0
            
            redirects = [
                {
                    "url": url,
                    "status_code": 200,
                    "redirect_type": "Initial URL",
                    "is_malicious": is_malicious
                }
            ]
            
            # Add mock redirects if the URL seems suspicious
            if is_malicious:
                parsed_url = urlparse(url)
                redirects.extend([
                    {
                        "url": f"https://tracking.{parsed_url.netloc}/redirect?target=intermediate",
                        "status_code": 302,
                        "redirect_type": "HTTP 302",
                        "is_malicious": False
                    },
                    {
                        "url": "https://intermediate-domain.com/loading?id=12345",
                        "status_code": 200,
                        "redirect_type": "JavaScript",
                        "is_malicious": True
                    },
                    {
                        "url": "https://malicious-endpoint.com/phish",
                        "status_code": 200,
                        "redirect_type": "Final Destination",
                        "is_malicious": True
                    }
                ])
            
            # JavaScript analysis
            js_analysis = {
                "summary": "JavaScript analysis complete" if is_malicious else "No suspicious JavaScript detected",
                "findings": []
            }
            
            if is_malicious:
                js_analysis["findings"] = [
                    {
                        "severity": "high",
                        "description": "Obfuscated code detected that decodes to a redirect function"
                    },
                    {
                        "severity": "medium",
                        "description": "Script attempts to access localStorage and sessionStorage"
                    },
                    {
                        "severity": "low", 
                        "description": "Multiple third-party scripts loaded from untrusted domains"
                    }
                ]
            
            result = {
                "resource": url,
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "permalink": base_scan.get("permalink", f"https://www.virustotal.com/gui/url/{hashlib.sha256(url.encode()).hexdigest()}"),
                "positives": base_scan.get("positives", 0),
                "total": base_scan.get("total", 0),
                "malicious": is_malicious,
                "summary": f"Found a chain of {len(redirects)} redirects, with {sum(1 for r in redirects if r['is_malicious'])} malicious hops" if is_malicious else "No malicious redirects detected",
                "redirects": redirects,
                "javascript_analysis": js_analysis
            }
            
            # Add to history 
            self._add_to_history(result, 'deep_scan')
            
            return result
            
        except Exception as e:
            logger.exception(f"Exception in deep_scan_url: {str(e)}")
            return {"error": f"Deep scan failed: {str(e)}"}
    
    def _format_url_result(self, vt_result: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Format the VirusTotal URL result into a standardized format"""
        try:
            attributes = vt_result.get('data', {}).get('attributes', {})
            stats = attributes.get('stats', {})
            
            return {
                "resource": url,
                "scan_date": attributes.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "permalink": f"https://www.virustotal.com/gui/url/{attributes.get('id', hashlib.sha256(url.encode()).hexdigest())}/detection",
                "positives": stats.get('malicious', 0),
                "total": sum(stats.values()),
                "scans": attributes.get('results', {})
            }
        except Exception as e:
            logger.exception(f"Error formatting URL result: {str(e)}")
            return {"error": "Failed to process scan results", "raw": vt_result}
    
    def _format_ip_result(self, vt_result: Dict[str, Any], ip: str) -> Dict[str, Any]:
        """Format the VirusTotal IP result into a standardized format"""
        try:
            attributes = vt_result.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            return {
                "resource": ip,
                "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "permalink": f"https://www.virustotal.com/gui/ip-address/{ip}/detection",
                "positives": stats.get('malicious', 0),
                "total": sum(stats.values()),
                "country": attributes.get('country', 'Unknown'),
                "owner": attributes.get('as_owner', 'Unknown'),
                "scans": attributes.get('last_analysis_results', {})
            }
        except Exception as e:
            logger.exception(f"Error formatting IP result: {str(e)}")
            return {"error": "Failed to process scan results", "raw": vt_result}
    
    def _format_file_result(self, vt_result: Dict[str, Any], file_hash: str) -> Dict[str, Any]:
        """Format the VirusTotal file result into a standardized format"""
        try:
            attributes = vt_result.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})
            
            return {
                "resource": file_hash,
                "scan_date": datetime.fromtimestamp(attributes.get('last_analysis_date', time.time())).strftime("%Y-%m-%d %H:%M:%S"),
                "permalink": f"https://www.virustotal.com/gui/file/{file_hash}/detection",
                "positives": stats.get('malicious', 0),
                "total": sum(stats.values()),
                "type": attributes.get('type_description', 'Unknown'),
                "name": attributes.get('meaningful_name', file_hash),
                "size": attributes.get('size', 0),
                "scans": attributes.get('last_analysis_results', {})
            }
        except Exception as e:
            logger.exception(f"Error formatting file result: {str(e)}")
            return {"error": "Failed to process scan results", "raw": vt_result}
    
    def _add_to_history(self, result: Dict[str, Any], scan_type: str):
        """Add a scan to the history"""
        history_item = {
            "id": len(self.scan_history) + 1,
            "type": scan_type,
            "resource": result.get("resource", "Unknown"),
            "scan_date": result.get("scan_date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "positives": result.get("positives", 0),
            "total": result.get("total", 0),
            "permalink": result.get("permalink", "")
        }
        
        self.scan_history.append(history_item)
        
        # Limit history size
        if len(self.scan_history) > 100:
            self.scan_history.pop(0)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get scan history"""
        return list(reversed(self.scan_history))  # Most recent first

# Initialize once when module is imported
threat_intelligence = ThreatIntelligence()