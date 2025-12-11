"""
SHOCKWAVE PLANNER v2.0 - Statistics View
Launch statistics and analytics overview

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                              QFormLayout, QLabel, QTextEdit)
from PyQt6.QtCore import Qt
from datetime import datetime


class StatisticsView(QWidget):
    """Statistics and analytics view for launch data"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        stats = self.db.get_statistics()
        
        # Launch Overview
        overview_group = QGroupBox("Launch Overview")
        overview_layout = QFormLayout()
        overview_layout.addRow("Total Launches:", QLabel(str(stats['total_launches'])))
        overview_layout.addRow("Successful:", QLabel(str(stats['successful'])))
        overview_layout.addRow("Failed:", QLabel(str(stats['failed'])))
        overview_layout.addRow("Pending:", QLabel(str(stats['pending'])))
        
        success_rate = 0
        if stats['successful'] + stats['failed'] > 0:
            success_rate = (stats['successful'] / (stats['successful'] + stats['failed'])) * 100
        overview_layout.addRow("Success Rate:", QLabel(f"{success_rate:.1f}%"))
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Top 10 Rockets
        rockets_group = QGroupBox("Top 10 Rockets")
        rockets_layout = QVBoxLayout()
        rockets_text = QTextEdit()
        rockets_text.setReadOnly(True)
        rocket_stats = "\n".join([f"{r['name']}: {r['count']} launches" 
                                 for r in stats['by_rocket']])
        rockets_text.setPlainText(rocket_stats if rocket_stats else "No data")
        rockets_layout.addWidget(rockets_text)
        rockets_group.setLayout(rockets_layout)
        layout.addWidget(rockets_group)
        
        # Launches by Site
        sites_group = QGroupBox("Launches by Site")
        sites_layout = QVBoxLayout()
        sites_text = QTextEdit()
        sites_text.setReadOnly(True)
        site_stats = "\n".join([f"{s['location']}: {s['count']} launches" 
                               for s in stats['by_site']])
        sites_text.setPlainText(site_stats if site_stats else "No data")
        sites_layout.addWidget(sites_text)
        sites_group.setLayout(sites_layout)
        layout.addWidget(sites_group)
        
        # Space Devs Sync Status
        last_sync = self.db.get_last_sync('SPACE_DEVS_UPCOMING')
        if last_sync:
            sync_group = QGroupBox("Last Space Devs Sync")
            sync_layout = QFormLayout()
            sync_time = datetime.fromisoformat(last_sync['sync_time']).strftime('%Y-%m-%d %H:%M:%S')
            sync_layout.addRow("Time:", QLabel(sync_time))
            sync_layout.addRow("Added:", QLabel(str(last_sync['records_added'])))
            sync_layout.addRow("Updated:", QLabel(str(last_sync['records_updated'])))
            sync_layout.addRow("Status:", QLabel(last_sync['status']))
            sync_group.setLayout(sync_layout)
            layout.addWidget(sync_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh the statistics display"""
        # Clear the current layout
        while self.layout().count():
            child = self.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Rebuild the UI with fresh data
        self.init_ui()
