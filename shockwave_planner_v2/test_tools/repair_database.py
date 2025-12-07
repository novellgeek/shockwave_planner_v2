#!/usr/bin/env python3
"""
SHOCKWAVE PLANNER v2.0 - Database Repair Script
Fixes missing columns and updates schema to v2.0
"""
import sqlite3
import sys
import os

def repair_database(db_path='shockwave_planner.db'):
    """Repair and update database schema"""
    
    print("=" * 60)
    print("SHOCKWAVE PLANNER v2.0 - Database Repair")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("A new database will be created when you run the application.")
        return
    
    print(f"Repairing database: {db_path}")
    print()
    
    # Backup first
    backup_path = db_path + '.backup'
    import shutil
    shutil.copy(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    repairs_made = []
    
    # Check and add status_color column
    try:
        cursor.execute("SELECT status_color FROM launch_status LIMIT 1")
        print("✓ launch_status.status_color exists")
    except sqlite3.OperationalError:
        print("  Adding launch_status.status_color...")
        cursor.execute("ALTER TABLE launch_status ADD COLUMN status_color TEXT")
        # Update existing statuses with colors
        cursor.execute("UPDATE launch_status SET status_color = '#FFFF00' WHERE status_name = 'Scheduled'")
        cursor.execute("UPDATE launch_status SET status_color = '#00FF00' WHERE status_name = 'Go for Launch'")
        cursor.execute("UPDATE launch_status SET status_color = '#00AA00' WHERE status_name = 'Success'")
        cursor.execute("UPDATE launch_status SET status_color = '#FF0000' WHERE status_name = 'Failure'")
        cursor.execute("UPDATE launch_status SET status_color = '#FFA500' WHERE status_name = 'Partial Failure'")
        cursor.execute("UPDATE launch_status SET status_color = '#808080' WHERE status_name = 'Scrubbed'")
        cursor.execute("UPDATE launch_status SET status_color = '#FFAA00' WHERE status_name = 'Hold'")
        cursor.execute("UPDATE launch_status SET status_color = '#00AAFF' WHERE status_name = 'In Flight'")
        repairs_made.append("Added status_color column")
        print("✓ Added launch_status.status_color")
    
    # Check and add status_abbr column
    try:
        cursor.execute("SELECT status_abbr FROM launch_status LIMIT 1")
        print("✓ launch_status.status_abbr exists")
    except sqlite3.OperationalError:
        print("  Adding launch_status.status_abbr...")
        cursor.execute("ALTER TABLE launch_status ADD COLUMN status_abbr TEXT")
        cursor.execute("UPDATE launch_status SET status_abbr = 'SCH' WHERE status_name = 'Scheduled'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'GO' WHERE status_name = 'Go for Launch'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'SUC' WHERE status_name = 'Success'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'FAIL' WHERE status_name = 'Failure'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'PF' WHERE status_name = 'Partial Failure'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'SCR' WHERE status_name = 'Scrubbed'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'HOLD' WHERE status_name = 'Hold'")
        cursor.execute("UPDATE launch_status SET status_abbr = 'FLT' WHERE status_name = 'In Flight'")
        repairs_made.append("Added status_abbr column")
        print("✓ Added launch_status.status_abbr")
    
    # Check and add description column
    try:
        cursor.execute("SELECT description FROM launch_status LIMIT 1")
        print("✓ launch_status.description exists")
    except sqlite3.OperationalError:
        print("  Adding launch_status.description...")
        cursor.execute("ALTER TABLE launch_status ADD COLUMN description TEXT")
        repairs_made.append("Added description column")
        print("✓ Added launch_status.description")
    
    # Check and add launches columns
    launches_columns = [
        ('launch_date', 'DATE'),
        ('launch_time', 'TIME'),
        ('launch_window_start', 'DATETIME'),
        ('launch_window_end', 'DATETIME'),
        ('site_id', 'INTEGER'),
        ('rocket_id', 'INTEGER'),
        ('vehicle_id', 'INTEGER'),
        ('mission_name', 'TEXT'),
        ('payload_name', 'TEXT'),
        ('payload_mass', 'REAL'),
        ('orbit_type', 'TEXT'),
        ('orbit_altitude', 'REAL'),
        ('inclination', 'REAL'),
        ('status_id', 'INTEGER'),
        ('success', 'BOOLEAN'),
        ('failure_reason', 'TEXT'),
        ('remarks', 'TEXT'),
        ('source_url', 'TEXT'),
        ('last_updated', 'DATETIME'),
        ('notam_reference', 'TEXT'),
        ('data_source', 'TEXT DEFAULT "MANUAL"'),
        ('external_id', 'TEXT'),
        ('last_synced', 'DATETIME'),
    ]
    
    for col_name, col_type in launches_columns:
        try:
            cursor.execute(f"SELECT {col_name} FROM launches LIMIT 1")
            print(f"✓ launches.{col_name} exists")
        except sqlite3.OperationalError:
            print(f"  Adding launches.{col_name}...")
            # Handle DEFAULT in column type
            if 'DEFAULT' in col_type.upper():
                cursor.execute(f"ALTER TABLE launches ADD COLUMN {col_name} {col_type}")
            else:
                cursor.execute(f"ALTER TABLE launches ADD COLUMN {col_name} {col_type}")
            repairs_made.append(f"Added launches.{col_name}")
            print(f"✓ Added launches.{col_name}")
    
    # Check and add site columns
    site_columns = [
        ('latitude', 'REAL'),
        ('longitude', 'REAL'),
        ('country', 'TEXT'),
        ('site_type', 'TEXT DEFAULT "LAUNCH"'),
        ('external_id', 'TEXT'),
    ]
    
    for col_name, col_type in site_columns:
        try:
            cursor.execute(f"SELECT {col_name} FROM launch_sites LIMIT 1")
            print(f"✓ launch_sites.{col_name} exists")
        except sqlite3.OperationalError:
            print(f"  Adding launch_sites.{col_name}...")
            cursor.execute(f"ALTER TABLE launch_sites ADD COLUMN {col_name} {col_type}")
            repairs_made.append(f"Added launch_sites.{col_name}")
            print(f"✓ Added launch_sites.{col_name}")
    
    # Check and add rocket columns
    rocket_columns = [
        ('family', 'TEXT'),
        ('variant', 'TEXT'),
        ('manufacturer', 'TEXT'),
        ('country', 'TEXT'),
        ('payload_leo', 'INTEGER'),
        ('payload_gto', 'INTEGER'),
        ('height', 'REAL'),
        ('diameter', 'REAL'),
        ('mass', 'REAL'),
        ('stages', 'INTEGER'),
        ('external_id', 'TEXT'),
    ]
    
    for col_name, col_type in rocket_columns:
        try:
            cursor.execute(f"SELECT {col_name} FROM rockets LIMIT 1")
            print(f"✓ rockets.{col_name} exists")
        except sqlite3.OperationalError:
            print(f"  Adding rockets.{col_name}...")
            cursor.execute(f"ALTER TABLE rockets ADD COLUMN {col_name} {col_type}")
            repairs_made.append(f"Added rockets.{col_name}")
            print(f"✓ Added rockets.{col_name}")
    
    # Create new tables if they don't exist
    
    # Reentry sites
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reentry_sites (
            reentry_site_id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            drop_zone TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            country TEXT,
            zone_type TEXT,
            external_id TEXT,
            UNIQUE(location, drop_zone)
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='reentry_sites'")
    if cursor.fetchone()[0] > 0:
        print("✓ reentry_sites table exists")
    
    # Reentries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reentries (
            reentry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            launch_id INTEGER,
            reentry_date DATE,
            reentry_time TIME,
            reentry_site_id INTEGER,
            vehicle_component TEXT,
            reentry_type TEXT,
            status_id INTEGER,
            remarks TEXT,
            data_source TEXT DEFAULT 'MANUAL',
            external_id TEXT,
            FOREIGN KEY (launch_id) REFERENCES launches(launch_id),
            FOREIGN KEY (reentry_site_id) REFERENCES reentry_sites(reentry_site_id),
            FOREIGN KEY (status_id) REFERENCES launch_status(status_id)
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='reentries'")
    if cursor.fetchone()[0] > 0:
        print("✓ reentries table exists")
    
    # Sync log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT,
            records_added INTEGER,
            records_updated INTEGER,
            status TEXT,
            error_message TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='sync_log'")
    if cursor.fetchone()[0] > 0:
        print("✓ sync_log table exists")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("REPAIR COMPLETE")
    print("=" * 60)
    
    if repairs_made:
        print(f"\nRepairs made ({len(repairs_made)}):")
        for repair in repairs_made:
            print(f"  • {repair}")
    else:
        print("\nNo repairs needed - database schema is up to date!")
    
    print(f"\nBackup saved: {backup_path}")
    print("\nYou can now run the application:")
    print("  python main.py")
    print()

if __name__ == '__main__':
    db_path = 'shockwave_planner.db'
    
    # Check if database path provided as argument
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    repair_database(db_path)
