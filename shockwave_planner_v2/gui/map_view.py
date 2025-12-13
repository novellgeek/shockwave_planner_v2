"""
SHOCKWAVE PLANNER v2.1 - Launch Site Map View
Interactive 2D world map showing active launch sites

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                              QLabel, QComboBox, QPushButton, QDateEdit)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    print("Warning: cartopy not available, using simple matplotlib map")

from datetime import datetime, timedelta


class MapView(QWidget):
    """Interactive world map showing launch sites with activity filtering"""
    
    site_selected = pyqtSignal(int)  # Emits site_id when clicked
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_filter = 'next_30'
        self.custom_start = None
        self.custom_end = None
        self.site_markers = {}  # Store site_id -> marker mapping
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # ===== FILTERS (match Launch List View) =====
        filter_group = QGroupBox("Date Range Filter")
        filter_layout = QVBoxLayout()
        
        # Date range selector
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("Show sites active in:"))
        
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
        date_range_layout.addWidget(self.date_range_combo)
        date_range_layout.addStretch()
        
        filter_layout.addLayout(date_range_layout)
        
        # Custom range inputs (hidden by default)
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
        
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_custom_range)
        custom_layout.addWidget(apply_btn)
        custom_layout.addStretch()
        
        self.custom_range_widget.setLayout(custom_layout)
        self.custom_range_widget.setVisible(False)
        filter_layout.addWidget(self.custom_range_widget)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # ===== MAP CANVAS =====
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)  # Hover detection
        
        # Add matplotlib navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # ===== STATUS BAR =====
        self.status_label = QLabel("Loading map...")
        self.status_label.setStyleSheet("font-style: italic; color: #cccccc; background-color: #1a1a2e; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Initial map render
        self.update_map()
    
    def get_date_range(self):
        """Get start and end dates based on current filter (matches enhanced_list_view.py)"""
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
        
        # Show/hide custom range inputs
        self.custom_range_widget.setVisible(self.current_filter == 'custom')
        
        if self.current_filter != 'custom':
            self.update_map()
    
    def apply_custom_range(self):
        """Apply custom date range filter"""
        self.custom_start = self.custom_start_date.date().toPyDate()
        self.custom_end = self.custom_end_date.date().toPyDate()
        self.update_map()
    
    def update_map(self):
        """Render the world map with active launch sites"""
        self.figure.clear()
        
        if CARTOPY_AVAILABLE:
            self._render_cartopy_map()
        else:
            self._render_simple_map()
        
        self.canvas.draw()
    
    def _render_cartopy_map(self):
        """Render map using cartopy (with coastlines and features)"""
        # Create map projection (PlateCarree = simple lat/lon)
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Dark theme colors
        ax.set_facecolor('#1a1a2e')  # Dark blue-gray ocean
        self.figure.patch.set_facecolor('#0f0f1e')  # Darker background
        
        # Add map features with dark theme
        ax.add_feature(cfeature.LAND, facecolor='#16213e', edgecolor='none')  # Dark land
        ax.add_feature(cfeature.OCEAN, facecolor='#0f3460', edgecolor='none')  # Dark ocean
        ax.add_feature(cfeature.COASTLINE, linewidth=1.0, edgecolor='#533483', alpha=0.9)  # Purple coastline
        ax.add_feature(cfeature.BORDERS, linewidth=1.2, linestyle='-', edgecolor='#533483', alpha=0.9)  # Purple borders
        
        # Grid and labels with purple color matching borders
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.3, color='#808080')
        gl.xlabel_style = {'color': '#533483', 'size': 10}
        gl.ylabel_style = {'color': '#533483', 'size': 10}
        
        # Set global extent
        ax.set_extent([-180, 180, -60, 75], crs=ccrs.PlateCarree())
        
        # Plot sites
        self._plot_launch_sites(ax, transform=ccrs.PlateCarree())
        
        # Dark theme title
        # No title - clean look
        self.figure.tight_layout()
    
    def _render_simple_map(self):
        """Render simple map without cartopy (fallback)"""
        ax = self.figure.add_subplot(111)
        
        # Dark theme
        ax.set_facecolor('#0f3460')  # Dark ocean
        self.figure.patch.set_facecolor('#0f0f1e')  # Darker background
        
        # Simple world outline
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xlabel('Longitude', color='#533483')
        ax.set_ylabel('Latitude', color='#533483')
        ax.grid(True, alpha=0.3, color='#808080')
        
        # Purple tick labels to match borders
        ax.tick_params(colors='#533483')
        
        # Plot sites
        self._plot_launch_sites(ax, transform=None)
        
        # Dark theme title
        # No title - clean look
        ax.set_aspect('equal')
        self.figure.tight_layout()
    
    def _plot_launch_sites(self, ax, transform=None):
        """Plot launch sites on the given axes"""
        # Get active launch sites in current date range
        start_date, end_date = self.get_date_range()
        launches = self.db.get_launches_by_date_range(start_date, end_date)
        
        # Count launches per site
        site_activity = {}  # site_id -> launch_count
        site_coords = {}    # site_id -> (lat, lon, location, pad)
        
        for launch in launches:
            site_id = launch.get('site_id')
            if not site_id:
                continue
            
            # Increment launch count
            site_activity[site_id] = site_activity.get(site_id, 0) + 1
            
            # Store coordinates (first occurrence)
            if site_id not in site_coords:
                lat = launch.get('latitude')
                lon = launch.get('longitude')
                if lat and lon:
                    site_coords[site_id] = (
                        lat, lon, 
                        launch.get('location', 'Unknown'),
                        launch.get('launch_pad', '')
                    )
        
        # Plot sites with color based on activity level
        self.site_markers.clear()
        self.site_annotations = {}  # Store annotations for hover
        
        for site_id, (lat, lon, location, pad) in site_coords.items():
            launch_count = site_activity[site_id]
            
            # Color code by activity - bright colors for dark theme
            # ALL markers same size (70)
            if launch_count >= 10:
                color = '#ff3838'  # Bright red
                label = '10+ launches'
            elif launch_count >= 5:
                color = '#ff9500'  # Bright orange
                label = '5-9 launches'
            elif launch_count >= 2:
                color = '#ffdd00'  # Bright yellow
                label = '2-4 launches'
            else:
                color = '#00ff41'  # Bright green
                label = '1 launch'
            
            # Plot marker - consistent size for all
            plot_kwargs = {
                's': 70,  # Same size for all markers
                'c': color,
                'edgecolors': 'white',  # White border for dark theme
                'linewidths': 1.5,
                'alpha': 0.9,
                'zorder': 5,
                'picker': True
            }
            
            if transform:
                plot_kwargs['transform'] = transform
            
            marker = ax.scatter(lon, lat, **plot_kwargs)
            
            # Create annotation (hidden by default, shown on hover)
            text_kwargs = {
                'fontsize': 9,
                'ha': 'center',
                'color': 'white',
                'weight': 'bold',
                'bbox': dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', 
                           edgecolor='#533483', alpha=0.95, linewidth=1.5),
                'visible': False,  # Hidden by default
                'zorder': 10
            }
            
            if transform:
                text_kwargs['transform'] = transform
            
            annotation = ax.annotate(
                f"{location}\n{pad}\n({launch_count} launches)",
                xy=(lon, lat),
                xytext=(0, 15),  # Offset above marker
                textcoords='offset points',
                **text_kwargs
            )
            
            # Store for hover detection
            self.site_markers[site_id] = (lon, lat, location, pad, launch_count)
            self.site_annotations[site_id] = annotation
        
        # Add legend with dark theme
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff3838', 
                   markersize=7, label='10+ launches', markeredgecolor='white', markeredgewidth=1.0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff9500', 
                   markersize=7, label='5-9 launches', markeredgecolor='white', markeredgewidth=1.0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ffdd00', 
                   markersize=7, label='2-4 launches', markeredgecolor='white', markeredgewidth=1.0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#00ff41', 
                   markersize=7, label='1 launch', markeredgecolor='white', markeredgewidth=1.0),
        ]
        legend = ax.legend(handles=legend_elements, loc='lower left', fontsize=9,
                          facecolor='#1a1a2e', edgecolor='#533483', 
                          labelcolor='white', framealpha=0.9)
        
        # Update status
        filter_names = {
            'previous_7': 'Previous 7 Days',
            'previous_30': 'Previous 30 Days',
            'current': 'Current (Today)',
            'next_7': 'Next 7 Days',
            'next_30': 'Next 30 Days',
            'custom': 'Custom Range'
        }
        filter_name = filter_names.get(self.current_filter, 'Unknown')
        self.status_label.setText(
            f"Showing {len(site_coords)} active sites with {len(launches)} launches ({filter_name})"
        )
    
    def on_map_click(self, event):
        """Handle click on map to select launch site"""
        if event.inaxes is None:
            return
        
        # Get click coordinates
        click_lon = event.xdata
        click_lat = event.ydata
        
        if click_lon is None or click_lat is None:
            return
        
        # Find nearest site (within 5 degrees)
        min_distance = 5.0
        selected_site_id = None
        
        for site_id, (lon, lat, location, pad, count) in self.site_markers.items():
            distance = ((lon - click_lon)**2 + (lat - click_lat)**2)**0.5
            if distance < min_distance:
                min_distance = distance
                selected_site_id = site_id
        
        if selected_site_id:
            # Emit signal (can be caught by main_window to show details)
            self.site_selected.emit(selected_site_id)
            
            # Update status
            site_info = self.site_markers[selected_site_id]
            location, pad, count = site_info[2], site_info[3], site_info[4]
            self.status_label.setText(
                f"Selected: {location} - {pad} ({count} launches in this period)"
            )
    
    def on_mouse_move(self, event):
        """Handle mouse movement for hover tooltips"""
        if event.inaxes is None:
            # Mouse left the plot area - hide all annotations
            for annotation in self.site_annotations.values():
                if annotation.get_visible():
                    annotation.set_visible(False)
                    self.canvas.draw_idle()
            return
        
        mouse_lon = event.xdata
        mouse_lat = event.ydata
        
        if mouse_lon is None or mouse_lat is None:
            return
        
        # Find if hovering over any site
        hover_threshold = 3.0  # degrees
        hovered_site_id = None
        min_dist = float('inf')
        
        for site_id, (lon, lat, location, pad, count) in self.site_markers.items():
            dist = ((lon - mouse_lon)**2 + (lat - mouse_lat)**2)**0.5
            
            if dist < hover_threshold and dist < min_dist:
                min_dist = dist
                hovered_site_id = site_id
        
        # Update annotation visibility
        redraw_needed = False
        for site_id, annotation in self.site_annotations.items():
            should_be_visible = (site_id == hovered_site_id)
            if annotation.get_visible() != should_be_visible:
                annotation.set_visible(should_be_visible)
                redraw_needed = True
        
        if redraw_needed:
            self.canvas.draw_idle()
    
    def refresh(self):
        """Refresh the map (called by main window)"""
        self.update_map()
