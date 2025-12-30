"""
SHOCKWAVE PLANNER v2.1 - Enhanced Launch Site Map View
Interactive 2D world map with launch selection, NOTAM visualization, and flight paths

Features:
- Launch site markers (color-coded by activity)
- Launch selection dropdown
- Auto-zoom to selected launch
- NOTAM area parsing and visualization
- Great circle paths from launch to NOTAM
- Custom NOTAM area drawing

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                              QLabel, QComboBox, QPushButton, QDateEdit, 
                              QTextEdit, QCheckBox, QSpinBox, QDoubleSpinBox,
                              QFormLayout)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon
import matplotlib.pyplot as plt
import numpy as np
import re
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    print("Warning: cartopy not available, using simple matplotlib map")

from datetime import datetime, timedelta

# import data models
from data.db.models.launch import Launch
from data.db.models.launch_notam import LaunchNotam
from data.db.models.launch_site import LaunchSite

class NotamParser:
    """Parse NOTAM coordinate strings into lat/lon coordinates"""
    
    @staticmethod
    def parse_coordinate(coord_str):
        """
        Parse NOTAM coordinate format: N301900E1103700
        Returns: (lat, lon) in decimal degrees
        
        Format:
        - N/S followed by DDMMSS (degrees, minutes, seconds)
        - E/W followed by DDDMMSS (degrees, minutes, seconds)
        """
        # Match patterns like N301900E1103700
        pattern = r'([NS])(\d{2})(\d{2})(\d{2})([EW])(\d{3})(\d{2})(\d{2})'
        match = re.match(pattern, coord_str.strip())
        
        if not match:
            return None
        
        lat_dir, lat_deg, lat_min, lat_sec, lon_dir, lon_deg, lon_min, lon_sec = match.groups()
        
        # Convert to decimal degrees
        lat = int(lat_deg) + int(lat_min)/60 + int(lat_sec)/3600
        lon = int(lon_deg) + int(lon_min)/60 + int(lon_sec)/3600
        
        # Apply direction
        if lat_dir == 'S':
            lat = -lat
        if lon_dir == 'W':
            lon = -lon
        
        return (lat, lon)
    
    @staticmethod
    def parse_notam_area(notam_text):
        """
        Parse NOTAM text to extract danger area coordinates
        
        Example input:
        "A TEMPORARY DANGER AREA ESTABLISHED BOUNDED BY: 
         N301900E1103700-N301700E1110000-N293800E1105700-N294000E1103400, 
         BACK TO START."
        
        Returns: [(lat1, lon1), (lat2, lon2), ...] or None
        """
        # Find the bounded area section
        bounded_match = re.search(r'BOUNDED BY:\s*([^.]+)', notam_text, re.IGNORECASE)
        if not bounded_match:
            return None
        
        bounded_text = bounded_match.group(1)
        
        # Extract coordinate strings (pattern: N123456E1234567)
        coord_pattern = r'[NS]\d{6}[EW]\d{7}'
        coord_strings = re.findall(coord_pattern, bounded_text)
        
        if not coord_strings:
            return None
        
        # Parse each coordinate
        coordinates = []
        for coord_str in coord_strings:
            coord = NotamParser.parse_coordinate(coord_str)
            if coord:
                coordinates.append(coord)
        
        return coordinates if coordinates else None
    
    @staticmethod
    def calculate_polygon_center(coordinates):
        """Calculate centroid of polygon"""
        if not coordinates:
            return None
        
        lats = [c[0] for c in coordinates]
        lons = [c[1] for c in coordinates]
        
        return (np.mean(lats), np.mean(lons))


# FIXME
class MapView(QWidget):
    """Interactive world map with launch selection and NOTAM visualization"""
    
    launch_selected = pyqtSignal(int)  # Emits launch_id when selected
    site_selected = pyqtSignal(int)    # Emits site_id when clicked (for compatibility)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter = 'next_30'
        self.custom_start = None
        self.custom_end = None
        self.site_markers = {}  # Store site_id -> marker mapping
        self.site_labels = {}   # Store site_id -> label mapping
        self.selected_launch = None  # Currently selected launch
        self.notam_polygons = []  # Store NOTAM polygon patches
        self.notam_paths = []    # Store great circle path lines
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # ===== COMPACT CONTROLS (NO GROUP BOX) =====
        
        # === Single Line: Date Range + Launch Selection + Focus + Checkboxes ===
        main_controls = QHBoxLayout()
        
        # Date Range
        main_controls.addWidget(QLabel("Date Range:"))
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItems([
            "Previous 7 Days",
            "Previous 30 Days",
            "Current (Today)",
            "Next 7 Days",
            "Next 30 Days",
            "Custom Range..."
        ])
        self.date_range_combo.setCurrentIndex(4)  # Default to "Next 30 Days"
        self.date_range_combo.currentIndexChanged.connect(self.on_date_range_changed)
        main_controls.addWidget(self.date_range_combo)
        
        main_controls.addSpacing(20)
        
        # Launch Selection
        main_controls.addWidget(QLabel("Select Launch:"))
        self.launch_combo = QComboBox()
        self.launch_combo.currentIndexChanged.connect(self.on_launch_selected)
        main_controls.addWidget(self.launch_combo)
        
        # Focus Button
        self.focus_btn = QPushButton("🎯 Focus")
        self.focus_btn.clicked.connect(self.focus_on_selected_launch)
        main_controls.addWidget(self.focus_btn)
        
        main_controls.addSpacing(20)
        
        # NOTAM Checkboxes
        self.show_notam_check = QCheckBox("NOTAM Areas")
        self.show_notam_check.setChecked(True)
        self.show_notam_check.stateChanged.connect(self.update_map)
        main_controls.addWidget(self.show_notam_check)
        
        self.show_path_check = QCheckBox("Flight Path")
        self.show_path_check.setChecked(True)
        self.show_path_check.stateChanged.connect(self.update_map)
        main_controls.addWidget(self.show_path_check)
        
        main_controls.addStretch()
        
        layout.addLayout(main_controls)
        
        # === Custom Date Range (hidden by default) ===
        self.custom_range_widget = QWidget()
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        
        custom_layout.addWidget(QLabel("From:"))
        self.custom_start_date = QDateEdit()
        self.custom_start_date.setCalendarPopup(True)
        self.custom_start_date.setDate(QDate.currentDate())
        custom_layout.addWidget(self.custom_start_date)
        
        custom_layout.addWidget(QLabel("To:"))
        self.custom_end_date = QDateEdit()
        self.custom_end_date.setCalendarPopup(True)
        self.custom_end_date.setDate(QDate.currentDate().addDays(30))
        custom_layout.addWidget(self.custom_end_date)
        
        self.apply_custom_btn = QPushButton("Apply")
        self.apply_custom_btn.clicked.connect(self.apply_custom_range)
        custom_layout.addWidget(self.apply_custom_btn)
        custom_layout.addStretch()
        
        self.custom_range_widget.setLayout(custom_layout)
        self.custom_range_widget.setVisible(False)
        layout.addWidget(self.custom_range_widget)
        
        # === Custom NOTAM Entry (Single Line) ===
        notam_layout = QHBoxLayout()
        
        notam_layout.addWidget(QLabel("Custom NOTAM:"))
        
        self.custom_notam_text = QTextEdit()
        self.custom_notam_text.setPlaceholderText("Paste NOTAM text (auto-extracts BOUNDED BY coordinates)")
        self.custom_notam_text.setMaximumHeight(60)
        notam_layout.addWidget(self.custom_notam_text, 1)
        
        self.parse_notam_btn = QPushButton("📍 Parse")
        self.parse_notam_btn.clicked.connect(self.parse_custom_notam)
        notam_layout.addWidget(self.parse_notam_btn)
        
        self.clear_notam_btn = QPushButton("🗑️ Clear")
        self.clear_notam_btn.clicked.connect(self.clear_custom_notam)
        notam_layout.addWidget(self.clear_notam_btn)
        
        layout.addLayout(notam_layout)
        
        # ===== MAP =====
        # No fixed size - let it fill available space dynamically
        self.figure = Figure(facecolor='#0f0f1e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(
            self.canvas.sizePolicy().Policy.Expanding,
            self.canvas.sizePolicy().Policy.Expanding
        )
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)
        
        # Canvas event connections
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_click)
        self.canvas.mpl_connect('scroll_event', self.on_mouse_scroll)  # Mouse wheel zoom
        
        # Status label
        self.status_label = QLabel("Loading map...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Initial map render
        self.update_map()
        self.populate_launch_combo()
    
    def get_date_range(self):
        """Get start and end dates based on current filter"""
        today = datetime.now().date()
        
        if self.current_filter == 'previous_7':
            start = today - timedelta(days=7)
            end = today
        elif self.current_filter == 'previous_30':
            start = today - timedelta(days=30)
            end = today
        elif self.current_filter == 'current':
            start = today
            end = today
        elif self.current_filter == 'next_7':
            start = today
            end = today + timedelta(days=7)
        elif self.current_filter == 'next_30':
            start = today
            end = today + timedelta(days=30)
        elif self.current_filter == 'custom':
            start = self.custom_start
            end = self.custom_end
        else:
            start = today
            end = today + timedelta(days=30)
        
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
    
    def on_date_range_changed(self, index):
        """Handle date range selection change"""
        filters = ['previous_7', 'previous_30', 'current', 'next_7', 'next_30', 'custom']
        self.current_filter = filters[index]
        
        self.custom_range_widget.setVisible(self.current_filter == 'custom')
        
        if self.current_filter != 'custom':
            self.update_map()
            self.populate_launch_combo()
    
    def apply_custom_range(self):
        """Apply custom date range"""
        self.custom_start = self.custom_start_date.date().toPyDate()
        self.custom_end = self.custom_end_date.date().toPyDate()
        self.update_map()
        self.populate_launch_combo()
    
    def populate_launch_combo(self):
        """Populate launch selection dropdown"""
        start_date, end_date = self.get_date_range()
        
        launches = Launch.objects.filter(launch_date__range=(start_date, end_date))

        self.launch_combo.blockSignals(True)
        self.launch_combo.clear()
        self.launch_combo.addItem("-- All Launches --", None)
        
        for launch in launches:
            date = launch.launch_date
            mission = launch.mission_name
            site = launch.site.name
            
            display = f"{date} - {mission} ({site})"
            self.launch_combo.addItem(display, launch.pk)
        
        self.launch_combo.blockSignals(False)
    
    def on_launch_selected(self, index):
        """Handle launch selection from dropdown"""
        launch_id = self.launch_combo.currentData()
        
        if launch_id is None:
            self.selected_launch = None
        else:
            # Get full launch details
            start_date, end_date = self.get_date_range()
            
            launches = Launch.objects.filter(launch_date__range=(start_date, end_date))
            
            self.selected_launch = next((l for l in launches if l.pk == launch_id), None)
        
        self.update_map()
        
        # Don't auto-focus - let user click Focus button to zoom
    
    def focus_on_selected_launch(self):
        """Zoom map to selected launch site and NOTAM area, filling entire canvas"""
        if not self.selected_launch:
            return
        
        lat = self.selected_launch.site.latitude
        lon = self.selected_launch.site.longitude
        
        if lat is None or lon is None:
            return
        
        # Get NOTAM coordinates if they exist
        launch_id = self.selected_launch.pk
        notam_coords = self.get_notam_coordinates(launch_id)
        
        # # Also check for custom NOTAM
        # if 'custom_notam' in self.selected_launch:
        #     if notam_coords is None:
        #         notam_coords = []
        #     notam_coords.extend(self.selected_launch['custom_notam'])
        
        # Get canvas aspect ratio (width / height)
        fig_width, fig_height = self.figure.get_size_inches()
        canvas_aspect = fig_width / fig_height
        
        if notam_coords and len(notam_coords) > 0:
            # Calculate bounding box that includes launch site and all NOTAMs
            all_lats = [lat] + [c[0] for c in notam_coords]
            all_lons = [lon] + [c[1] for c in notam_coords]
            
            min_lat = min(all_lats)
            max_lat = max(all_lats)
            min_lon = min(all_lons)
            max_lon = max(all_lons)
            
            # Add padding (30%)
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon
            
            padding_lat = max(lat_range * 0.30, 2.0)
            padding_lon = max(lon_range * 0.30, 2.0)
            
            # Calculate ranges with padding
            padded_lat_range = lat_range + 2*padding_lat
            padded_lon_range = lon_range + 2*padding_lon
            
            # Adjust ranges to match canvas aspect ratio
            # Aspect ratio = lon_range / lat_range
            current_aspect = padded_lon_range / padded_lat_range if padded_lat_range > 0 else 1.0
            
            if current_aspect < canvas_aspect:
                # Too tall, need to widen longitude
                padded_lon_range = padded_lat_range * canvas_aspect
            else:
                # Too wide, need to increase latitude
                padded_lat_range = padded_lon_range / canvas_aspect
            
            # Center the view
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            self.ax.set_extent([
                center_lon - padded_lon_range/2,
                center_lon + padded_lon_range/2,
                center_lat - padded_lat_range/2,
                center_lat + padded_lat_range/2
            ], crs=ccrs.PlateCarree() if CARTOPY_AVAILABLE else None)
        else:
            # No NOTAM - create extent matching canvas aspect ratio
            # Start with ±15 degrees base range
            base_range = 15
            
            lat_range = base_range * 2
            lon_range = lat_range * canvas_aspect
            
            if CARTOPY_AVAILABLE:
                self.ax.set_extent([
                    lon - lon_range/2, 
                    lon + lon_range/2, 
                    lat - lat_range/2, 
                    lat + lat_range/2
                ], crs=ccrs.PlateCarree())
            else:
                self.ax.set_xlim(lon - lon_range/2, lon + lon_range/2)
                self.ax.set_ylim(lat - lat_range/2, lat + lat_range/2)
        
        self.canvas.draw_idle()
    
    def calculate_great_circle_info(self, lat1, lon1, lat2, lon2):
        """
        Calculate great circle distance, azimuth, and inclination between two points
        
        Returns:
            dict with 'distance_km', 'distance_nm', 'azimuth', 'inclination'
        """
        from math import radians, degrees, sin, cos, atan2, sqrt, asin, acos
        
        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        # Haversine formula for distance
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth radius in km
        earth_radius_km = 6371.0
        distance_km = earth_radius_km * c
        distance_nm = distance_km * 0.539957  # Convert to nautical miles
        
        # Calculate azimuth (bearing) from point 1 to point 2
        y = sin(lon2_rad - lon1_rad) * cos(lat2_rad)
        x = cos(lat1_rad) * sin(lat2_rad) - sin(lat1_rad) * cos(lat2_rad) * cos(lon2_rad - lon1_rad)
        azimuth = (degrees(atan2(y, x)) + 360) % 360  # Normalize to 0-360
        
        # Calculate orbital inclination from launch azimuth and latitude
        # Formula: cos(i) = cos(lat) * sin(azimuth)
        # This gives the inclination of the orbit based on the launch trajectory
        azimuth_rad = radians(azimuth)
        
        # The inclination formula accounts for the launch latitude and direction
        cos_inclination = cos(lat1_rad) * sin(azimuth_rad)
        
        # Clamp to [-1, 1] to avoid numerical errors with acos
        cos_inclination = max(-1.0, min(1.0, cos_inclination))
        
        inclination = degrees(acos(cos_inclination))
        
        # Ensure inclination is in the range [0, 180]
        # For retrograde orbits (azimuth > 180), inclination > 90
        if inclination < 0:
            inclination = abs(inclination)
        
        return {
            'distance_km': distance_km,
            'distance_nm': distance_nm,
            'azimuth': azimuth,
            'inclination': inclination
        }
    
    def get_notam_coordinates(self, launch_id): # TODO
        """Get all NOTAM coordinates for a launch"""       
        notam_records = LaunchNotam.objects.filter(launch_id=launch_id)

        all_coords = []
        # for record in notam_records:
        #     notam_text = record[1] if len(record) > 1 else record[0]
        #     coordinates = NotamParser.parse_notam_area(notam_text)
        #     if coordinates:
        #         all_coords.extend(coordinates)
        
        return all_coords if all_coords else None
    
    def parse_custom_notam(self):
        """Parse custom NOTAM text and display on map"""
        notam_text = self.custom_notam_text.toPlainText().strip()
        
        if not notam_text:
            return
        
        # Parse NOTAM coordinates
        coordinates = NotamParser.parse_notam_area(notam_text)
        
        if not coordinates:
            self.status_label.setText("⚠️ Could not parse NOTAM coordinates. Check format.")
            return
        
        # Store as custom NOTAM for the selected launch
        if self.selected_launch:
            self.selected_launch['custom_notam'] = coordinates
            self.update_map()
            self.status_label.setText(f"✅ Custom NOTAM parsed: {len(coordinates)} vertices")
        else:
            self.status_label.setText("⚠️ Select a launch first to associate NOTAM")
    
    def clear_custom_notam(self):
        """Clear custom NOTAM"""
        if self.selected_launch and 'custom_notam' in self.selected_launch: #FIXME
            del self.selected_launch['custom_notam']
        
        self.custom_notam_text.clear()
        self.update_map()
        self.status_label.setText("Custom NOTAM cleared")
    
    def draw_great_circle(self, ax, lon1, lat1, lon2, lat2, color='#ff3838', linewidth=2, alpha=0.8):
        """Draw great circle path between two points"""
        if not CARTOPY_AVAILABLE:
            # Simple straight line fallback
            ax.plot([lon1, lon2], [lat1, lat2], 
                   color=color, linewidth=linewidth, alpha=alpha, 
                   linestyle='-', transform=ccrs.Geodetic())
            return
        
        # Use Geodetic transform for curved path (SOLID LINE)
        ax.plot([lon1, lon2], [lat1, lat2], 
               color=color, linewidth=linewidth, alpha=alpha,
               linestyle='-', transform=ccrs.Geodetic())
    
    def update_map(self):
        """Update the map display"""
        self.figure.clear()
        
        # Calculate canvas aspect ratio for consistent fill
        fig_width, fig_height = self.figure.get_size_inches()
        canvas_aspect = fig_width / fig_height if fig_height > 0 else 2.4
        
        # Get launches for current date range
        start_date, end_date = self.get_date_range()
        launches = Launch.objects.filter(launch_date__range=(start_date, end_date))
        
        # Create map
        if CARTOPY_AVAILABLE:
            self.ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
            # Keep equal aspect for proper geographic proportions
            
            # Dark theme ocean and land
            self.ax.add_feature(cfeature.OCEAN, facecolor='#0f3460', zorder=0)
            self.ax.add_feature(cfeature.LAND, facecolor='#16213e', zorder=1)
            
            # Purple borders and coastlines
            self.ax.add_feature(cfeature.COASTLINE, linewidth=1.0, 
                              edgecolor='#533483', alpha=0.9, zorder=2)
            self.ax.add_feature(cfeature.BORDERS, linewidth=1.2, 
                              edgecolor='#533483', alpha=0.9, zorder=2)
            
            # Gridlines in purple - labels INSIDE the map
            gl = self.ax.gridlines(draw_labels=True, linewidth=0.5, 
                                  color='#533483', alpha=0.5, linestyle='-')
            gl.top_labels = False
            gl.right_labels = False
            gl.left_labels = True
            gl.bottom_labels = True
            gl.xlabel_style = {'color': '#533483', 'size': 9}
            gl.ylabel_style = {'color': '#533483', 'size': 9}
            
            # Move labels inside the plot area
            try:
                gl.xpadding = -5  # Negative = inside
                gl.ypadding = -5  # Negative = inside
            except:
                pass  # Some cartopy versions don't support this
            
            # Force gridlines to update with extent
            try:
                gl.xlocator = plt.MaxNLocator(nbins=6)
                gl.ylocator = plt.MaxNLocator(nbins=6)
            except:
                pass  # Some cartopy versions don't support this
            
            # Set global extent to fill canvas based on aspect ratio
            # Base latitude range: -75 to 75 (150 degrees total)
            lat_range = 150
            # Calculate longitude range to match aspect ratio
            lon_range = lat_range * canvas_aspect
            
            # Cap longitude at 360 degrees (full world)
            lon_range = min(lon_range, 360)
            
            # Center on 0, 0
            self.ax.set_extent([
                -lon_range/2, 
                lon_range/2, 
                -lat_range/2, 
                lat_range/2
            ], crs=ccrs.PlateCarree())
            
        else:
            # Simple matplotlib fallback
            self.ax = self.figure.add_subplot(111)
            
            # Match aspect ratio to canvas using pre-calculated value
            lat_range = 150  # -75 to 75
            lon_range = min(lat_range * canvas_aspect, 360)
            
            self.ax.set_xlim(-lon_range/2, lon_range/2)
            self.ax.set_ylim(-lat_range/2, lat_range/2)
            self.ax.set_facecolor('#0f3460')
            self.ax.set_xlabel('Longitude', color='#533483')
            self.ax.set_ylabel('Latitude', color='#533483')
            self.ax.tick_params(colors='#533483')
            self.ax.grid(True, alpha=0.3, color='#533483', linewidth=0.5)
        
        # Plot launch sites
        site_activity = {}  # site_id -> launch_count
        
        for launch in launches:
            site_id = launch.site.pk
            if site_id:
                site_activity[site_id] = site_activity.get(site_id, 0) + 1
        
        self.site_markers = {}
        self.site_labels = {}
        
        # Get all sites
        all_sites = LaunchSite.objects.all()
        
        for site in all_sites:
            lat = site.latitude
            lon = site.longitude
            site_id = site.pk
            
            if lat is None or lon is None:
                continue
            
            count = site_activity.get(site_id, 0)
            
            # Color based on activity
            if count >= 10:
                color = '#ff3838'  # Red
            elif count >= 5:
                color = '#ff9500'  # Orange
            elif count >= 2:
                color = '#ffdd00'  # Yellow
            elif count >= 1:
                color = '#00ff41'  # Green
            else:
                continue  # Skip inactive sites
            
            # Plot marker
            marker = self.ax.plot(lon, lat, 'o', color=color, markersize=8,
                                 markeredgecolor='white', markeredgewidth=1,
                                 transform=ccrs.PlateCarree() if CARTOPY_AVAILABLE else None,
                                 zorder=10)[0]
            
            self.site_markers[site_id] = marker
            
            # Label (hidden by default)
            location = site.name
            pad = site.launch_pad
            label_text = f"{location}\n{pad}\n({count} launches)"
            
            label = self.ax.text(lon, lat + 0.5, label_text,
                               fontsize=8, color='white',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor='#1a1a2e', 
                                       edgecolor='#533483', 
                                       alpha=0.9),
                               ha='center', va='bottom',
                               transform=ccrs.PlateCarree() if CARTOPY_AVAILABLE else None,
                               zorder=15, visible=False)
            
            self.site_labels[site_id] = label
        
        # Highlight selected launch site
        if self.selected_launch:
            lat = self.selected_launch.site.latitude
            lon = self.selected_launch.site.longitude
            
            if lat is not None and lon is not None:
                # Highlight with red circle (filled)
                self.ax.plot(lon, lat, 'o', color='#ff3838', markersize=15,
                           markeredgecolor='white', markeredgewidth=2,
                           transform=ccrs.PlateCarree() if CARTOPY_AVAILABLE else None,
                           zorder=20)
                
                # Show label permanently for selected
                site_id = self.selected_launch.site.pk
                if site_id in self.site_labels:
                    self.site_labels[site_id].set_visible(True)
                
                # Draw NOTAM areas if enabled
                if self.show_notam_check.isChecked():
                    self.draw_notam_areas()
        
        self.canvas.draw()
        
        # Use tight layout with minimal padding to maximize map area
        self.figure.tight_layout(pad=0.1)
        
        # Update status
        filter_names = {
            'previous_7': 'Previous 7 Days',
            'previous_30': 'Previous 30 Days',
            'current': 'Current (Today)',
            'next_7': 'Next 7 Days',
            'next_30': 'Next 30 Days',
            'custom': 'Custom Range'
        }
        filter_name = filter_names.get(self.current_filter, 'All')
        
        active_sites = len([s for s in site_activity.values() if s > 0])
        self.status_label.setText(
            f"{len(launches)} launches | {active_sites} active sites | {filter_name}"
        )
    
    def draw_notam_areas(self):
        """Draw NOTAM danger areas for selected launch"""
        if not self.selected_launch:
            return
        
        launch_id = self.selected_launch.pk
        launch_lat = self.selected_launch.site.latitude
        launch_lon = self.selected_launch.site.longitude
        
        if launch_lat is None or launch_lon is None:
            return
        
        # Get NOTAMs for this launch from database       
        notam_records = LaunchNotam.objects.filter(launch_id=launch_id)
        
        # # Parse and draw each NOTAM
        # # TODO implement notam
        # for record in notam_records:
        #     notam_text = record
        #     coordinates = NotamParser.parse_notam_area(notam_text)
            
        #     if coordinates:
        #         self.draw_notam_polygon(coordinates, launch_lat, launch_lon)
        
        # # Draw custom NOTAM if present
        # if 'custom_notam' in self.selected_launch:
        #     coordinates = self.selected_launch['custom_notam']
        #     self.draw_notam_polygon(coordinates, launch_lat, launch_lon, 
        #                            color='#ffdd00', alpha=0.4)
    
    def draw_notam_polygon(self, coordinates, launch_lat, launch_lon, 
                          color='#ff3838', alpha=0.3):
        """Draw a NOTAM danger area polygon and path from launch site"""
        if not coordinates:
            return
        
        # Extract lat/lon arrays
        lats = [c[0] for c in coordinates]
        lons = [c[1] for c in coordinates]
        
        # Close the polygon
        if coordinates[0] != coordinates[-1]:
            lats.append(lats[0])
            lons.append(lons[0])
        
        # Draw polygon
        polygon = MplPolygon(list(zip(lons, lats)), 
                            facecolor=color, edgecolor=color, 
                            alpha=alpha, linewidth=2,
                            transform=ccrs.PlateCarree() if CARTOPY_AVAILABLE else None,
                            zorder=5)
        self.ax.add_patch(polygon)
        self.notam_polygons.append(polygon)
        
        # Calculate center
        center = NotamParser.calculate_polygon_center(coordinates)
        if center and self.show_path_check.isChecked():
            notam_lat, notam_lon = center
            
            # Draw great circle from launch to NOTAM center
            self.draw_great_circle(self.ax, launch_lon, launch_lat, 
                                  notam_lon, notam_lat, 
                                  color=color, linewidth=2, alpha=0.8)
            
            # Calculate trajectory information
            traj_info = self.calculate_great_circle_info(
                launch_lat, launch_lon, notam_lat, notam_lon
            )
            
            # Create info text box
            info_text = (
                f"Distance: {traj_info['distance_km']:.1f} km ({traj_info['distance_nm']:.1f} NM)\n"
                f"Azimuth: {traj_info['azimuth']:.1f}°\n"
                f"Inclination: {traj_info['inclination']:.1f}°"
            )
            
            # Position the text box in the upper left corner of the map
            # Use axes coordinates (0-1 range) so it stays in same place regardless of zoom
            self.ax.text(0.02, 0.98, info_text,
                        transform=self.ax.transAxes,  # Use axes coordinates, not data coordinates
                        fontsize=10,
                        color='white',
                        verticalalignment='top',
                        horizontalalignment='left',
                        bbox=dict(boxstyle='round,pad=0.5',
                                facecolor='#1a1a2e',
                                edgecolor='#533483',
                                alpha=0.9,
                                linewidth=1.5),
                        zorder=100)  # High zorder to appear on top
    
    def on_mouse_move(self, event):
        """Handle mouse movement for hover effects"""
        if event.inaxes != self.ax:
            return
        
        mouse_lon = event.xdata
        mouse_lat = event.ydata
        
        if mouse_lon is None or mouse_lat is None:
            return
        
        # Check if hovering over a site marker
        hover_found = False
        for site_id, marker in self.site_markers.items():
            marker_data = marker.get_data()
            marker_lon = marker_data[0][0]
            marker_lat = marker_data[1][0]
            
            # Check distance (approximately 3 degrees)
            dist = np.sqrt((mouse_lon - marker_lon)**2 + (mouse_lat - marker_lat)**2)
            
            if dist < 3.0:
                # Show label for this site
                if site_id in self.site_labels:
                    self.site_labels[site_id].set_visible(True)
                    hover_found = True
            else:
                # Hide label (unless it's the selected launch)
                if self.selected_launch and site_id == self.selected_launch.site.pk:
                    continue  # Keep selected visible
                if site_id in self.site_labels:
                    self.site_labels[site_id].set_visible(False)
        
        if hover_found:
            self.canvas.draw_idle()
    
    def on_mouse_scroll(self, event):
        """Handle mouse wheel scroll for zoom"""
        if event.inaxes != self.ax:
            return
        
        # Get current extent
        if CARTOPY_AVAILABLE:
            x_lim = self.ax.get_xlim()
            y_lim = self.ax.get_ylim()
        else:
            x_lim = self.ax.get_xlim()
            y_lim = self.ax.get_ylim()
        
        # Calculate center and ranges
        x_center = (x_lim[0] + x_lim[1]) / 2
        y_center = (y_lim[0] + y_lim[1]) / 2
        x_range = x_lim[1] - x_lim[0]
        y_range = y_lim[1] - y_lim[0]
        
        # Zoom factor
        zoom_factor = 0.85 if event.button == 'up' else 1.15  # Scroll up = zoom in
        
        # Calculate new ranges
        new_x_range = x_range * zoom_factor
        new_y_range = y_range * zoom_factor
        
        # Set new extent
        if CARTOPY_AVAILABLE:
            self.ax.set_extent([
                x_center - new_x_range/2,
                x_center + new_x_range/2,
                y_center - new_y_range/2,
                y_center + new_y_range/2
            ], crs=ccrs.PlateCarree())
        else:
            self.ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
            self.ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)
        
        self.canvas.draw_idle()
    
    def on_mouse_click(self, event):
        """Handle mouse clicks on site markers"""
        if event.inaxes != self.ax:
            return
        
        if event.button != 1:  # Only left click
            return
        
        mouse_lon = event.xdata
        mouse_lat = event.ydata
        
        if mouse_lon is None or mouse_lat is None:
            return
        
        # Check if clicked on a site marker
        for site_id, marker in self.site_markers.items():
            marker_data = marker.get_data()
            marker_lon = marker_data[0][0]
            marker_lat = marker_data[1][0]
            
            # Check distance (approximately 2 degrees for click)
            dist = np.sqrt((mouse_lon - marker_lon)**2 + (mouse_lat - marker_lat)**2)
            
            if dist < 2.0:
                # Emit site_selected signal for main_window compatibility
                self.site_selected.emit(site_id)
                return
    
    def refresh(self):
        """Refresh the map view"""
        self.update_map()
        self.populate_launch_combo()
