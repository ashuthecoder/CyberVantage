#!/usr/bin/env python3
"""
Test table creation and schema update
"""

import sqlite3
import os
from config.app_config import create_app, db

# Import all models to ensure they're registered
from models.database import (
    User, SimulationEmail, SimulationResponse, SimulationSession,
    update_database_schema
)

def test_table_creation():
    """Test creating tables and updating schema"""
    
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI'] 
        db_path = db_uri.replace('sqlite:///', '')
        print(f"Database path: {db_path}")
        
        # Force remove existing file to start fresh
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing {db_path}")
        
        print(f"\n=== Before create_all ===")
        print(f"File exists: {os.path.exists(db_path)}")
        
        # Try to create tables
        print(f"\n=== Creating tables ===")
        db.create_all()
        print("db.create_all() completed")
        
        print(f"\n=== After create_all ===")
        print(f"File exists: {os.path.exists(db_path)}")
        if os.path.exists(db_path):
            print(f"File size: {os.path.getsize(db_path)} bytes")
            
            # Check what tables exist
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Check simulation_email structure if it exists
            if any(t[0] == 'simulation_email' for t in tables):
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"simulation_email columns: {column_names}")
                print(f"Has simulation_id: {'simulation_id' in column_names}")
            
            conn.close()
        
        # Now try the schema update
        print(f"\n=== Updating schema ===")
        success = update_database_schema(app)
        print(f"Schema update success: {success}")
        
        # Check again after schema update
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
            table = cursor.fetchone()
            if table:
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"Updated simulation_email columns: {column_names}")
                print(f"Now has simulation_id: {'simulation_id' in column_names}")
            conn.close()

if __name__ == "__main__":
    test_table_creation()