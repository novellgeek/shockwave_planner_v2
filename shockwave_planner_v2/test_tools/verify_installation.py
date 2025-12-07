#!/usr/bin/env python3
"""
SHOCKWAVE PLANNER v2.0 - Verification Test
Quick test to verify installation and basic functionality
"""
import sys
import os

def test_imports():
    """Test required imports"""
    print("Testing imports...")
    try:
        import PyQt6
        print("  ✓ PyQt6 found")
    except ImportError:
        print("  ✗ PyQt6 NOT found - Install with: pip install PyQt6 --break-system-packages")
        return False
    
    try:
        import requests
        print("  ✓ requests found")
    except ImportError:
        print("  ✗ requests NOT found - Install with: pip install requests --break-system-packages")
        return False
    
    return True

def test_modules():
    """Test application modules"""
    print("\nTesting modules...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from data.database import LaunchDatabase
        print("  ✓ database module")
    except Exception as e:
        print(f"  ✗ database module: {e}")
        return False
    
    try:
        from data.space_devs import SpaceDevsAPI
        print("  ✓ space_devs module")
    except Exception as e:
        print(f"  ✗ space_devs module: {e}")
        return False
    
    try:
        from gui.main_window import MainWindow
        print("  ✓ main_window module")
    except Exception as e:
        print(f"  ✗ main_window module: {e}")
        return False
    
    try:
        from gui.timeline_view import TimelineView
        print("  ✓ timeline_view module")
    except Exception as e:
        print(f"  ✗ timeline_view module: {e}")
        return False
    
    try:
        from gui.timeline_view_reentry import ReentryTimelineView
        print("  ✓ timeline_view_reentry module")
    except Exception as e:
        print(f"  ✗ timeline_view_reentry module: {e}")
        return False
    
    try:
        from gui.enhanced_list_view import EnhancedListView
        print("  ✓ enhanced_list_view module")
    except Exception as e:
        print(f"  ✗ enhanced_list_view module: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from data.database import LaunchDatabase
        
        # Create test database
        db = LaunchDatabase('test_verify.db')
        print("  ✓ Database creation")
        
        # Test basic operations
        sites = db.get_all_sites()
        print(f"  ✓ Get sites (found {len(sites)})")
        
        rockets = db.get_all_rockets()
        print(f"  ✓ Get rockets (found {len(rockets)})")
        
        statuses = db.get_all_statuses()
        print(f"  ✓ Get statuses (found {len(statuses)})")
        
        stats = db.get_statistics()
        print(f"  ✓ Get statistics (total: {stats['total_launches']})")
        
        db.close()
        
        # Clean up test database
        if os.path.exists('test_verify.db'):
            os.remove('test_verify.db')
        
        return True
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False

def test_files():
    """Test required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'gui/__init__.py',
        'gui/main_window.py',
        'gui/timeline_view.py',
        'gui/timeline_view_reentry.py',
        'gui/enhanced_list_view.py',
        'data/__init__.py',
        'data/database.py',
        'data/space_devs.py',
        'README.md',
        'CHANGELOG.md',
        'MIGRATION_GUIDE.md',
        'QUICK_REFERENCE.md',
        'PROJECT_SUMMARY_v2.md',
    ]
    
    all_found = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} MISSING")
            all_found = False
    
    return all_found

def main():
    print("=" * 60)
    print("SHOCKWAVE PLANNER v2.0 - Verification Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("File Structure", test_files()))
    results.append(("Modules", test_modules()))
    results.append(("Database", test_database()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All tests PASSED! SHOCKWAVE PLANNER v2.0 is ready!")
        print("\nTo start the application:")
        print("  ./start_shockwave.sh")
        print("  OR: python3 main.py")
        return 0
    else:
        print("\n⚠️  Some tests FAILED. Please review the output above.")
        print("\nCommon fixes:")
        print("  - Install PyQt6: pip install PyQt6 --break-system-packages")
        print("  - Install requests: pip install requests --break-system-packages")
        print("  - Check file permissions")
        return 1

if __name__ == '__main__':
    sys.exit(main())
