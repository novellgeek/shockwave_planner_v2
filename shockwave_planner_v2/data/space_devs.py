"""
SHOCKWAVE PLANNER v2.0 - Space Devs API Integration
Sync launches from The Space Devs Launch Library API

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0

API Documentation: https://ll.thespacedevs.com/2.2.0/swagger/
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data.database import LaunchDatabase


class SpaceDevsAPI:
    """Interface to The Space Devs Launch Library API"""
    
    BASE_URL = "https://ll.thespacedevs.com/2.2.0"
    
    def __init__(self, db: LaunchDatabase):
        """Initialize API client"""
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHOCKWAVE PLANNER v2.0 - NZDF Space Operations Centre'
        })
    
    def fetch_upcoming_launches(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Fetch upcoming launches from API"""
        url = f"{self.BASE_URL}/launch/upcoming/"
        params = {
            'limit': limit,
            'offset': offset,
            'mode': 'detailed'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching upcoming launches: {e}")
            return []
    
    def fetch_previous_launches(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Fetch previous launches from API"""
        url = f"{self.BASE_URL}/launch/previous/"
        params = {
            'limit': limit,
            'offset': offset,
            'mode': 'detailed'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching previous launches: {e}")
            return []
    
    def fetch_launches_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch launches within a date range"""
        url = f"{self.BASE_URL}/launch/"
        params = {
            'net__gte': start_date,  # NET = No Earlier Than
            'net__lte': end_date,
            'mode': 'detailed',
            'limit': 100
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching launches by date range: {e}")
            return []
    
    def search_launches(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for launches"""
        url = f"{self.BASE_URL}/launch/"
        params = {
            'search': query,
            'limit': limit,
            'mode': 'detailed'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching launches: {e}")
            return []
    
    def parse_launch_data(self, api_launch: Dict) -> Dict:
        """Parse Space Devs launch data into database format"""
        
        # Parse date/time
        net = api_launch.get('net')  # No Earlier Than (ISO format)
        window_start = api_launch.get('window_start')
        window_end = api_launch.get('window_end')
        
        launch_date = None
        launch_time = None
        if net:
            try:
                dt = datetime.fromisoformat(net.replace('Z', '+00:00'))
                launch_date = dt.strftime('%Y-%m-%d')
                launch_time = dt.strftime('%H:%M:%S')
            except:
                pass
        
        # Parse pad location
        pad = api_launch.get('pad', {})
        location = pad.get('location', {})
        
        site_name = location.get('name', 'Unknown')
        pad_name = pad.get('name', 'Unknown')
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        country = location.get('country_code')
        
        # Parse rocket
        rocket = api_launch.get('rocket', {})
        configuration = rocket.get('configuration', {})
        
        rocket_name = configuration.get('full_name') or configuration.get('name', 'Unknown')
        rocket_family = configuration.get('family', '')
        rocket_variant = configuration.get('variant', '')
        
        # Parse mission
        mission = api_launch.get('mission', {})
        mission_name = api_launch.get('name', 'Unknown Mission')
        mission_description = mission.get('description', '')
        orbit = mission.get('orbit', {})
        orbit_name = orbit.get('abbrev') or orbit.get('name', '')
        
        # Parse status
        status = api_launch.get('status', {})
        status_name = status.get('name', 'Unknown')
        status_abbr = status.get('abbrev', '')
        
        # Map Space Devs status to our status
        status_mapping = {
            'Go for Launch': 'Go for Launch',
            'TBC': 'Scheduled',
            'TBD': 'Scheduled',
            'Success': 'Success',
            'Failure': 'Failure',
            'Partial Failure': 'Partial Failure',
            'In Flight': 'In Flight',
            'Hold': 'Hold',
        }
        mapped_status = status_mapping.get(status_name, 'Scheduled')
        
        # Determine success
        success = None
        if status_name == 'Success':
            success = True
        elif status_name in ['Failure', 'Partial Failure']:
            success = False
        
        return {
            'launch_date': launch_date,
            'launch_time': launch_time,
            'launch_window_start': window_start,
            'launch_window_end': window_end,
            'site_data': {
                'location': site_name,
                'launch_pad': pad_name,
                'latitude': latitude,
                'longitude': longitude,
                'country': country,
                'external_id': pad.get('id')
            },
            'rocket_data': {
                'name': rocket_name,
                'family': rocket_family,
                'variant': rocket_variant,
                'external_id': configuration.get('id')
            },
            'mission_name': mission_name,
            'payload_name': mission.get('name', ''),
            'orbit_type': orbit_name,
            'status_name': mapped_status,
            'success': success,
            'remarks': mission_description[:500] if mission_description else None,
            'source_url': api_launch.get('url'),
            'external_id': api_launch.get('id'),
            'data_source': 'SPACE_DEVS'
        }
    
    def sync_launch_to_db(self, launch_data: Dict) -> Tuple[str, int]:
        """
        Sync a parsed launch to the database
        Returns: (action, launch_id) where action is 'added', 'updated', or 'skipped'
        """
        
        # Check if launch already exists
        existing = self.db.find_launch_by_external_id(launch_data['external_id'])
        
        # Find or create site
        site_data = launch_data['site_data']
        site_id = None
        sites = self.db.get_all_sites()
        for site in sites:
            if (site['location'] == site_data['location'] and 
                site['launch_pad'] == site_data['launch_pad']):
                site_id = site['site_id']
                break
        
        if not site_id:
            site_id = self.db.add_site(site_data)
        
        # Find or create rocket
        rocket_data = launch_data['rocket_data']
        rocket_id = self.db.find_or_create_rocket(
            rocket_data['name'], 
            rocket_data.get('external_id')
        )
        
        # Find status
        status_id = self.db.find_status_by_name(launch_data['status_name'])
        if not status_id:
            status_id = 1  # Default to first status
        
        # Build database record
        db_launch = {
            'launch_date': launch_data['launch_date'],
            'launch_time': launch_data['launch_time'],
            'launch_window_start': launch_data.get('launch_window_start'),
            'launch_window_end': launch_data.get('launch_window_end'),
            'site_id': site_id,
            'rocket_id': rocket_id,
            'mission_name': launch_data['mission_name'],
            'payload_name': launch_data.get('payload_name'),
            'orbit_type': launch_data.get('orbit_type'),
            'status_id': status_id,
            'success': launch_data.get('success'),
            'remarks': launch_data.get('remarks'),
            'source_url': launch_data.get('source_url'),
            'external_id': launch_data['external_id'],
            'data_source': 'SPACE_DEVS'
        }
        
        if existing:
            # Update existing launch
            self.db.update_launch(existing['launch_id'], db_launch)
            return ('updated', existing['launch_id'])
        else:
            # Add new launch
            launch_id = self.db.add_launch(db_launch)
            return ('added', launch_id)
    
    def sync_upcoming_launches(self, limit: int = 100) -> Dict:
        """
        Sync upcoming launches from Space Devs API
        Returns: Statistics about the sync operation
        """
        print(f"Fetching up to {limit} upcoming launches from Space Devs...")
        
        api_launches = self.fetch_upcoming_launches(limit=limit)
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        for api_launch in api_launches:
            try:
                launch_data = self.parse_launch_data(api_launch)
                action, launch_id = self.sync_launch_to_db(launch_data)
                
                if action == 'added':
                    added += 1
                    print(f"  + Added: {launch_data['mission_name']} ({launch_data['launch_date']})")
                elif action == 'updated':
                    updated += 1
                    print(f"  * Updated: {launch_data['mission_name']} ({launch_data['launch_date']})")
                else:
                    skipped += 1
            
            except Exception as e:
                errors.append(str(e))
                print(f"  âœ— Error processing launch: {e}")
        
        # Log sync
        status = 'SUCCESS' if not errors else 'PARTIAL'
        error_msg = '; '.join(errors[:5]) if errors else None
        self.db.log_sync('SPACE_DEVS_UPCOMING', added, updated, status, error_msg)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total_processed': len(api_launches)
        }
    
    def sync_date_range(self, start_date: str, end_date: str) -> Dict:
        """
        Sync launches within a date range
        start_date, end_date: YYYY-MM-DD format
        """
        print(f"Fetching launches from {start_date} to {end_date}...")
        
        api_launches = self.fetch_launches_by_date_range(start_date, end_date)
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        for api_launch in api_launches:
            try:
                launch_data = self.parse_launch_data(api_launch)
                action, launch_id = self.sync_launch_to_db(launch_data)
                
                if action == 'added':
                    added += 1
                elif action == 'updated':
                    updated += 1
                else:
                    skipped += 1
            
            except Exception as e:
                errors.append(str(e))
        
        # Log sync
        status = 'SUCCESS' if not errors else 'PARTIAL'
        error_msg = '; '.join(errors[:5]) if errors else None
        self.db.log_sync('SPACE_DEVS_RANGE', added, updated, status, error_msg)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total_processed': len(api_launches)
        }
    
    def sync_previous_launches(self, limit: int = 50) -> Dict:
        """Sync previous launches for historical data"""
        print(f"Fetching up to {limit} previous launches from Space Devs...")
        
        api_launches = self.fetch_previous_launches(limit=limit)
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        for api_launch in api_launches:
            try:
                launch_data = self.parse_launch_data(api_launch)
                action, launch_id = self.sync_launch_to_db(launch_data)
                
                if action == 'added':
                    added += 1
                elif action == 'updated':
                    updated += 1
                else:
                    skipped += 1
            
            except Exception as e:
                errors.append(str(e))
        
        # Log sync
        status = 'SUCCESS' if not errors else 'PARTIAL'
        error_msg = '; '.join(errors[:5]) if errors else None
        self.db.log_sync('SPACE_DEVS_PREVIOUS', added, updated, status, error_msg)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total_processed': len(api_launches)
        }


# Standalone sync script
if __name__ == '__main__':
    import sys
    
    db = LaunchDatabase()
    api = SpaceDevsAPI(db)
    
    print("=" * 60)
    print("SHOCKWAVE PLANNER - Space Devs Sync Utility")
    print("=" * 60)
    print()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'upcoming':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            result = api.sync_upcoming_launches(limit=limit)
        elif sys.argv[1] == 'previous':
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
            result = api.sync_previous_launches(limit=limit)
        elif sys.argv[1] == 'range':
            if len(sys.argv) < 4:
                print("Usage: python space_devs.py range START_DATE END_DATE")
                print("Example: python space_devs.py range 2025-01-01 2025-12-31")
                sys.exit(1)
            start = sys.argv[2]
            end = sys.argv[3]
            result = api.sync_date_range(start, end)
        else:
            print("Unknown command. Use: upcoming, previous, or range")
            sys.exit(1)
    else:
        # Default: sync upcoming
        result = api.sync_upcoming_launches(limit=100)
    
    print()
    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Added:      {result['added']}")
    print(f"Updated:    {result['updated']}")
    print(f"Skipped:    {result['skipped']}")
    print(f"Errors:     {len(result['errors'])}")
    print(f"Processed:  {result['total_processed']}")
    
    if result['errors']:
        print("\nErrors:")
        for error in result['errors'][:5]:
            print(f"  - {error}")
    
    db.close()
