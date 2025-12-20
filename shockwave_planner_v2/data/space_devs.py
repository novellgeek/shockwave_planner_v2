"""
SHOCKWAVE PLANNER v2.0 - Space Devs API Integration
Sync launches from The Space Devs Launch Library API

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0

API Documentation: https://ll.thespacedevs.com/2.3.0/swagger/
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data.database import LaunchDatabase


class SpaceDevsAPI:
    """Interface to The Space Devs Launch Library API"""
    
    BASE_URL = "https://lldev.thespacedevs.com/2.3.0/launches/"
    RATE_LIMIT_DELAY = 0.5  # seconds between requests
    
    def __init__(self, db: LaunchDatabase):
        """Initialize API client"""
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHOCKWAVE PLANNER v2.0 - Remix Astronautics'
        })
    
    def fetch_launches(self, params: Dict) -> List[Dict]:
        """
        Fetch launches from API with pagination
        
        Args:
            params: Query parameters
            
        Returns:
            List of launch dictionaries
        """
        all_launches = []
        url = self.BASE_URL
        first_page = True
        page = 1
        
        print(f"📡 Fetching launches from Space Devs API...")
        
        while url:
            try:
                print(f"   Page {page}...", end=' ')
                
                # Rate limiting (skip on first page)
                if not first_page:
                    time.sleep(self.RATE_LIMIT_DELAY)
                
                # Make request (params only on first page, then use 'next' URL)
                resp = self.session.get(
                    url, 
                    params=params if first_page else None,
                    timeout=30
                )
                
                # Handle rate limiting - wait and retry ONCE
                if resp.status_code == 429:
                    print("⚠️  Rate limited! Waiting 60 seconds...")
                    time.sleep(60)
                    
                    # Retry the request once
                    resp = self.session.get(
                        url,
                        params=params if first_page else None,
                        timeout=30
                    )
                    
                    # If still rate limited, give up on this batch
                    if resp.status_code == 429:
                        print("❌ Still rate limited after retry. Stopping sync.")
                        print(f"   Got {len(all_launches)} launches before rate limit.")
                        break
                
                if resp.status_code != 200:
                    print(f"❌ Error: HTTP {resp.status_code}")
                    break
                
                data = resp.json()
                results = data.get("results", [])
                all_launches.extend(results)
                
                print(f"✓ ({len(results)} launches)")
                
                # Get next page URL from response
                url = data.get("next")
                first_page = False
                page += 1
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
        
        print(f"✅ Fetched {len(all_launches)} total launches")
        return all_launches
    
    def fetch_upcoming_launches(self, limit: int = 100) -> List[Dict]:
        """Fetch upcoming launches from API - 1 year in the future"""
        now = datetime.utcnow()
        end_date = now + timedelta(days=365)  # Next 1 year
        
        params = {
            "net__gte": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "detailed",
            "limit": min(limit, 100),  # API max is 100 per page
            "ordering": "net",
        }
        
        return self.fetch_launches(params)
    
    def fetch_previous_launches(self, limit: int = 100) -> List[Dict]:
        """Fetch previous launches from API - 3 years in the past"""
        now = datetime.utcnow()
        start_date = now - timedelta(days=1095)  # Last 3 years (365 * 3)
        
        params = {
            "net__gte": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "detailed",
            "limit": min(limit, 100),
            "ordering": "-net",  # Reverse chronological
        }
        
        return self.fetch_launches(params)
    
    def fetch_launches_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Fetch launches within a date range"""
        # Parse dates and convert to UTC datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        params = {
            "net__gte": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "detailed",
            "limit": 100,
            "ordering": "net",
        }
        
        return self.fetch_launches(params)
    
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
        
        site_name_raw = location.get('name', 'Unknown')
        pad_name_raw = pad.get('name', 'Unknown')
        latitude = location.get('latitude')
        longitude = location.get('longitude')
        country_code = location.get('country_code', '')
        
        # Clean up pad name - remove location suffix if present
        # Example: "Space Launch Complex 40, Cape Canaveral SFS, FL, USA" -> "SLC-40"
        pad_name = pad_name_raw
        if ',' in pad_name_raw:
            # Take only the first part before the comma
            pad_name = pad_name_raw.split(',')[0].strip()
        
        # Shorten pad name
        pad_name = pad_name.replace("Space Launch Complex", "SLC")
        pad_name = pad_name.replace("Launch Complex", "LC")
        pad_name = pad_name.replace("Launch Area", "LA")
        pad_name = pad_name.replace("Launch Pad", "LP")
        
        # Clean up location name - remove country code suffix if present
        # Example: "Cape Canaveral Space Force Station, FL, USA" -> "Cape Canaveral SFS, FL"
        site_name = site_name_raw
        if country_code and site_name_raw.endswith(f", {country_code}"):
            # Remove ", USA" or ", CHN" etc from the end
            site_name = site_name_raw[:-len(country_code)-2].strip()
        
        # Further cleanup: shorten common long names
        site_name = site_name.replace("Space Force Station", "SFS")
        site_name = site_name.replace("Air Force Base", "AFB")
        site_name = site_name.replace("Rocket Launch Site", "RLS")
        
        # Parse rocket
        rocket = api_launch.get('rocket', {})
        configuration = rocket.get('configuration', {})
        
        rocket_name = configuration.get('full_name') or configuration.get('name', 'Unknown')
        rocket_family = configuration.get('family', '')
        rocket_variant = configuration.get('variant', '')
        rocket_manufacturer = configuration.get('manufacturer', {}).get('name', '') if configuration.get('manufacturer') else ''
        
        # Get country from manufacturer if available
        rocket_country = ''
        if configuration.get('manufacturer'):
            manufacturer_country = configuration.get('manufacturer', {}).get('country_code', '')
            if manufacturer_country:
                rocket_country = manufacturer_country
        
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
        # Space Devs uses these common statuses:
        # - Go for Launch, Go, TBD, TBC (pre-launch)
        # - Success, Launch Successful, Failure, Launch Failure, Partial Failure (post-launch)
        # - Hold, In Flight (active)
        status_mapping = {
            'Go for Launch': 'Go for Launch',
            'Go': 'Go for Launch',
            'TBC': 'Scheduled',
            'TBD': 'Scheduled',
            'To Be Confirmed': 'Scheduled',
            'To Be Determined': 'Scheduled',
            'Success': 'Success',
            'Launch Successful': 'Success',  # Space Devs uses this!
            'Failure': 'Failure',
            'Launch Failure': 'Failure',  # Space Devs uses this!
            'Partial Failure': 'Partial Failure',
            'In Flight': 'In Flight',
            'Hold': 'Hold',
            'On Hold': 'Hold',
        }
        mapped_status = status_mapping.get(status_name, 'Scheduled')
        
        # Log unmapped statuses for debugging
        if status_name not in status_mapping and status_name != 'Unknown':
            print(f"  ⚠ Unknown status from Space Devs: '{status_name}' - mapping to 'Scheduled'")
        
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
                'country': country_code,
                'external_id': str(pad.get('id')) if pad.get('id') else None
            },
            'rocket_data': {
                'name': rocket_name,
                'family': rocket_family,
                'variant': rocket_variant,
                'manufacturer': rocket_manufacturer,
                'country': rocket_country,
                'external_id': str(configuration.get('id')) if configuration.get('id') else None
            },
            'mission_name': mission_name,
            'payload_name': mission.get('name', ''),
            'orbit_type': orbit_name,
            'status_name': mapped_status,
            'success': success,
            'remarks': mission_description[:500] if mission_description else None,
            'source_url': api_launch.get('url'),
            'external_id': str(api_launch.get('id')) if api_launch.get('id') else None,
            'data_source': 'SPACE_DEVS'
        }
    
    def sync_launch_to_db(self, launch_data: Dict) -> Tuple[str, int]:
        """
        Sync a parsed launch to the database
        Returns: (action, launch_id) where action is 'added', 'updated', or 'skipped'
        """
        
        # Ensure external_id is string
        external_id = str(launch_data.get('external_id', ''))
        if not external_id:
            print(f"  ⚠ Warning: Launch has no external_id, skipping")
            return ('skipped', 0)
        
        # Check if launch already exists
        existing = self.db.find_launch_by_external_id(external_id)
        
        # Find or create site
        site_data = launch_data['site_data']
        site_id = None
        sites = self.db.get_all_sites()
        for site in sites:
            if (site.get('location') == site_data.get('location') and 
                site.get('launch_pad') == site_data.get('launch_pad')):
                site_id = site['site_id']
                break
        
        if not site_id:
            try:
                site_id = self.db.add_site(site_data)
            except Exception as e:
                print(f"  ⚠ Warning: Could not create site: {e}")
                return ('skipped', 0)
        
        # Find or create rocket with full details
        rocket_data = launch_data['rocket_data']
        rocket_id = None
        rocket_external_id = str(rocket_data.get('external_id', '')) if rocket_data.get('external_id') else None
        
        # Try to find existing rocket by external_id
        if rocket_external_id:
            rockets = self.db.get_all_rockets()
            for rocket in rockets:
                if rocket.get('external_id') == rocket_external_id:
                    rocket_id = rocket['rocket_id']
                    # Update with latest data
                    try:
                        self.db.update_rocket(rocket_id, rocket_data)
                    except:
                        pass  # Update failed, but we have the ID
                    break
        
        # If not found by external_id, try by name
        if not rocket_id:
            rockets = self.db.get_all_rockets()
            for rocket in rockets:
                if rocket.get('name') == rocket_data.get('name'):
                    rocket_id = rocket['rocket_id']
                    # Update with latest data
                    try:
                        self.db.update_rocket(rocket_id, rocket_data)
                    except:
                        pass
                    break
        
        # If still not found, create new rocket with full data
        if not rocket_id:
            try:
                rocket_id = self.db.add_rocket(rocket_data)
            except Exception as e:
                print(f"  ⚠ Warning: Could not create rocket: {e}")
                return ('skipped', 0)
        
        # Find status
        status_name_mapped = launch_data['status_name']
        status_id = self.db.find_status_by_name(status_name_mapped)
        if not status_id:
            print(f"  ⚠ Warning: Status '{status_name_mapped}' not found in database, defaulting to 'Scheduled'")
            status_id = self.db.find_status_by_name('Scheduled')
            if not status_id:
                status_id = 1  # Fallback to first status
        
        # Build database record - only include fields that exist in SHOCKWAVE schema
        db_launch = {
            'launch_date': launch_data.get('launch_date'),
            'launch_time': launch_data.get('launch_time'),
            'launch_window_start': launch_data.get('launch_window_start'),
            'launch_window_end': launch_data.get('launch_window_end'),
            'site_id': site_id,
            'rocket_id': rocket_id,
            'mission_name': launch_data.get('mission_name', '')[:200],  # Limit length
            'payload_name': launch_data.get('payload_name', '')[:200],
            'orbit_type': launch_data.get('orbit_type', '')[:50],
            'status_id': status_id,
            'success': launch_data.get('success'),
            'remarks': launch_data.get('remarks', '')[:500] if launch_data.get('remarks') else None,
            'source_url': launch_data.get('source_url', '')[:500],
            'external_id': external_id,
            'data_source': 'SPACE_DEVS'
        }
        
        try:
            if existing:
                # Update existing launch
                self.db.update_launch(existing['launch_id'], db_launch)
                return ('updated', existing['launch_id'])
            else:
                # Add new launch
                launch_id = self.db.add_launch(db_launch)
                return ('added', launch_id)
        except Exception as e:
            print(f"  ✗ Error saving launch: {e}")
            return ('skipped', 0)
    
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
                    mission = launch_data.get('mission_name', 'Unknown')[:50]
                    date = launch_data.get('launch_date', 'Unknown')
                    print(f"  + Added: {mission} ({date})")
                elif action == 'updated':
                    updated += 1
                    mission = launch_data.get('mission_name', 'Unknown')[:50]
                    date = launch_data.get('launch_date', 'Unknown')
                    print(f"  * Updated: {mission} ({date})")
                else:
                    skipped += 1
            
            except Exception as e:
                error_msg = str(e)[:100]
                errors.append(error_msg)
                print(f"  X Error: {error_msg}")
                skipped += 1
        
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
    
    def sync_full_range(self) -> Dict:
        """
        Sync full date range: 3 years past + 1 year future
        This is the comprehensive sync that gets all relevant launches
        """
        print("=" * 60)
        print("FULL RANGE SYNC: 3 years past + 1 year future")
        print("=" * 60)
        
        now = datetime.utcnow()
        start_date = now - timedelta(days=1095)  # 3 years ago
        end_date = now + timedelta(days=365)     # 1 year ahead
        
        # Break into 30-day chunks to avoid API limitations
        all_results = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': [],
            'total_processed': 0
        }
        
        current_start = start_date
        chunk_num = 1
        
        while current_start < end_date:
            # Calculate chunk end (30 days or remaining time)
            chunk_end = min(current_start + timedelta(days=30), end_date)
            
            start_str = current_start.strftime('%Y-%m-%d')
            end_str = chunk_end.strftime('%Y-%m-%d')
            
            print(f"\n📅 Chunk {chunk_num}: {start_str} to {end_str}")
            
            try:
                # Sync this chunk
                chunk_result = self.sync_date_range(start_str, end_str)
                
                # Aggregate results
                all_results['added'] += chunk_result['added']
                all_results['updated'] += chunk_result['updated']
                all_results['skipped'] += chunk_result['skipped']
                all_results['errors'].extend(chunk_result['errors'])
                all_results['total_processed'] += chunk_result['total_processed']
                
            except Exception as e:
                error_msg = f"Chunk {chunk_num} failed: {e}"
                all_results['errors'].append(error_msg)
                print(f"❌ {error_msg}")
            
            # Move to next chunk
            current_start = chunk_end + timedelta(days=1)
            chunk_num += 1
            
            # Small delay between chunks to be nice to the API
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print("FULL RANGE SYNC COMPLETE")
        print("=" * 60)
        print(f"Total Added:     {all_results['added']}")
        print(f"Total Updated:   {all_results['updated']}")
        print(f"Total Skipped:   {all_results['skipped']}")
        print(f"Total Errors:    {len(all_results['errors'])}")
        print(f"Total Processed: {all_results['total_processed']}")
        
        # Log the full sync
        status = 'SUCCESS' if not all_results['errors'] else 'PARTIAL'
        error_msg = '; '.join(all_results['errors'][:10]) if all_results['errors'] else None
        self.db.log_sync('SPACE_DEVS_FULL_RANGE', 
                        all_results['added'], 
                        all_results['updated'], 
                        status, 
                        error_msg)
        
        return all_results
    
    def sync_rocket_details(self) -> dict:
        """
        Update existing rockets with details from Space Devs
        Returns: {'updated': count, 'errors': [...]}
        """
        print("🚀 Updating rocket details from Space Devs...")
        
        # Get all rockets from database
        rockets = self.db.get_all_rockets()
        
        updated_count = 0
        errors = []
        
        for rocket in rockets:
            rocket_id = rocket['rocket_id']
            external_id = rocket.get('external_id')
            
            # Skip if no external_id - can't look it up
            if not external_id:
                print(f"   Skipping {rocket['name']} (no external_id)")
                continue
            
            try:
                # Fetch rocket config from Space Devs
                url = f"https://ll.thespacedevs.com/2.3.0/config/launcher/{external_id}/"
                
                print(f"   Fetching details for: {rocket['name']}...", end=' ')
                
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 404:
                    print("⚠️  Not found")
                    continue
                
                if resp.status_code != 200:
                    print(f"❌ HTTP {resp.status_code}")
                    continue
                
                config = resp.json()
                
                # Extract details
                rocket_data = {
                    'name': config.get('full_name') or config.get('name', rocket['name']),
                    'family': config.get('family', ''),
                    'variant': config.get('variant', ''),
                    'manufacturer': config.get('manufacturer', {}).get('name', '') if config.get('manufacturer') else '',
                    'country': config.get('manufacturer', {}).get('country_code', '') if config.get('manufacturer') else '',
                }
                
                # Update rocket - PRESERVE MANUAL DATA (alternative_name, boosters, payload_sso, payload_tli)
                self.db.update_rocket_preserve_manual(rocket_id, rocket_data)
                updated_count += 1
                print("✓")
                
                # Rate limiting
                time.sleep(self.RATE_LIMIT_DELAY)
                
            except Exception as e:
                error_msg = f"Error updating {rocket['name']}: {e}"
                errors.append(error_msg)
                print(f"❌ {e}")
        
        print(f"\n✅ Updated {updated_count} rockets")
        
        return {
            'updated': updated_count,
            'errors': errors
        }
    
    def fetch_all_rockets(self) -> List[Dict]:
        """
        Fetch all launcher configurations from Space Devs API
        Returns: List of rocket configuration dictionaries
        """
        all_rockets = []
        url = "https://ll.thespacedevs.com/2.3.0/config/launcher/"
        page = 1
        
        print("🚀 Fetching all rockets from Space Devs API...")
        
        while url:
            try:
                print(f"   Page {page}...", end=' ')
                
                if page > 1:
                    time.sleep(self.RATE_LIMIT_DELAY)
                
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 429:
                    print("⚠️  Rate limited! Waiting 60 seconds...")
                    time.sleep(60)
                    resp = self.session.get(url, timeout=30)
                
                if resp.status_code != 200:
                    print(f"❌ Error: HTTP {resp.status_code}")
                    break
                
                data = resp.json()
                results = data.get("results", [])
                all_rockets.extend(results)
                
                print(f"✓ ({len(results)} rockets)")
                
                url = data.get("next")
                page += 1
                
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break
        
        print(f"✅ Fetched {len(all_rockets)} total rockets")
        return all_rockets
    
    def sync_all_rockets(self) -> dict:
        """
        Fetch all rockets from SpaceDevs and add/update them in the database
        This is a comprehensive sync of the entire rocket catalog
        Returns: {'added': count, 'updated': count, 'skipped': count, 'errors': [...]}
        """
        print("=" * 60)
        print("SYNCING ALL ROCKETS FROM SPACE DEVS")
        print("=" * 60)
        print()
        
        # Fetch all rockets from API
        api_rockets = self.fetch_all_rockets()
        
        if not api_rockets:
            print("❌ No rockets fetched from API")
            return {'added': 0, 'updated': 0, 'skipped': 0, 'errors': ['No rockets fetched']}
        
        # Get existing rockets from database
        existing_rockets = self.db.get_all_rockets()
        existing_by_external_id = {r.get('external_id'): r for r in existing_rockets if r.get('external_id')}
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        print(f"\n📊 Processing {len(api_rockets)} rockets...")
        print()
        
        for api_rocket in api_rockets:
            try:
                external_id = str(api_rocket.get('id', ''))
                
                if not external_id:
                    skipped += 1
                    continue
                
                # Prepare rocket data
                rocket_data = {
                    'name': api_rocket.get('full_name') or api_rocket.get('name', 'Unknown'),
                    'family': api_rocket.get('family', ''),
                    'variant': api_rocket.get('variant', ''),
                    'manufacturer': api_rocket.get('manufacturer', {}).get('name', '') if api_rocket.get('manufacturer') else '',
                    'country': api_rocket.get('manufacturer', {}).get('country_code', '') if api_rocket.get('manufacturer') else '',
                    'external_id': external_id,
                    'external_source': 'SPACE_DEVS'
                }
                
                # Check if rocket already exists
                if external_id in existing_by_external_id:
                    # Update existing rocket - PRESERVE MANUAL DATA
                    existing = existing_by_external_id[external_id]
                    self.db.update_rocket_preserve_manual(existing['rocket_id'], rocket_data)
                    updated += 1
                    print(f"   ↻ Updated: {rocket_data['name']}")
                else:
                    # Add new rocket
                    self.db.add_rocket(rocket_data)
                    added += 1
                    print(f"   + Added: {rocket_data['name']}")
                
            except Exception as e:
                error_msg = f"Error processing rocket: {e}"
                errors.append(error_msg)
                print(f"   ❌ Error: {e}")
                skipped += 1
        
        print()
        print("=" * 60)
        print("ROCKET SYNC COMPLETE")
        print("=" * 60)
        print(f"Added:   {added}")
        print(f"Updated: {updated}")
        print(f"Skipped: {skipped}")
        print(f"Errors:  {len(errors)}")
        
        # Log sync
        status = 'SUCCESS' if not errors else 'PARTIAL'
        error_msg = '; '.join(errors[:10]) if errors else None
        self.db.log_sync('SPACE_DEVS_ALL_ROCKETS', added, updated, status, error_msg)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors
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
        elif sys.argv[1] == 'full':
            # Sync full 4-year range (3 years past + 1 year future)
            result = api.sync_full_range()
        elif sys.argv[1] == 'range':
            if len(sys.argv) < 4:
                print("Usage: python space_devs.py range START_DATE END_DATE")
                print("Example: python space_devs.py range 2025-01-01 2025-12-31")
                sys.exit(1)
            start = sys.argv[2]
            end = sys.argv[3]
            result = api.sync_date_range(start, end)
        elif sys.argv[1] == 'rockets':
            # NEW: Sync all rockets from SpaceDevs
            result = api.sync_all_rockets()
        elif sys.argv[1] == 'update-rockets':
            # NEW: Update existing rockets only
            result = api.sync_rocket_details()
        else:
            print("Unknown command.")
            print("Available commands:")
            print("  upcoming [limit]  - Sync upcoming launches (1 year ahead)")
            print("  previous [limit]  - Sync previous launches (3 years back)")
            print("  full              - Sync full range (3 years back + 1 year ahead)")
            print("  range START END   - Sync specific date range (YYYY-MM-DD)")
            print("  rockets           - Sync ALL rockets from SpaceDevs (add new + update existing)")
            print("  update-rockets    - Update existing rockets only (no new additions)")
            sys.exit(1)
    else:
        # Default: sync upcoming
        result = api.sync_upcoming_launches(limit=100)
    
    print()
    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    
    # Handle different result formats
    if 'total_processed' in result:
        # Launch sync results
        print(f"Added:      {result['added']}")
        print(f"Updated:    {result['updated']}")
        print(f"Skipped:    {result['skipped']}")
        print(f"Errors:     {len(result['errors'])}")
        print(f"Processed:  {result['total_processed']}")
    else:
        # Rocket sync results (or other formats)
        print(f"Added:      {result.get('added', 0)}")
        print(f"Updated:    {result.get('updated', 0)}")
        print(f"Skipped:    {result.get('skipped', 0)}")
        print(f"Errors:     {len(result.get('errors', []))}")
    
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors'][:5]:
            print(f"  - {error}")
    
    db.close()
