#!/usr/bin/env python3
"""
SHOCKWAVE PLANNER v2.0 - Fresh Start Script
Creates a brand new v2.0 database

Use this if:
- You don't have important data to keep
- You want to start fresh
- The repair script isn't working
"""
import os
import shutil
import sys

def start_fresh():
    """Remove old database and start fresh"""
    
    print("=" * 60)
    print("SHOCKWAVE PLANNER v2.0 - Fresh Start")
    print("=" * 60)
    print()
    
    db_file = 'shockwave_planner.db'
    
    if not os.path.exists(db_file):
        print("No database found. A new one will be created when you run the app.")
        print()
        print("Run the application:")
        print("  python main.py")
        return
    
    print("WARNING: This will delete your current database!")
    print()
    print("Current database: shockwave_planner.db")
    print()
    
    # Ask for confirmation
    response = input("Delete current database and start fresh? (yes/no): ").lower().strip()
    
    if response not in ['yes', 'y']:
        print("\nCancelled. Your database was not modified.")
        return
    
    # Backup old database
    backup_name = 'shockwave_planner.db.OLD'
    if os.path.exists(backup_name):
        # If backup already exists, add number
        counter = 1
        while os.path.exists(f'shockwave_planner.db.OLD.{counter}'):
            counter += 1
        backup_name = f'shockwave_planner.db.OLD.{counter}'
    
    print()
    print(f"Backing up old database to: {backup_name}")
    shutil.copy(db_file, backup_name)
    print("✓ Backup created")
    
    # Delete database
    print("Deleting old database...")
    os.remove(db_file)
    print("✓ Old database deleted")
    
    # Also remove journal if it exists
    journal_file = db_file + '-journal'
    if os.path.exists(journal_file):
        os.remove(journal_file)
        print("✓ Removed database journal")
    
    print()
    print("=" * 60)
    print("FRESH START COMPLETE")
    print("=" * 60)
    print()
    print("Your old database has been backed up to:")
    print(f"  {backup_name}")
    print()
    print("Now run the application:")
    print("  python main.py")
    print()
    print("A new v2.0 database will be created automatically.")
    print()
    print("To get launch data:")
    print("  1. Run: python main.py")
    print("  2. In the app: Data → Sync Upcoming Launches")
    print("  3. Wait 30 seconds for sync to complete")
    print()

if __name__ == '__main__':
    try:
        start_fresh()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
