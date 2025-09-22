#!/usr/bin/env python3
"""
Demonstrate the database update issue
"""

import sqlite3
import os
from config.app_config import create_app, db
from models.database import update_database_schema, User, SimulationEmail, SimulationResponse, SimulationSession

def simulate_app_lifecycle():
    """Simulate what happens during app startup and usage"""
    
    print("=== APP STARTUP SIMULATION ===")
    app = create_app()
    
    with app.app_context():
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db_uri = app.config['SQLALCHEMY_DATABASE_URI'] 
        db_path = db_uri.replace('sqlite:///', '')
        print(f"Database path: {db_path}")
        
        # Step 1: db.create_all() (like in main.py)
        print("\n1. Running db.create_all()...")
        db.create_all()
        
        # Check what tables were created
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"   Tables created: {[t[0] for t in tables]}")
        
        # Check simulation_email table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
        table = cursor.fetchone()
        if table:
            cursor.execute("PRAGMA table_info(simulation_email)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"   simulation_email columns: {column_names}")
            print(f"   Has simulation_id: {'simulation_id' in column_names}")
        
        conn.close()
        
        # Step 2: update_database_schema() (like in main.py)
        print("\n2. Running update_database_schema()...")
        success = update_database_schema(app)
        print(f"   Result: {success}")
        
        # Check if simulation_id column was added
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
        table = cursor.fetchone()
        if table:
            cursor.execute("PRAGMA table_info(simulation_email)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"   Updated simulation_email columns: {column_names}")
            print(f"   Now has simulation_id: {'simulation_id' in column_names}")
        
        conn.close()
        
        # Check file size
        size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        print(f"   Database file size: {size} bytes")
        
        return db_path

def check_git_status(db_path):
    """Check if the database file will show up in git status"""
    print(f"\n=== GIT STATUS CHECK ===")
    print(f"Database file: {db_path}")
    print(f"File size: {os.path.getsize(db_path)} bytes")
    
    # Check if file is tracked
    os.system(f"cd /home/runner/work/CyberVantage/CyberVantage && git ls-files | grep -q '{db_path}' && echo 'File is tracked by git' || echo 'File not tracked by git'")

if __name__ == "__main__":
    db_path = simulate_app_lifecycle()
    check_git_status(db_path)
    
    # Simulate running the app again
    print(f"\n=== SIMULATING SECOND RUN ===")
    db_path = simulate_app_lifecycle()