#!/usr/bin/env python3
"""
Debug Flask-SQLAlchemy configuration
"""

import os
from config.app_config import create_app, db

# Import models
from models.database import User, SimulationEmail, SimulationResponse, SimulationSession

def debug_flask_config():
    """Debug Flask and SQLAlchemy configuration"""
    
    app = create_app()
    print(f"Flask app created: {app}")
    print(f"SQLAlchemy instance: {db}")
    
    with app.app_context():
        print(f"\n=== App Config ===")
        print(f"SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"SQLALCHEMY_TRACK_MODIFICATIONS: {app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS')}")
        
        print(f"\n=== Database Engine Info ===")
        print(f"Database engine: {db.engine}")
        print(f"Database URL: {db.engine.url}")
        
        print(f"\n=== Model Registry ===")
        print(f"Model registry: {db.Model.registry._class_registry.keys()}")
        
        print(f"\n=== Table Metadata ===")
        print(f"Tables in metadata: {list(db.metadata.tables.keys())}")
        
        # Try to inspect what would be created
        print(f"\n=== What would be created ===")
        for table_name, table in db.metadata.tables.items():
            print(f"Table {table_name}: {[col.name for col in table.columns]}")
        
        # Try manual create
        print(f"\n=== Manual table creation ===")
        try:
            db.metadata.create_all(bind=db.engine)
            print("Manual create_all completed successfully")
            
            # Check if file was created now
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            db_path = db_uri.replace('sqlite:///', '')
            print(f"Database file exists after manual create: {os.path.exists(db_path)}")
            if os.path.exists(db_path):
                print(f"Database file size: {os.path.getsize(db_path)}")
            
        except Exception as e:
            print(f"Manual create_all failed: {e}")

if __name__ == "__main__":
    debug_flask_config()