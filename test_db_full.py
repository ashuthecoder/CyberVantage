#!/usr/bin/env python3
"""
Test script to simulate the full app startup sequence
"""

import sqlite3
import os
from config.app_config import create_app, db
from models.database import update_database_schema

def check_db_timestamps():
    """Check modification times of database files"""
    files = ['users.db', 'instance/users.db', 'instance/cybervantage.db']
    for file_path in files:
        if os.path.exists(file_path):
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            print(f"{file_path}: mtime={mtime}, size={size}")

def check_simulation_email_schema():
    """Check the simulation_email table structure"""
    db_files = ['instance/users.db', 'instance/cybervantage.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
                table = cursor.fetchone()
                if table:
                    cursor.execute("PRAGMA table_info(simulation_email)")
                    columns = cursor.fetchall()
                    print(f"\n{db_file} - simulation_email columns:")
                    for col in columns:
                        print(f"  {col[1]} ({col[2]})")
                    has_sim_id = any(col[1] == 'simulation_id' for col in columns)
                    print(f"  Has simulation_id column: {has_sim_id}")
                else:
                    print(f"\n{db_file} - simulation_email table does not exist")
                conn.close()
            except Exception as e:
                print(f"\n{db_file} - Error: {e}")

if __name__ == "__main__":
    print("=== BEFORE APP CREATION ===")
    check_db_timestamps()
    check_simulation_email_schema()
    
    print("\n=== CREATING APP ===")
    app = create_app()
    
    print("\n=== AFTER APP CREATION ===")
    check_db_timestamps() 
    check_simulation_email_schema()
    
    print("\n=== RUNNING db.create_all() ===")
    with app.app_context():
        db.create_all()
        print("db.create_all() completed")
    
    print("\n=== AFTER db.create_all() ===")
    check_db_timestamps()
    check_simulation_email_schema()
    
    print("\n=== UPDATING SCHEMA ===")
    with app.app_context():
        success = update_database_schema(app)
        print(f"Schema update result: {success}")
    
    print("\n=== AFTER SCHEMA UPDATE ===")
    check_db_timestamps()
    check_simulation_email_schema()