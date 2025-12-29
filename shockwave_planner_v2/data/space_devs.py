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
import logging

# Data Models
from data.db.models.launch import Launch
from data.db.models.launch_site import LaunchSite
from data.db.models.rocket import Rocket
from data.db.models.status import Status
from data.db.models.sync_log import SyncLog

class SpaceDevsClient:
    """Interface to The Space Devs Launch Library API"""
    
    BASE_URL = "https://lldev.thespacedevs.com/2.3.0/launches/"
    
    REQ_PER_HOUR = 15
    RATE_LIMIT_DELAY = 60/REQ_PER_HOUR  # seconds between requests

    def __init__(self):
        """Initialize API client"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SHOCKWAVE PLANNER v2.0 - Remix Astronautics'
        })
    
    def fetch_upcoming_launches(self, max_launches: int = 100) -> List[Dict]:
        """Fetch upcoming launches from API - 1 year in the future"""
        now = datetime.utcnow()
        end_date = now + timedelta(days=365)  # Next 1 year
        
        params = {
            "net__gte": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "detailed",
            "limit": min(max_launches, 100),  # API max is 100 per page
            "ordering": "net",
        }
        
        return self._fetch(self.BASE_URL, params, max_launches)
    
    def fetch_previous_launches(self, max_launches: int = 100) -> List[Dict]:
        """Fetch previous launches from API - 3 years in the past"""
        now = datetime.utcnow()
        start_date = now - timedelta(days=365*3)  # Last 3 years (365 * 3)
        
        params = {
            "net__gte": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "net__lte": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": "detailed",
            "limit": min(max_launches, 100),
            "ordering": "-net",  # Reverse chronological
        }
        
        return self._fetch(self.BASE_URL, params, max_launches)
    
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
        
        return self._fetch(self.BASE_URL, params)
    
    def _fetch(self, url: str, params: Dict, max_results = float('inf')) -> List[Dict]:
        """
        Fetch launches from API
        
        Args:
            params: Query parameters
            
        Returns:
            List of launch dictionaries
        """
        results  = []
        num_results = 0

        logging.info(f"📡 Fetching launches from Space Devs API...")
        
        try:           
            # Make request (params only on first page, then use 'next' URL)
            resp = self.session.get(
                url, 
                params=params,
                timeout=30
            )
            
            response_json = resp.json()
            content = response_json["results"]
            results.extend(content)

            url = response_json["next"]
            num_results += params["limit"]
            params["limit"] = 100 if (max_results - num_results) % 100 == 0 else (max_results - num_results) % 100

            while url is not None and num_results < max_results:
                # Rate limiting
                time.sleep(self.RATE_LIMIT_DELAY)
            
                # Make request
                resp = self.session.get(
                    url,
                    params=params,
                    timeout=30
                )
                
                # # TODO Handle rate limiting - wait and retry ONCE
                # if resp.status_code == 429:
                #     print("⚠️  Rate limited! Waiting 60 seconds...")
                #     time.sleep(60)
                    
                #     # Retry the request once
                #     resp = self.session.get(
                #         url,
                #         params=params if first_page else None,
                #         timeout=30
                #     )
                    
                #     # If still rate limited, give up on this batch
                #     if resp.status_code == 429:
                #         print("❌ Still rate limited after retry. Stopping sync.")
                #         print(f"   Got {len(all_launches)} launches before rate limit.")
                        
                
                if resp.status_code != 200:
                    logging.error(f"❌ Error: HTTP {resp.status_code}")
                    raise requests.HTTPError(response=resp)

                response_json = resp.json()
                content = response_json["results"]
                results.extend(content)
            
                url = response_json["next"]
                num_results += params["limit"]

            logging.info(f"✓ ({len(results)} launches)")
            return results
            
        except Exception as e:
            logging.error(f"❌ Error fetching: {e}")
            return []
    
    # FIXME properly handle data inputs
    def _parse_launch_data(self, launch: Dict):
        """Parse Space Devs launch data into database format"""
        try:
            # Parse Launch data
            # Launch window - datetime 
            window_start = launch['window_start']
            window_end = launch['window_end']
            
            # launch date and launch time
            net = launch['net']  # No Earlier Than (ISO format)
            launch_date = None
            launch_time = None
            
            if net is not None:
                # extract date and time from datetime group
                try:
                    dt = datetime.fromisoformat(net.replace('Z', '+00:00'))
                    launch_date = dt.strftime('%Y-%m-%d')
                    launch_time = dt.strftime('%H:%M:%S')
                except Exception as e:
                    logging.error("Error parsing launch date/time: " + str(e))
            
            # source url for data
            source_url = launch["url"]
            last_update_time = launch["last_updated"].replace('Z', '+00:00')
            last_updated = dt = datetime.fromisoformat(last_update_time)

            # Space Devs id for launch
            external_id = launch["id"]

            # Parse Launch Site
            # extract launch site data
            launch_pad = dict(launch["pad"])
            pad_location = dict(launch_pad['location'])
            
            # name of launch facility
            site_name = str(pad_location.get('name', 'Unknown'))
            # name of specific launch pad at facility
            pad_name = str(launch_pad.get('name', 'Unknown'))
            
            # location of launch pad
            latitude = pad_location['latitude']
            longitude = pad_location['longitude']
            country_code = pad_location["country"]["alpha_3_code"]
            
            # Clean up pad name - remove location suffix if present
            # Example: "Space Launch Complex 40, Cape Canaveral SFS, FL, USA" -> "SLC-40"
            if pad_name.find(",") != -1:
                # Take only the first part before the comma
                pad_name = pad_name.split(',')[0].strip()
            
            # Shorten pad name
            pad_name = pad_name.replace("Space Launch Complex", "SLC")
            pad_name = pad_name.replace("Launch Complex", "LC")
            pad_name = pad_name.replace("Launch Area", "LA")
            pad_name = pad_name.replace("Launch Pad", "LP")
            
            # TODO FIX -> need to find first comma and remove everything afterwards
            # Clean up location name - remove country code suffix if present
            # Example: "Cape Canaveral Space Force Station, FL, USA" -> "Cape Canaveral SFS, FL"
            if country_code and site_name.endswith(f", {country_code}"):
                # Remove ", USA" or ", CHN" etc from the end
                site_name = site_name[:-len(country_code)-2].strip()
            
            site_name = site_name[:site_name.find(",")]

            # Further cleanup: shorten common long names
            site_name = site_name.replace("Space Force Station", "SFS")
            site_name = site_name.replace("Air Force Base", "AFB")
            site_name = site_name.replace("Rocket Launch Site", "RLS")
            
            # extract rocket data
            rocket = launch['rocket']
            configuration = rocket['configuration']
            
            rocket_name = configuration.get('full_name') or configuration.get('name', 'Unknown')
            # # TODO handle rocket family
            # rocket_family = configuration['families']
            rocket_family = "TODO: IMPLEMENT"
            rocket_variant = configuration['variant']
            rocket_manufacturer = configuration['manufacturer']['name']
            rocket_country = configuration['manufacturer']['country'][0]['name']
            rocket_min_stages = configuration["min_stage"]
            rocket_height = configuration["length"]
            rocket_diameter = configuration["diameter"]
            rocket_payload_leo = configuration["leo_capacity"]
            rocket_payload_gto = configuration["gto_capacity"]
            rocket_payload_sso = configuration["sso_capacity"]
            rocket_mass = configuration["launch_mass"]

            # extract mission data
            mission = launch['mission']
            mission_name = mission["name"]
            mission_description = mission['description']
            orbit = mission['orbit']
            orbit_name = orbit['abbrev']
            
            # Parse status
            status = launch.get('status', {})
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
                logging.error(f"  ⚠ Unknown status from Space Devs: '{status_name}' - mapping to 'Scheduled'")
            
            # Determine success
            success = None
            if status_name == 'Success':
                success = True
            elif status_name in ['Failure', 'Partial Failure']:
                success = False
            
            return {
                "launch_data": {
                    'launch_date': launch_date,
                    'launch_time': launch_time,
                    'launch_window_start': window_start,
                    'launch_window_end': window_end,
                    'mission_name': mission_name,
                    'payload_name': mission_name,
                    'orbit_type': orbit_name,
                    'status_name': mapped_status,
                    'status_abbr': status_abbr,
                    'success': success,
                    'remarks': mission_description,
                    'source_url': source_url,
                    'external_id': external_id,
                    'data_source': 'SPACE_DEVS',
                    'last_updated': last_updated
                },
                'site_data': {
                    'name': site_name,
                    'launch_pad': pad_name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': country_code,
                    'external_id': launch_pad["id"]
                },
                'rocket_data': {
                    'name': rocket_name,
                    'family': rocket_family,
                    'variant': rocket_variant,
                    'manufacturer': rocket_manufacturer,
                    'country': rocket_country,
                    'payload_leo': rocket_payload_leo,
                    "payload_gto": rocket_payload_gto,
                    "payload_sso": rocket_payload_sso,
                    "height": rocket_height,
                    "diameter": rocket_diameter,
                    "mass": rocket_mass,
                    "stages": rocket_min_stages,
                    'external_id': rocket["id"]
                }
            }
        except Exception as e:
            logging.error("Error parsing launch: " + str(e.__traceback__))
            return {}

    def _sync_launch_to_db(self, parsed_data: Dict):
        """
        Sync a parsed launch to the database
        Returns: (action, launch_id) where action is 'added', 'updated', or 'skipped'
        """

        launch_data = parsed_data["launch_data"]
        site_data = parsed_data["site_data"]
        rocket_data = parsed_data["rocket_data"]

        # Update or create site
        try:
            # TODO: add suppport for multiple site_types
            # TODO: add support for different turnaround days field is fastest_turnaround (ISO 8601 duration format) in rocket['configuration']
            site, _ = LaunchSite.objects.update_or_create(
                external_id=site_data["external_id"],
                defaults=site_data
            )

        except Exception as e:
            logging.error(f"  ⚠ Could not create LaunchSite: {e}")
            return ('skipped', 0)
        
        # Update or create rocket
        try:
            rocket, _ = Rocket.objects.update_or_create(
                external_id=rocket_data["external_id"],
                name=rocket_data["name"],               
                defaults=rocket_data
            )
        except Exception as e:
            logging.error(f"  ⚠ Could not create Rocket {rocket_data['name'], rocket_data['external_id'], launch_data['external_id']} : {e}")
            return ('skipped', 0)
        
        # Find status
        status_name_mapped = launch_data['status_name']      
        status = Status.objects.filter(name=status_name_mapped).first()

        if status is None:
            print(f"  ⚠ Warning: Status '{status_name_mapped}' not found in database, defaulting to 'Scheduled'")
            status = Status.objects.filter(name="Scheduled").first()
            if status is None:
                status_id = 1  # Fallback to first status
            else:
                status_id = status.pk
        else:
            status_id = status.pk

        # TODO add in missing inputs
        try:                       
            launch_input = {
                'launch_date': launch_data['launch_date'],
                'launch_time': launch_data['launch_time'],
                'launch_window_start': launch_data['launch_window_start'],
                'launch_window_end': launch_data['launch_window_end'],
                'site_id': site.pk,
                'rocket_id': rocket.pk,
                'mission_name': launch_data['mission_name'],
                'payload_name': launch_data['payload_name'],
                "payload_mass": None,
                'orbit_type': launch_data['orbit_type'],
                "orbit_altitude": None,
                "inclination": None,
                'success': launch_data['success'],
                "failure_reason": None,
                'remarks': launch_data['remarks'],
                'source_url': launch_data['source_url'],
                'status_id': status_id,
                'data_source': 'SPACE_DEVS',
                'external_id': launch_data["external_id"],
                'last_updated': launch_data["last_updated"]
            }

            launch, _ = Launch.objects.update_or_create(external_id=launch_data["external_id"], defaults=launch_input)

        except Exception as e:
            logging.error(f"  ✗ Error saving launch: {e}")
            return ('skipped', 0)

        return ('added', launch.pk)

    def sync_upcoming_launches(self, limit: int = 100) -> Dict:
        """
        Sync upcoming launches from Space Devs API
        Returns: Statistics about the sync operation
        """
        print(f"Fetching up to {limit} upcoming launches from Space Devs...")
        
        api_launches = self.fetch_upcoming_launches(limit)
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        for launch in api_launches:
            try:
                launch_data = self._parse_launch_data(launch)
                action, _ = self._sync_launch_to_db(launch_data)
                
                if action == 'added':
                    added += 1
                    mission = launch_data["launch_data"]['mission_name'][:50]
                    date = launch_data["launch_data"]['launch_date']
                    print(f"  + Added: {mission} ({date})")
                elif action == 'updated':
                    updated += 1
                    mission = launch_data["launch_data"]['mission_name'][:50]
                    date = launch_data["launch_data"]['launch_date']
                    print(f"  * Updated: {mission} ({date})")
                else:
                    skipped += 1
            
            except Exception as e:
                error_msg = str(e)[:100]
                errors.append(error_msg)
                logging.error(f"  X Error: {error_msg}")
                skipped += 1
        
        # Log sync
        status = 'SUCCESS' if not errors else 'PARTIAL'
        error_msg = '; '.join(errors[:5]) if errors else None
        sync_data = {
            "data_source": "SPACE_DEVS_UPCOMING",
            "records_added": added,
            "records_updated": updated,
            "status": status,
            "error_msg": error_msg
        }
        SyncLog.objects.create(**sync_data)

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
                launch_data = self._parse_launch_data(api_launch)
                action, launch_id = self._sync_launch_to_db(launch_data)
                
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
        sync_data = {
            "data_source": "SPACE_DEVS_RANGE",
            "records_added": added,
            "records_updated": updated,
            "status": status,
            "error_msg": error_msg
        }
        SyncLog.objects.create(**sync_data)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors,
            'total_processed': len(api_launches)
        }
    
    def sync_previous_launches(self, limit: int = 100) -> Dict:
        """Sync previous launches for historical data"""
        print(f"Fetching up to {limit} previous launches from Space Devs...")
        
        api_launches = self.fetch_previous_launches(limit)
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        for api_launch in api_launches:
            try:
                launch_data = self._parse_launch_data(api_launch)
                action, _ = self._sync_launch_to_db(launch_data)
                
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
        sync_data = {
            "data_source": "SPACE_DEVS_PREVIOUS",
            "records_added": added,
            "records_updated": updated,
            "status": status,
            "error_msg": error_msg
        }
        SyncLog.objects.create(**sync_data)
        
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
        
        # Log sync
        status = 'SUCCESS' if not all_results['errors'] else 'PARTIAL'
        error_msg = '; '.join(all_results['errors'][:10]) if all_results['errors'] else None
        sync_data = {
            "data_source": "SPACE_DEVS_FULL_RANGE",
            "records_added": all_results['added'],
            "records_updated": all_results['updated'],
            "status": status,
            "error_msg": error_msg
        }
        SyncLog.objects.create(**sync_data)
        
        return all_results
    
    def sync_rocket_details(self) -> dict:
        """
        Update existing rockets with details from Space Devs
        Returns: {'updated': count, 'errors': [...]}
        """
        logging.info("🚀 Updating rocket details from Space Devs...")
        
        # Get all rockets from database
        rockets = Rocket.objects.all()

        updated_count = 0
        errors = []
        
        # TODO optimise -> reduce number of api calls made        
        for rocket in rockets:
            external_id = rocket.external_id
            
            # Skip if no external_id - can't look it up
            if external_id is None:
                logging.warning(f"   Skipping {rocket.name} (no external_id)")
                continue
            
            try:
                # Fetch rocket config from Space Devs
                url = f"https://lldev.thespacedevs.com/2.3.0/config/launcher/{external_id}/"
                
                logging.info(f"   Fetching details for: {rocket.name}...")
                
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 404:
                    logging.error(f"⚠️  {rocket.name} Not found")
                    continue
                
                if resp.status_code != 200:
                    logging.error(f"❌ HTTP error: {resp.status_code}")
                    continue
                
                config = resp.json()
                
                # Extract details
                rocket_data = {
                    'name': config.get('full_name') or config.get('name', 'Unknown'),
                    'family': "TODO: IMPLEMENT",
                    'variant': config['variant'],
                    'manufacturer': config['manufacturer']['name'],
                    'country': config['manufacturer']['country'][0]['name'],
                }
                
                # Update rocket - PRESERVE MANUAL DATA (alternative_name, boosters, payload_sso, payload_tli)
                rocket.objects.update(**rocket_data)
                updated_count += 1
                print("✓")
                
                # Rate limiting
                time.sleep(self.RATE_LIMIT_DELAY)
                
            except Exception as e:
                error_msg = f"Error updating {rocket.name}: {e}"
                errors.append(error_msg)
                logging.error(f"❌ {e}")
        
        logging.info(f"\n✅ Updated {updated_count} rockets")
        
        return {
            'updated': updated_count,
            'errors': errors
        }
    
    def fetch_all_rockets(self) -> List[Dict]: #FIXME
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
        
        url = "https://lldev.thespacedevs.com/2.3.0/launcher_configurations/"
        params = {"limit": 100}

        # Fetch all rockets from API
        api_rockets = self._fetch(url, params=params)
        
        if api_rockets == []:
            logging.error("❌ No rockets fetched from API")
            return {'added': 0, 'updated': 0, 'skipped': 0, 'errors': ['No rockets fetched']}
        
        # Get existing rockets from database
        existing_rockets = Rocket.objects.all()
        existing_by_external_id = {r.external_id: r for r in existing_rockets if r.external_id is None}
        
        added = 0
        updated = 0
        skipped = 0
        errors = []
        
        print(f"\n📊 Processing {len(api_rockets)} rockets...")
        print()
        
        for api_rocket in api_rockets:
            try:
                external_id = str(api_rocket['id'])
                
                if external_id != '':
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
        error_msg = '; '.join(errors[:5]) if errors else None
        sync_data = {
            "data_source": "SPACE_DEVS_ALL_ROCKETS",
            "records_added": added,
            "records_updated": updated,
            "status": status,
            "error_msg": error_msg
        }
        SyncLog.objects.create(**sync_data)
        
        return {
            'added': added,
            'updated': updated,
            'skipped': skipped,
            'errors': errors
        }