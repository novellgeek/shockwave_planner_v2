"""
SHOCKWAVE PLANNER v2.0 - Statistics View
Launch statistics and analytics overview

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                              QFormLayout, QLabel, QTextEdit, QTableWidget,
                              QTableWidgetItem, QHeaderView)
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
        
        # 5-Year Launch Overview (at the top)
        yearly_stats = self.db.get_yearly_statistics(5)
        
        # Reverse the list so 2025 is at the top
        yearly_stats.reverse()
        
        overview_group = QGroupBox("Launch Statistics - Past 5 Years")
        overview_layout = QVBoxLayout()
        
        # Create table for yearly statistics
        year_table = QTableWidget()
        year_table.setRowCount(len(yearly_stats))
        year_table.setColumnCount(6)
        year_table.setHorizontalHeaderLabels([
            'Year', 'Total', 'Successful', 'Failed', 'Pending', 'Success Rate'
        ])
        year_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        year_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        year_table.setMaximumHeight(200)
        
        for row, year_data in enumerate(yearly_stats):
            # Center-aligned items
            def create_centered_item(text):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item
            
            year_table.setItem(row, 0, create_centered_item(year_data['year']))
            year_table.setItem(row, 1, create_centered_item(year_data['total']))
            year_table.setItem(row, 2, create_centered_item(year_data['successful']))
            year_table.setItem(row, 3, create_centered_item(year_data['failed']))
            year_table.setItem(row, 4, create_centered_item(year_data['pending']))
            year_table.setItem(row, 5, create_centered_item(f"{year_data['success_rate']:.1f}%"))
        
        overview_layout.addWidget(year_table)
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Get overall statistics for other sections
        stats = self.db.get_statistics()
        
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
        # Delete the old layout properly
        old_layout = self.layout()
        if old_layout:
            # Remove all widgets from layout
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Delete the layout itself
            QWidget().setLayout(old_layout)
        
        # Rebuild the UI with fresh data
        self.init_ui()
