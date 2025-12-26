#!/usr/bin/env python3
"""
SHOCKWAVE PLANNER v2.0 - Space Devs API Test
Quick test to verify the API connection works

This tests the Space Devs API without needing the full application.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import LaunchDatabase
from data.space_devs import SpaceDevsClient

def test_api():
    """Test Space Devs API connection"""
    
    print("=" * 60)
    print("SHOCKWAVE PLANNER - Space Devs API Test")
    print("=" * 60)
    print()
    
    # Create temporary database
    print("Creating temporary database...")
    db = LaunchDatabase('test_api.db')
    print("✓ Database created")
    print()
    
    # Create API client
    print("Creating API client...")
    api = SpaceDevsClient(db)
    print("✓ API client created")
    print()
    
    # Test fetching upcoming launches (just a few)
    print("Testing API fetch (this will take ~10 seconds)...")
    print()
    
    try:
        # Fetch just first page (10 launches)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        future = now + timedelta(days=30)
        
        params = {
            "net__gte": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": future.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 10,
            "mode": "detailed",
            "ordering": "net"
        }
        
        launches = api.fetch_launches(params)
        
        # Close database connection BEFORE trying to delete
        db.close()
        
        if launches:
            print()
            print("=" * 60)
            print("✅ SUCCESS! API is working!")
            print("=" * 60)
            print(f"Fetched {len(launches)} launches")
            print()
            print("Sample launches:")
            print("-" * 60)
            for i, launch in enumerate(launches[:3], 1):
                name = launch.get('name', 'Unknown')
                net = launch.get('net', 'Unknown')
                status = launch.get('status', {}).get('name', 'Unknown')
                print(f"{i}. {name}")
                print(f"   Date: {net}")
                print(f"   Status: {status}")
                print()
            
            print("-" * 60)
            print()
            print("The Space Devs API is working correctly!")
            print("You can now use: Data → Sync Upcoming Launches")
            print()
            
            # Clean up - add retry for Windows
            import time
            for attempt in range(3):
                try:
                    if os.path.exists('test_api.db'):
                        os.remove('test_api.db')
                    if os.path.exists('test_api.db-journal'):
                        os.remove('test_api.db-journal')
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.5)  # Wait for Windows to release the file
                    else:
                        print("Note: Could not delete test_api.db (file locked)")
                        print("You can safely delete it manually if you wish.")
            
            return True
            
        else:
            print()
            print("=" * 60)
            print("⚠️  WARNING: No launches returned")
            print("=" * 60)
            print()
            print("This could mean:")
            print("  1. You're being rate limited (wait 60 seconds)")
            print("  2. Network connectivity issue")
            print("  3. API endpoint changed")
            print()
            return False
            
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        print("Possible issues:")
        print("  1. No internet connection")
        print("  2. Firewall blocking requests")
        print("  3. Space Devs API is down")
        print()
        
        import traceback
        traceback.print_exc()
        
        return False

if __name__ == '__main__':
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
