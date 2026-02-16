#!/usr/bin/env python3
"""
Database Reset Script for CyberVantage
This script will wipe the database and create fresh tables
"""
import os
import sys

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.app_config import create_app, db
from models.database import User, SimulationEmail, SimulationResponse, SimulationSession

def reset_database():
    """Wipe and recreate the database"""
    print("=" * 60)
    print("CyberVantage Database Reset Script")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print("This includes:")
    print("  - All user accounts")
    print("  - All simulation data")
    print("  - All session records")
    print("  - All responses")
    print("\n")
    
    # Confirm action
    confirm = input("Type 'RESET' to confirm: ").strip()
    if confirm != 'RESET':
        print("\n❌ Reset cancelled.")
        return
    
    print("\n🔄 Starting database reset...\n")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables
            print("📋 Dropping all tables...")
            db.drop_all()
            print("✅ All tables dropped successfully")
            
            # Create all tables
            print("\n📋 Creating fresh tables...")
            db.create_all()
            print("✅ All tables created successfully")
            
            # Verify tables
            print("\n📊 Verifying database schema...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n✅ Database reset complete!")
            print(f"\n📌 Created tables:")
            for table in tables:
                print(f"   - {table}")
            
            print("\n" + "=" * 60)
            print("✅ Database is now fresh and ready to use!")
            print("=" * 60)
            print("\n💡 Next steps:")
            print("   1. Start the application")
            print("   2. Register a new user account")
            print("   3. Begin training!\n")
            
        except Exception as e:
            print(f"\n❌ Error during database reset: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    reset_database()
