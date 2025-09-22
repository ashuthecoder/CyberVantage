#!/usr/bin/env python3
"""
Debug which database is being used by the app
"""

import sqlite3
import os
from config.app_config import create_app, db

def debug_database_path():
    """Debug which database path the app is using"""
    app = create_app()
    with app.app_context():
        print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Extract the actual database path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            print(f"Database file path: {db_path}")
            print(f"Absolute path: {os.path.abspath(db_path)}")
            print(f"File exists: {os.path.exists(db_path)}")
            if os.path.exists(db_path):
                print(f"File size: {os.path.getsize(db_path)}")
                
        # Try to connect and check tables
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables in {db_path}: {[t[0] for t in tables]}")
            
            # Check simulation_email table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
            table = cursor.fetchone()
            if table:
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"simulation_email columns: {column_names}")
                print(f"Has simulation_id: {'simulation_id' in column_names}")
                
                # Try adding the column manually
                if 'simulation_id' not in column_names:
                    print("Manually adding simulation_id column...")
                    cursor.execute("ALTER TABLE simulation_email ADD COLUMN simulation_id TEXT")
                    conn.commit()
                    print("Column added successfully")
                    
                    # Check again
                    cursor.execute("PRAGMA table_info(simulation_email)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    print(f"Updated simulation_email columns: {column_names}")
            
            conn.close()
        except Exception as e:
            print(f"Error accessing database: {e}")

if __name__ == "__main__":
    debug_database_path()