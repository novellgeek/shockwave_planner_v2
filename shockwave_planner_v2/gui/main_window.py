"""
SHOCKWAVE PLANNER v2.0 - Main Window
Enhanced with Space Devs Integration, Re-entry Tracking, and Timeline Views

Author: Remix Astronautics
Date: December 2025
Version: 2.0.0
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QTabWidget, QGroupBox,
                              QDialog, QFormLayout, QDialogButtonBox, QLineEdit,
                              QComboBox, QDateEdit, QTimeEdit, QTextEdit,
                              QMessageBox, QProgressDialog, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from datetime import datetime
import sys
import os

from data.space_devs import SpaceDevsClient
from data.space_devs_worker import SyncWorker

# import GUI elements
from gui.enhanced_list_view import EnhancedListView
from gui.timeline_view import TimelineView
from gui.timeline_view_reentry import ReentryTimelineView
from gui.map_view import MapView
from gui.statistics_view import StatisticsView
from gui.launch_sites_view import LaunchSitesView
from gui.drop_zones_view import DropZonesView
from gui.rockets_view import RocketsView
from gui.reentry_vehicles_view import ReentryVehiclesView
from gui.reentry_dialog import ReentryDialog

class MainWindow(QMainWindow):
    """Main application window for SHOCKWAVE PLANNER v2.0"""
    
    def __init__(self):
        super().__init__()
        self.sync_worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("SHOCKWAVE PLANNER v2.0 - Launch Operations Planning System")
        self.setGeometry(100, 100, 1600, 900)
        
        # Menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_launch_action = QAction('New Launch', self)
        new_launch_action.setShortcut('Ctrl+N')
        # new_launch_action.triggered.connect(self.new_launch) TODO
        file_menu.addAction(new_launch_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        refresh_action = QAction('Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # Data menu
        data_menu = menubar.addMenu('Data')
        
        sync_upcoming_action = QAction('Sync Upcoming Launches (Space Devs)', self)
        sync_upcoming_action.triggered.connect(self.sync_upcoming_launches)
        data_menu.addAction(sync_upcoming_action)
        
        sync_previous_action = QAction('Sync Previous Launches (Space Devs)', self)
        # sync_previous_action.triggered.connect(self.sync_previous_launches) TODO
        data_menu.addAction(sync_previous_action)
        
        data_menu.addSeparator()
        
        sync_rockets_action = QAction('Sync Rocket Details (Space Devs)', self)
        # sync_rockets_action.triggered.connect(self.sync_rocket_details) TODO
        data_menu.addAction(sync_rockets_action)
        
        data_menu.addSeparator()
        
        sync_history_action = QAction('View Sync History', self)
        sync_history_action.triggered.connect(self.show_sync_history)
        data_menu.addAction(sync_history_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
       # Master Activity Schedule - Launch
        self.timeline_view = TimelineView()
        # self.timeline_view.launch_selected.connect(self.edit_launch) TODO
        self.tab_widget.addTab(self.timeline_view, "Master Activity Schedule - Launch")
        
        # Master Activity Schedule - Re-entry 
        self.reentry_timeline_view = ReentryTimelineView()
        self.reentry_timeline_view.reentry_selected.connect(self.edit_reentry)
        self.tab_widget.addTab(self.reentry_timeline_view, "Master Activity Schedule - Re-entry")
        
        # Enhanced List view
        self.list_view = EnhancedListView()
        # self.list_view.launch_selected.connect(self.edit_launch) TODO
        self.tab_widget.addTab(self.list_view, "Launch List View")
        
        # # Launch Site Map view TODO
        self.map_view = MapView()
        # self.map_view.site_selected.connect(self.show_site_launches)
        self.tab_widget.addTab(self.map_view, "Launch Site Map")
        
        # # Statistics view
        self.statistics_view = StatisticsView()
        self.tab_widget.addTab(self.statistics_view, "Launch Statistics")
        
        # # Launch Sites view
        self.sites_view = LaunchSitesView(parent=self)
        self.tab_widget.addTab(self.sites_view, "Launch Sites")
        
        # Drop Zones view
        self.drop_zones_view = DropZonesView(parent=self)
        self.tab_widget.addTab(self.drop_zones_view, "Drop Zones")
        
        # Rockets view
        self.rockets_view = RocketsView(parent=self)
        self.tab_widget.addTab(self.rockets_view, "Launch Vehicles")
        
        # # Re-entry vehicle view
        # self.reentry_vehicles_tab = ReentryVehiclesView()
        # self.tab_widget.addTab(self.reentry_vehicles_tab, "Re-entry Vehicles")
        
        main_layout.addWidget(self.tab_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("+ New Launch") #TODO
        # new_btn.clicked.connect(self.new_launch)
        button_layout.addWidget(new_btn)
        
        new_reentry_btn = QPushButton("+ New Re-entry")
        new_reentry_btn.clicked.connect(self.new_reentry)
        button_layout.addWidget(new_reentry_btn)
        
        sync_btn = QPushButton("🔄 Sync Space Devs") #TODO
        # sync_btn.clicked.connect(self.sync_upcoming_launches)
        button_layout.addWidget(sync_btn)
        
        refresh_btn = QPushButton("♻️ Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        
        # Version label
        version_label = QLabel("v2.0.0")
        version_label.setStyleSheet("color: gray; font-weight: bold;")
        button_layout.addWidget(version_label)
        
        main_layout.addLayout(button_layout)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready - SHOCKWAVE PLANNER v2.0")
    
    # def new_launch(self): TODO
    #     """Create new launch"""
    #     dialog = LaunchEditorDialog(parent=self)
    #     if dialog.exec() == QDialog.DialogCode.Accepted:
    #         self.refresh_all()
    #         self.statusBar().showMessage("Launch added successfully", 3000)
    
    def new_reentry(self):
        """Create new re-entry"""
        dialog = ReentryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Re-entry added successfully", 3000)
    
    # def edit_launch(self, launch_id: int): TODO
    #     """Edit existing launch"""
    #     dialog = LaunchEditorDialog(launch_id, parent=self)
    #     if dialog.exec() == QDialog.DialogCode.Accepted:
    #         self.refresh_all()
    #         self.statusBar().showMessage("Launch updated successfully", 3000)
    
    def edit_reentry(self, reentry_id: int):
        """Edit existing re-entry"""
        dialog = ReentryDialog(parent=self, reentry_id=reentry_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Re-entry updated successfully", 3000)
    
    def sync_upcoming_launches(self):
        """Sync upcoming launches from Space Devs"""
        reply = QMessageBox.question(
            self,
            'Sync Upcoming Launches',
            'Fetch upcoming launches from The Space Devs API?\n\n'
            'This will download up to 100 upcoming launches and merge them with existing data.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_sync('upcoming', 100)
    
    def sync_previous_launches(self): #TODO
        """Sync previous launches from Space Devs"""
        reply = QMessageBox.question(
            self,
            'Sync Previous Launches',
            'Fetch previous launches from The Space Devs API?\n\n'
            'This will download up to 50 recent previous launches for historical data.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_sync('previous', 50)
    
    # def sync_rocket_details(self): TODO
    #     """Sync rocket details from Space Devs"""
    #     rockets_count = len(self.db.get_all_rockets())
        
    #     reply = QMessageBox.question(
    #         self,
    #         'Sync Rocket Details',
    #         f'Update rocket details from The Space Devs API?\n\n'
    #         f'This will fetch family, variant, manufacturer, and country\n'
    #         f'for {rockets_count} rockets in your database.\n\n'
    #         f'Note: Only rockets synced from Space Devs can be updated.',
    #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    #     )
        
    #     if reply == QMessageBox.StandardButton.Yes:
    #         self.start_sync('rockets', 0)
    
    def start_sync(self, sync_type: str, limit: int):
        """Start background sync"""
        self.sync_worker = SyncWorker(sync_type=sync_type, limit=limit)
        self.sync_worker.finished.connect(self.sync_finished)
        self.sync_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        
        self.statusBar().showMessage(f"Syncing {sync_type} launches...")
        self.sync_worker.start()
    
    def sync_finished(self, result: dict):
        """Handle sync completion"""
        self.refresh_all()
        
        message = f"Sync Complete!\n\n"
        
        # Handle different sync types
        if 'added' in result:
            message += f"Added: {result['added']}\n"
        if 'updated' in result:
            message += f"Updated: {result['updated']}\n"
        
        if result.get('errors'):
            message += f"\nErrors: {len(result['errors'])}"
            QMessageBox.warning(self, "Sync Complete (with errors)", message)
        else:
            QMessageBox.information(self, "Sync Complete", message)
        
        # Status bar message
        if 'added' in result and 'updated' in result:
            self.statusBar().showMessage(f"Sync complete: {result['added']} added, {result['updated']} updated", 5000)
        elif 'updated' in result:
            self.statusBar().showMessage(f"Sync complete: {result['updated']} updated", 5000)
        else:
            self.statusBar().showMessage("Sync complete", 5000)
    
    def show_sync_history(self):
        """Show sync history"""
        QMessageBox.information(
            self,
            "Sync History",
            "Sync history viewer coming soon!\n\n"
            "For now, check the sync_log table in the database directly."
        )
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About SHOCKWAVE PLANNER",
            "<h2>SHOCKWAVE PLANNER v2.0</h2>"
            "<p><b>Desktop Launch Operations Planning System</b></p>"
            "<p>Created for Remix Astronautics</p>"
            "<p>Built with Python & PyQt6</p>"
            "<br>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Comprehensive launch tracking</li>"
            "<li>Re-entry operations management</li>"
            "<li>Space Devs API integration</li>"
            "<li>Timeline visualization</li>"
            "<li>NOTAM tracking</li>"
            "</ul>"
            "<br>"
            "<p>Author: Remix Astronautics</p>"
            "<p>December 2025</p>"
        )
    
    # def show_site_launches(self, site_id: int): TODO
    #     """Show launches for selected site from map"""
    #     # Get site info
    #     sites = self.db.get_all_sites()
    #     site = next((s for s in sites if s['site_id'] == site_id), None)
        
    #     if not site:
    #         return
        
    #     # Get launches for this site in current map date range
    #     start_date, end_date = self.map_view.get_date_range()
    #     all_launches = self.db.get_launches_by_date_range(start_date, end_date)
    #     site_launches = [l for l in all_launches if l.get('site_id') == site_id]
        
    #     # Show summary dialog
    #     launch_list = "\n".join([
    #         f"• {l.get('launch_date')} - {l.get('mission_name', 'Unknown')}"
    #         for l in site_launches[:10]  # Show first 10
    #     ])
        
    #     more_text = f"\n... and {len(site_launches) - 10} more" if len(site_launches) > 10 else ""
        
    #     QMessageBox.information(
    #         self,
    #         f"{site['location']} - {site['launch_pad']}",
    #         f"<b>{len(site_launches)} launches</b> in selected period:<br><br>"
    #         f"<pre>{launch_list}{more_text}</pre><br>"
    #         f"<i>Tip: Use Launch List View with same date filter for full details</i>"
    #     )
    
    def refresh_all(self):
        """Refresh all views"""
        # Update all pad turnarounds from launch history
        # self.db.update_all_pad_turnarounds_from_history()
        
        self.timeline_view.update_timeline()
        self.reentry_timeline_view.update_timeline()
        self.list_view.refresh()
        self.map_view.refresh()
        self.sites_view.refresh_table()
        self.drop_zones_view.refresh_table()
        self.rockets_view.refresh_table()
        # self.reentry_vehicles_tab.refresh_table()
        self.statistics_view.refresh()
        
        self.statusBar().showMessage("Refreshed", 2000)
    
    def closeEvent(self, event):
        """Handle window close"""
        event.accept()