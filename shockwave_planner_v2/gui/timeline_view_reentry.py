"""
SHOCKWAVE PLANNER v2.0 - Re-entry Timeline View
Gantt-chart style re-entry timeline with grouped landing zones
Properly integrated with reentries table

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                              QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
import calendar

# import data models
from data.db.models.reentry import Reentry
from data.db.models.reentry_site import ReentrySite


class ReentryTimelineView(QWidget):
    """Gantt-chart style timeline showing re-entries across a month"""
    
    reentry_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.show_only_active = True
        self.zone_turnaround_days = 7
        self.expanded_groups = set()  # Track which countries are expanded
        self.initial_load = True  # Track if this is the first load
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        controls = self.create_controls()
        layout.addLayout(controls)
        
        self.timeline_table = QTableWidget()
        self.timeline_table.verticalHeader().setVisible(True)
        self.timeline_table.setShowGrid(True)
        self.timeline_table.cellClicked.connect(self.cell_clicked)
        
        layout.addWidget(self.timeline_table)
        self.setLayout(layout)
        
        self.update_timeline()
    
    def create_controls(self):
        layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀ Previous Month")
        self.prev_btn.clicked.connect(self.previous_month)
        layout.addWidget(self.prev_btn)
        
        self.month_label = QLabel()
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.month_label.setFont(font)
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.month_label, 1)
        
        self.next_btn = QPushButton("Next Month ▶")
        self.next_btn.clicked.connect(self.next_month)
        layout.addWidget(self.next_btn)
        
        layout.addSpacing(20)
        
        self.active_only_cb = QCheckBox("Show only zones with re-entries")
        self.active_only_cb.setChecked(True)
        self.active_only_cb.stateChanged.connect(self.toggle_active_only)
        layout.addWidget(self.active_only_cb)
        
        return layout
    
    # TODO optimise update_timeline
    def update_timeline(self):
        month_name = calendar.month_name[self.current_month]
        self.month_label.setText(f"{month_name} {self.current_year} - Re-entry Operations")
        
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        # Get re-entries for this month
        current_month_reentries = Reentry.objects.filter(reentry_date__year=self.current_year, 
                                              reentry_date__month=self.current_month
                                              )
        
        # Also get re-entries from the end of previous month for turnaround carry-over
        prev_year = self.current_year
        prev_month = self.current_month - 1
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1
        
        prev_month_reentries = Reentry.objects.filter(reentry_date__year=self.current_year, 
                                              reentry_date__month=self.current_month
                                              )
        
        # Group re-entries by zone
        zone_reentries = {(site["site__name"], site['site__drop_zone']):[] for site in current_month_reentries.values("site__name", "site__drop_zone").distinct()}
        zone_prev_reentries = {(site["site__name"], site['site__drop_zone']):[] for site in prev_month_reentries.values("site__name", "site__drop_zone").distinct()}  # Track previous month re-entries for turnaround
        
        for reentry in current_month_reentries:
            key = (reentry.site.name, reentry.site.drop_zone)
            
            if key not in zone_reentries:
                zone_reentries[key] = []
            zone_reentries[key].append(reentry)
        
        for reentry in prev_month_reentries:
            key = (reentry.site.name, reentry.site.drop_zone)
            
            if key not in zone_prev_reentries:
                zone_prev_reentries[key] = []
            zone_prev_reentries[key].append(reentry)
        
        # Get all re-entry sites and group by country
        all_sites = ReentrySite.objects.all()
        country_zones_map = {}
        
        for zone in all_sites:
            country = zone.country
            
            if not country or country == '':
                country = 'Other'
            
            if country not in country_zones_map:
                country_zones_map[country] = []
            
            zone_key = (zone.name, zone.drop_zone)
            has_reentries = zone_key in zone_reentries
            
            if has_reentries or not self.show_only_active:
                country_zones_map[country].append({
                    'type': 'zone',
                    'country': country,
                    'location': zone.name,
                    'drop_zone': zone.drop_zone,
                    'site_id': zone.pk,
                    'turnaround_days': zone.turnaround_days,
                    'reentries': zone_reentries.get(zone_key, []),
                    'prev_month_reentries': zone_prev_reentries.get(zone_key, [])  # For turnaround carry-over
                })
        
        # Build rows for display
        rows = []
        for country in sorted(country_zones_map.keys()):
            zones = country_zones_map[country]
            country_has_reentries = any(z['reentries'] for z in zones)
            
            # FIXED: Only auto-expand countries with re-entries on initial load
            if self.initial_load and country_has_reentries:
                self.expanded_groups.add(country)
            
            if zones and (country_has_reentries or not self.show_only_active):
                rows.append({
                    'type': 'group',
                    'country': country,
                    'expanded': country in self.expanded_groups
                })
                
                if country in self.expanded_groups:
                    rows.extend(zones)
        
        # Mark that initial load is complete
        self.initial_load = False
        
        # Setup table
        self.timeline_table.setRowCount(len(rows))
        self.timeline_table.setColumnCount(3 + days_in_month)
        
        # Clear all spans from previous render
        self.timeline_table.clearSpans()
        
        headers = ['REGION', 'DROP ZONE', 'VEHICLE']
        for day in range(1, days_in_month + 1):
            headers.append(str(day))
        self.timeline_table.setHorizontalHeaderLabels(headers)
        
        self.timeline_table.setColumnWidth(0, 120)
        self.timeline_table.setColumnWidth(1, 120)
        self.timeline_table.setColumnWidth(2, 150)
        
        for col in range(3, 3 + days_in_month):
            self.timeline_table.setColumnWidth(col, 30)
        
        # Populate rows
        for row_idx, row_data in enumerate(rows):
            if row_data['type'] == 'group':
                country = row_data['country']
                expanded = row_data['expanded']
                
                expand_icon = "▼" if expanded else "▶"
                item = QTableWidgetItem(f"{expand_icon} {country}")
                font = item.font()
                font.setBold(True)
                font.setPointSize(10)
                item.setFont(font)
                item.setBackground(QColor(67, 25, 218))
                item.setForeground(Qt.GlobalColor.white)
                item.setData(Qt.ItemDataRole.UserRole, {'type': 'group', 'country': country})
                
                self.timeline_table.setItem(row_idx, 0, item)
                self.timeline_table.setSpan(row_idx, 0, 1, 3 + days_in_month)
                
            else:
                # Location
                location_item = QTableWidgetItem(row_data['location'])
                location_item.setBackground(QColor(240, 240, 245))
                location_item.setForeground(Qt.GlobalColor.black)
                self.timeline_table.setItem(row_idx, 0, location_item)
                
                # Drop zone - show turnaround days
                turnaround = row_data.get('turnaround_days', self.zone_turnaround_days)
                zone_text = f"{row_data['drop_zone']} ({turnaround}d)"
                zone_item = QTableWidgetItem(zone_text)
                zone_item.setBackground(QColor(240, 240, 245))
                zone_item.setForeground(Qt.GlobalColor.black)
                self.timeline_table.setItem(row_idx, 1, zone_item)
                
                # Vehicle components
                components = set()
                for reentry in row_data['reentries']:
                    if reentry.vehicle_component:
                        components.add(reentry.vehicle_component)
                
                vehicle_item = QTableWidgetItem(", ".join(sorted(components)[:2]))
                vehicle_item.setBackground(QColor(240, 240, 245))
                vehicle_item.setForeground(Qt.GlobalColor.black)
                self.timeline_table.setItem(row_idx, 2, vehicle_item)
                
                # Daily cells
                for col_day in range(1, days_in_month + 1):
                    col_idx = 2 + col_day
                    item = QTableWidgetItem("")
                    
                    # Find re-entries on this day
                    day_reentries = [r for r in row_data['reentries'] 
                                    if r.reentry_date.day == col_day]
                    
                    if day_reentries:
                        reentry = day_reentries[0]
                        status_color = reentry.status.colour
                        item.setBackground(QColor(status_color))
                        item.setText(str(len(day_reentries)))
                        item.setData(Qt.ItemDataRole.UserRole, {
                            'type': 'reentry',
                            'reentry_id': reentry.pk,
                            'count': len(day_reentries)
                        })
                    else:
                        # Check for recovery period using zone-specific turnaround
                        in_recovery = False
                        zone_turnaround = row_data['turnaround_days']

                        # Check re-entries in current month
                        for reentry in row_data['reentries']:
                            reentry_day = reentry.reentry_date.day
                            if reentry_day < col_day <= reentry_day + zone_turnaround:
                                in_recovery = True
                                break
                        
                        # Check re-entries from previous month that might extend into current month
                        if not in_recovery and row_data['prev_month_reentries']:
                            prev_year = self.current_year
                            prev_month = self.current_month - 1
                            if prev_month < 1:
                                prev_month = 12
                                prev_year -= 1
                            
                            days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]
                            
                            for prev_reentry in row_data['prev_month_reentries']:
                                prev_reentry_date = prev_reentry.reentry_date
                                prev_reentry_day = prev_reentry_date.day
                                
                                # Calculate how many days into current month the recovery extends
                                days_past_month_end = (prev_reentry_day + zone_turnaround) - days_in_prev_month
                                
                                if days_past_month_end > 0 and col_day <= days_past_month_end:
                                    in_recovery = True
                                    break
                        
                        if in_recovery:
                            item.setBackground(QColor(200, 200, 200))
                        else:
                            item.setBackground(QColor(255, 255, 255))
                    
                    self.timeline_table.setItem(row_idx, col_idx, item)
        
        for row in range(len(rows)):
            self.timeline_table.setRowHeight(row, 30)
    
    def cell_clicked(self, row: int, col: int):
        item = self.timeline_table.item(row, col)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        if data['type'] == 'group':
            country = data['country']
            if country in self.expanded_groups:
                self.expanded_groups.remove(country)
            else:
                self.expanded_groups.add(country)
            self.update_timeline()
        
        elif data['type'] == 'reentry':
            self.reentry_selected.emit(data['reentry_id'])
    
    def previous_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_timeline()
    
    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_timeline()
    
    def toggle_active_only(self, state):
        self.show_only_active = (state == Qt.CheckState.Checked.value)
        self.update_timeline()
