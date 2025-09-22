#!/usr/bin/env python3
"""
Comprehensive test showing the actual database update behavior
"""

import sqlite3
import os
from config.app_config import create_app, db

# Import models
from models.database import (
    User, SimulationEmail, SimulationResponse, SimulationSession,
    update_database_schema
)

def show_database_behavior():
    """Show what actually happens with the database during app lifecycle"""
    
    app = create_app()
    
    with app.app_context():
        # Get the actual database path
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        actual_db_path = str(db.engine.url).replace('sqlite:///', '')
        config_suggests = db_uri.replace('sqlite:///', '')
        
        print(f"Config suggests: {config_suggests}")
        print(f"Actually using: {actual_db_path}")
        print(f"Same file? {config_suggests == actual_db_path}")
        
        # Check before any operations
        print(f"\n=== BEFORE OPERATIONS ===")
        if os.path.exists(actual_db_path):
            print(f"Database exists: {actual_db_path} (size: {os.path.getsize(actual_db_path)})")
            
            # Check current schema
            conn = sqlite3.connect(actual_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
            table = cursor.fetchone()
            if table:
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"Current simulation_email columns: {column_names}")
                print(f"Has simulation_id: {'simulation_id' in column_names}")
            else:
                print("simulation_email table does not exist")
            conn.close()
        else:
            print(f"Database does not exist: {actual_db_path}")
        
        # Step 1: db.create_all() 
        print(f"\n=== RUNNING db.create_all() ===")
        db.create_all()
        print("db.create_all() completed")
        
        # Check after create_all
        if os.path.exists(actual_db_path):
            size = os.path.getsize(actual_db_path)
            print(f"Database size after create_all: {size}")
        
        # Step 2: update_database_schema()
        print(f"\n=== RUNNING update_database_schema() ===")
        success = update_database_schema(app)
        print(f"Schema update result: {success}")
        
        # Check final state
        print(f"\n=== FINAL STATE ===")
        if os.path.exists(actual_db_path):
            final_size = os.path.getsize(actual_db_path)
            print(f"Final database size: {final_size}")
            
            # Check final schema
            conn = sqlite3.connect(actual_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simulation_email'")
            table = cursor.fetchone()
            if table:
                cursor.execute("PRAGMA table_info(simulation_email)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                print(f"Final simulation_email columns: {column_names}")
                print(f"Final has simulation_id: {'simulation_id' in column_names}")
            conn.close()
        
        return actual_db_path

def check_git_tracking():
    """Check which database files are tracked by Git"""
    print(f"\n=== GIT TRACKING STATUS ===")
    
    # List all .db files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                filepath = os.path.join(root, file).replace('./', '')
                size = os.path.getsize(filepath)
                # Check if tracked
                result = os.system(f"git ls-files | grep -q '^{filepath}$'")
                tracked = "TRACKED" if result == 0 else "NOT TRACKED"
                print(f"{filepath}: {size} bytes, {tracked}")

def demonstrate_problem():
    """Demonstrate why the database keeps getting committed"""
    print(f"\n=== DEMONSTRATING THE PROBLEM ===")
    
    # Show the full sequence
    for i in range(2):
        print(f"\n--- Run #{i+1} ---")
        actual_db_path = show_database_behavior()
        
        # Check if file would show up in git status
        if os.path.exists(actual_db_path):
            size = os.path.getsize(actual_db_path)
            print(f"Database file size at end of run: {size}")

if __name__ == "__main__":
    demonstrate_problem()
    check_git_tracking()