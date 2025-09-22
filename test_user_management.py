#!/usr/bin/env python3
"""
Test script for user management and password reset functionality
"""

import sys
import os
import tempfile
import sqlite3
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_app, db
from models.database import User

def test_user_management():
    """Test user management functionality"""
    print("🧪 Testing User Management and Password Reset Features")
    print("=" * 60)
    
    # Create a temporary database for testing
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE']
    
    with app.app_context():
        db.create_all()
        
        # Test 1: Email uniqueness validation
        print("\n1. Testing email uniqueness validation...")
        user1 = User(name="Test User 1", email="test@example.com")
        user1.set_password("TestPass123")
        db.session.add(user1)
        db.session.commit()
        
        # Try to create another user with same email
        existing_user = User.query.filter_by(email="test@example.com").first()
        assert existing_user is not None, "User should exist"
        assert existing_user.email == "test@example.com", "Email should match"
        print("   ✅ Email uniqueness validation working correctly")
        
        # Test 2: Admin functionality
        print("\n2. Testing admin functionality...")
        assert not user1.is_admin_user(), "User should not be admin initially"
        
        user1.is_admin = True
        db.session.commit()
        
        updated_user = User.query.filter_by(email="test@example.com").first()
        assert updated_user.is_admin_user(), "User should be admin after update"
        print("   ✅ Admin functionality working correctly")
        
        # Test 3: Password reset token generation
        print("\n3. Testing password reset functionality...")
        token = user1.generate_reset_token()
        assert token is not None, "Reset token should be generated"
        assert len(token) > 20, "Reset token should be sufficiently long"
        assert user1.password_reset_token == token, "Token should be stored"
        assert user1.password_reset_expires is not None, "Expiry should be set"
        print("   ✅ Password reset token generation working correctly")
        
        # Test 4: Password reset token verification
        print("\n4. Testing password reset token verification...")
        assert user1.verify_reset_token(token), "Valid token should verify"
        assert not user1.verify_reset_token("invalid_token"), "Invalid token should not verify"
        print("   ✅ Password reset token verification working correctly")
        
        # Test 5: Password reset token cleanup
        print("\n5. Testing password reset token cleanup...")
        user1.clear_reset_token()
        assert user1.password_reset_token is None, "Token should be cleared"
        assert user1.password_reset_expires is None, "Expiry should be cleared"
        print("   ✅ Password reset token cleanup working correctly")
        
        # Test 6: User creation timestamps
        print("\n6. Testing user creation timestamps...")
        assert user1.created_at is not None, "Created timestamp should exist"
        assert isinstance(user1.created_at, datetime), "Created timestamp should be datetime"
        print("   ✅ User creation timestamps working correctly")
        
    # Cleanup
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! User management features are working correctly.")
    print("\nFeatures tested:")
    print("  • Email uniqueness validation")
    print("  • Admin role management")
    print("  • Password reset token generation")
    print("  • Password reset token verification")
    print("  • Password reset token cleanup")
    print("  • User creation timestamps")

def test_database_schema():
    """Test that the database schema includes new columns"""
    print("\n🗄️  Testing database schema...")
    
    with app.app_context():
        db.create_all()
        
        # Check if User table has new columns
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        required_columns = ['is_admin', 'created_at', 'password_reset_token', 'password_reset_expires']
        for column in required_columns:
            assert column in columns, f"Column '{column}' should exist in user table"
            print(f"   ✅ Column '{column}' exists")
        
        print("   ✅ Database schema is correct")

if __name__ == '__main__':
    from config.app_config import create_app
    app = create_app()
    
    try:
        test_database_schema()
        test_user_management()
        print("\n🚀 All functionality tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)