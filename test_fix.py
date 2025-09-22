#!/usr/bin/env python3
"""
Test the fixed database schema update
"""

import sqlite3
import os
from config.app_config import create_app, db

# Import models
from models.database import User, SimulationEmail, SimulationResponse, SimulationSession

def fixed_update_database_schema(app):
    """Fixed version that uses the actual database path"""
    try:
        # Use the actual database URL from the engine, not the config
        actual_db_url = str(db.engine.url)
        db_path = actual_db_url.replace('sqlite:///', '')
        print(f"[FIXED] Using actual database path: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure the table exists before attempting to alter it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
        table = cursor.fetchone()
        if not table:
            print("[FIXED] simulation_email table does not exist yet. Skipping ALTER until db.create_all() runs.")
            conn.close()
            return True

        # Check existing columns
        cursor.execute("PRAGMA table_info(simulation_email)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'simulation_id' not in columns:
            print("[FIXED] Adding simulation_id column to SimulationEmail table")
            cursor.execute("ALTER TABLE simulation_email ADD COLUMN simulation_id TEXT")
            conn.commit()
            print("[FIXED] Column added successfully")
        else:
            print("[FIXED] simulation_id column already exists")

        conn.close()
        return True
    except Exception as e:
        print(f"[FIXED] Error updating database schema: {str(e)}")
        return False

def test_fix():
    """Test the original vs fixed function"""
    
    app = create_app()
    
    with app.app_context():
        config_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        actual_path = str(db.engine.url).replace('sqlite:///', '')
        
        print(f"Config suggests path: {config_path}")
        print(f"Actual database path: {actual_path}")
        print(f"Config file exists: {os.path.exists(config_path)}")
        print(f"Actual file exists: {os.path.exists(actual_path)}")
        
        if os.path.exists(actual_path):
            print(f"Actual file size: {os.path.getsize(actual_path)}")
            
            # Check current schema
            conn = sqlite3.connect(actual_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
            table = cursor.fetchone()
            if table:
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"Current columns: {column_names}")
                has_sim_id = 'simulation_id' in column_names
                print(f"Has simulation_id: {has_sim_id}")
                
                if not has_sim_id:
                    print(f"\n=== Testing FIXED function ===")
                    success = fixed_update_database_schema(app)
                    print(f"Fixed function result: {success}")
                    
                    # Check if it worked
                    cursor.execute("PRAGMA table_info(simulation_email)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    print(f"Columns after fix: {column_names}")
                    print(f"Now has simulation_id: {'simulation_id' in column_names}")
                
            conn.close()

if __name__ == "__main__":
    test_fix()