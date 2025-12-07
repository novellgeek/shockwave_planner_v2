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
                              QMessageBox, QProgressDialog)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.database import LaunchDatabase
from data.space_devs import SpaceDevsAPI
from gui.timeline_view import TimelineView
from gui.enhanced_list_view import EnhancedListView
from gui.timeline_view_reentry import ReentryTimelineView


class SyncWorker(QThread):
    """Background worker for Space Devs sync"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, db, sync_type='upcoming', limit=100):
        super().__init__()
        self.db = db
        self.sync_type = sync_type
        self.limit = limit
    
    def run(self):
        try:
            api = SpaceDevsAPI(self.db)
            
            if self.sync_type == 'upcoming':
                self.progress.emit("Fetching upcoming launches...")
                result = api.sync_upcoming_launches(limit=self.limit)
            elif self.sync_type == 'previous':
                self.progress.emit("Fetching previous launches...")
                result = api.sync_previous_launches(limit=self.limit)
            else:
                result = {'added': 0, 'updated': 0, 'errors': []}
            
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({'added': 0, 'updated': 0, 'errors': [str(e)]})


class LaunchEditorDialog(QDialog):
    """Dialog for adding/editing launch records"""
    
    def __init__(self, db: LaunchDatabase, launch_id: int = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.launch_id = launch_id
        self.init_ui()
        
        if launch_id:
            self.load_launch_data()
    
    def init_ui(self):
        self.setWindowTitle("Launch Editor" if not self.launch_id else "Edit Launch")
        self.setMinimumWidth(600)
        
        layout = QFormLayout()
        
        # Date and Time
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("Launch Date:", self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        layout.addRow("Launch Time:", self.time_edit)
        
        # Launch Site
        self.site_combo = QComboBox()
        sites = self.db.get_all_sites()
        for site in sites:
            self.site_combo.addItem(f"{site['location']} - {site['launch_pad']}", site['site_id'])
        layout.addRow("Launch Site:", self.site_combo)
        
        # Rocket
        self.rocket_combo = QComboBox()
        rockets = self.db.get_all_rockets()
        for rocket in rockets:
            self.rocket_combo.addItem(rocket['name'], rocket['rocket_id'])
        layout.addRow("Rocket:", self.rocket_combo)
        
        # Mission Details
        self.mission_edit = QLineEdit()
        layout.addRow("Mission Name:", self.mission_edit)
        
        self.payload_edit = QLineEdit()
        layout.addRow("Payload:", self.payload_edit)
        
        # Orbit
        self.orbit_combo = QComboBox()
        self.orbit_combo.addItems(['LEO', 'SSO', 'GTO', 'GEO', 'MEO', 'HEO', 'Lunar', 'Other'])
        layout.addRow("Orbit Type:", self.orbit_combo)
        
        # NOTAM
        self.notam_edit = QLineEdit()
        self.notam_edit.setPlaceholderText("e.g., A1234/25")
        layout.addRow("NOTAM Reference:", self.notam_edit)
        
        # Status
        self.status_combo = QComboBox()
        statuses = self.db.get_all_statuses()
        for status in statuses:
            self.status_combo.addItem(status['status_name'], status['status_id'])
        layout.addRow("Status:", self.status_combo)
        
        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(100)
        layout.addRow("Remarks:", self.remarks_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_launch)
        button_box.rejected.connect(self.reject)
        
        layout.addRow(button_box)
        self.setLayout(layout)
    
    def load_launch_data(self):
        """Load existing launch data"""
        launches = self.db.get_launches_by_date_range('1900-01-01', '2100-01-01')
        launch = next((l for l in launches if l['launch_id'] == self.launch_id), None)
        
        if launch:
            if launch['launch_date']:
                date_obj = datetime.strptime(launch['launch_date'], '%Y-%m-%d')
                self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            
            if launch['launch_time']:
                time_obj = datetime.strptime(launch['launch_time'], '%H:%M:%S').time()
                self.time_edit.setTime(QTime(time_obj.hour, time_obj.minute, time_obj.second))
            
            if launch['site_id']:
                index = self.site_combo.findData(launch['site_id'])
                if index >= 0:
                    self.site_combo.setCurrentIndex(index)
            
            if launch['rocket_id']:
                index = self.rocket_combo.findData(launch['rocket_id'])
                if index >= 0:
                    self.rocket_combo.setCurrentIndex(index)
            
            if launch['status_id']:
                index = self.status_combo.findData(launch['status_id'])
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
            
            self.mission_edit.setText(launch.get('mission_name') or '')
            self.payload_edit.setText(launch.get('payload_name') or '')
            self.notam_edit.setText(launch.get('notam_reference') or '')
            
            if launch.get('orbit_type'):
                index = self.orbit_combo.findText(launch['orbit_type'])
                if index >= 0:
                    self.orbit_combo.setCurrentIndex(index)
            
            self.remarks_edit.setPlainText(launch.get('remarks') or '')
    
    def save_launch(self):
        """Save launch data"""
        launch_data = {
            'launch_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'launch_time': self.time_edit.time().toString('HH:mm:ss'),
            'site_id': self.site_combo.currentData(),
            'rocket_id': self.rocket_combo.currentData(),
            'mission_name': self.mission_edit.text(),
            'payload_name': self.payload_edit.text(),
            'orbit_type': self.orbit_combo.currentText(),
            'status_id': self.status_combo.currentData(),
            'notam_reference': self.notam_edit.text(),
            'remarks': self.remarks_edit.toPlainText()
        }
        
        if self.launch_id:
            self.db.update_launch(self.launch_id, launch_data)
        else:
            self.db.add_launch(launch_data)
        
        self.accept()


class MainWindow(QMainWindow):
    """Main application window for SHOCKWAVE PLANNER v2.0"""
    
    def __init__(self):
        super().__init__()
        self.db = LaunchDatabase()
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
        new_launch_action.triggered.connect(self.new_launch)
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
        sync_previous_action.triggered.connect(self.sync_previous_launches)
        data_menu.addAction(sync_previous_action)
        
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
        self.timeline_view = TimelineView(self.db)
        self.timeline_view.launch_selected.connect(self.edit_launch)
        self.tab_widget.addTab(self.timeline_view, "ðŸš€ Master Activity Schedule - Launch")
        
        # Master Activity Schedule - Re-entry  
        self.reentry_timeline_view = ReentryTimelineView(self.db)
        self.reentry_timeline_view.reentry_selected.connect(self.edit_reentry)
        self.tab_widget.addTab(self.reentry_timeline_view, "ðŸ›¬ Master Activity Schedule - Re-entry")
        
        # Enhanced List view
        self.list_view = EnhancedListView(self.db)
        self.list_view.launch_selected.connect(self.edit_launch)
        self.tab_widget.addTab(self.list_view, "📋 Launch List View")
        
        # Statistics view
        stats_widget = self.create_statistics_widget()
        self.tab_widget.addTab(stats_widget, "📊 Statistics")
        
        main_layout.addWidget(self.tab_widget)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        new_btn = QPushButton("âž• New Launch")
        new_btn.clicked.connect(self.new_launch)
        button_layout.addWidget(new_btn)
        
        sync_btn = QPushButton("🔄 Sync Space Devs")
        sync_btn.clicked.connect(self.sync_upcoming_launches)
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
    
    def create_statistics_widget(self):
        """Create statistics display"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        stats = self.db.get_statistics()
        
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
        
        # Sync status
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
        widget.setLayout(layout)
        
        return widget
    
    def new_launch(self):
        """Create new launch"""
        dialog = LaunchEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Launch added successfully", 3000)
    
    def edit_launch(self, launch_id: int):
        """Edit existing launch"""
        dialog = LaunchEditorDialog(self.db, launch_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all()
            self.statusBar().showMessage("Launch updated successfully", 3000)
    
    def edit_reentry(self, reentry_id: int):
        """Edit re-entry (placeholder for future implementation)"""
        QMessageBox.information(
            self,
            "Re-entry Editor",
            f"Re-entry editor coming soon!\n\nRe-entry ID: {reentry_id}\n\n"
            "For now, re-entries can be managed through the database directly."
        )
    
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
    
    def sync_previous_launches(self):
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
    
    def start_sync(self, sync_type: str, limit: int):
        """Start background sync"""
        self.sync_worker = SyncWorker(self.db, sync_type, limit)
        self.sync_worker.finished.connect(self.sync_finished)
        self.sync_worker.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        
        self.statusBar().showMessage(f"Syncing {sync_type} launches...")
        self.sync_worker.start()
    
    def sync_finished(self, result: dict):
        """Handle sync completion"""
        self.refresh_all()
        
        message = f"Sync Complete!\n\n"
        message += f"Added: {result['added']}\n"
        message += f"Updated: {result['updated']}\n"
        
        if result.get('errors'):
            message += f"\nErrors: {len(result['errors'])}"
            QMessageBox.warning(self, "Sync Complete (with errors)", message)
        else:
            QMessageBox.information(self, "Sync Complete", message)
        
        self.statusBar().showMessage(f"Sync complete: {result['added']} added, {result['updated']} updated", 5000)
    
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
            "<p>Created for NZDF 62SQN Space Operations Centre</p>"
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
    
    def refresh_all(self):
        """Refresh all views"""
        self.timeline_view.update_timeline()
        self.reentry_timeline_view.update_timeline()
        self.list_view.refresh()
        
        # Recreate statistics tab
        stats_widget = self.create_statistics_widget()
        self.tab_widget.removeTab(3)
        self.tab_widget.insertTab(3, stats_widget, "📊 Statistics")
        
        self.statusBar().showMessage("Refreshed", 2000)
    
    def closeEvent(self, event):
        """Handle window close"""
        self.db.close()
        event.accept()
