#!/usr/bin/env python3
"""
Simple security test script for CyberVantage
Tests basic security features without external dependencies
"""

def test_config_security():
    """Test that configuration security is working"""
    print("🔒 Testing Configuration Security...")
    
    import os
    os.environ.pop('FLASK_SECRET', None)  # Remove if exists to test fallback
    
    from config.app_config import create_app
    app = create_app()
    
    # Check that secrets are not the old defaults
    assert app.config['SECRET_KEY'] != 'dev_secret', "SECRET_KEY should not be default value"
    assert app.config['JWT_SECRET_KEY'] != 'jwt_secret', "JWT_SECRET_KEY should not be default value"
    assert app.config['WTF_CSRF_SECRET_KEY'] != 'csrf_secret', "CSRF_SECRET should not be default value"
    
    print("✅ Configuration security: PASSED")

def test_security_headers():
    """Test security headers are applied"""
    print("🔒 Testing Security Headers...")
    
    from config.app_config import create_app
    app = create_app()
    
    with app.test_client() as client:
        response = client.get('/')
        
        # Check security headers
        assert response.headers.get('X-Frame-Options') == 'DENY'
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'
        assert response.headers.get('Referrer-Policy') == 'same-origin'
    
    print("✅ Security headers: PASSED")

def test_auth_routes_exist():
    """Test that authentication routes are secure"""
    print("🔒 Testing Authentication Routes...")
    
    from routes.auth_routes import auth_bp, is_rate_limited, login_attempts
    from collections import deque
    
    # Test rate limiting function
    test_ip = "192.168.1.100"
    login_attempts[test_ip] = deque()
    
    # Should not be rate limited initially
    assert not is_rate_limited(test_ip, login_attempts, 5), "Should not be rate limited initially"
    
    # Add 5 attempts (max allowed)
    import time
    for _ in range(5):
        login_attempts[test_ip].append(time.time())
    
    # Should now be rate limited
    assert is_rate_limited(test_ip, login_attempts, 5), "Should be rate limited after max attempts"
    
    print("✅ Authentication security: PASSED")

def test_dangerous_routes_removed():
    """Test that dangerous encryption routes are not accessible"""
    print("🔒 Testing Dangerous Routes Removal...")
    
    from config.app_config import create_app
    from routes.auth_routes import auth_bp
    from routes.simulation_routes import simulation_bp  
    from routes.analysis_routes import analysis_bp
    from routes.threat_routes import threat_bp
    
    app = create_app()
    app.register_blueprint(auth_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(analysis_bp) 
    app.register_blueprint(threat_bp)
    
    with app.test_client() as client:
        # Test that dangerous routes return 404
        response = client.get('/encrypt/test_data')
        assert response.status_code == 404, "Encrypt route should not exist"
        
        response = client.get('/decrypt/test_data')
        assert response.status_code == 404, "Decrypt route should not exist"
    
    print("✅ Dangerous routes removal: PASSED")

if __name__ == "__main__":
    print("🛡️  CyberVantage Security Test Suite")
    print("=" * 50)
    
    try:
        test_config_security()
        test_security_headers()
        test_auth_routes_exist()
        test_dangerous_routes_removed()
        
        print("=" * 50)
        print("🎉 All security tests PASSED!")
        print("✅ CyberVantage security improvements verified")
        
    except Exception as e:
        print(f"❌ Security test FAILED: {e}")
        exit(1)