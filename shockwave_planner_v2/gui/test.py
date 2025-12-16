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
import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap
from main_window import MainWindow

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.database import LaunchDatabase
from data.space_devs import SpaceDevsAPI
from timeline_view import TimelineView
from enhanced_list_view import EnhancedListView
from timeline_view_reentry import ReentryTimelineView
from reentry_dialog import ReentryDialog
from launch_sites_view import LaunchSitesView
from drop_zones_view import DropZonesView
from rockets_view import RocketsView
from reentry_vehicles_view import ReentryVehiclesView

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
        self.site_combo.setEditable(True)
        sites = self.db.get_all_sites()
        for site in sites:
            self.site_combo.addItem(f"{site['location']} - {site['launch_pad']}", site['site_id'])
        layout.addRow("Launch Site:", self.site_combo)
        
        # Add Site button
        add_site_btn = QPushButton("Add New Site...")
        add_site_btn.clicked.connect(self.add_new_site)
        layout.addRow("", add_site_btn)
        
        # Rocket
        self.rocket_combo = QComboBox()
        self.rocket_combo.setEditable(True)
        rockets = self.db.get_all_rockets()
        for rocket in rockets:
            self.rocket_combo.addItem(rocket['name'], rocket['rocket_id'])
        layout.addRow("Rocket:", self.rocket_combo)
        
        # Add Rocket button
        add_rocket_btn = QPushButton("Add New Rocket...")
        add_rocket_btn.clicked.connect(self.add_new_rocket)
        layout.addRow("", add_rocket_btn)
        
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
        self.notam_edit = QTableWidget()
        self.notam_edit.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.notam_edit.setColumnCount(4)
        self.notam_edit.setRowCount(1)
        self.notam_edit.setMaximumSize(405,self.notam_edit.rowHeight(0))
        self.notam_edit.verticalHeader().hide()
        self.notam_edit.horizontalHeader().hide()
        layout.addRow("NOTAM Reference:", self.notam_edit)
        self.notam_edit.editTriggers()
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
            
            notam_data = self.db.conn.cursor().execute("""
                                                        SELECT ln.serial 
                                                        FROM launch_notam AS ln 
                                                        WHERE ln.launch_id == ?;
                                                       """, 
                                                       (str(launch['launch_id']),)
                                                       )
            notam_data = [dict(row) for row in notam_data.fetchall()]
            for col in range(len(notam_data)):
                serial = notam_data[col]["serial"]
                self.notam_edit.setItem(0, col, QTableWidgetItem(serial))

            if launch.get('orbit_type'):
                index = self.orbit_combo.findText(launch['orbit_type'])
                if index >= 0:
                    self.orbit_combo.setCurrentIndex(index)
            
            self.remarks_edit.setPlainText(launch.get('remarks') or '')
    
    def add_new_site(self):
        """Open dialog to add a new launch site"""
        from PyQt6.QtWidgets import QDoubleSpinBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Launch Site")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        location_edit = QLineEdit()
        location_edit.setPlaceholderText("e.g., Cape Canaveral, Vandenberg")
        layout.addRow("Location:", location_edit)
        
        pad_edit = QLineEdit()
        pad_edit.setPlaceholderText("e.g., LC-39A, SLC-4E")
        layout.addRow("Launch Pad:", pad_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", country_edit)
        
        lat_spin = QDoubleSpinBox()
        lat_spin.setRange(-90, 90)
        lat_spin.setDecimals(4)
        lat_spin.setSuffix("°")
        layout.addRow("Latitude:", lat_spin)
        
        lon_spin = QDoubleSpinBox()
        lon_spin.setRange(-180, 180)
        lon_spin.setDecimals(4)
        lon_spin.setSuffix("°")
        layout.addRow("Longitude:", lon_spin)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save new site
            site_data = {
                'location': location_edit.text(),
                'launch_pad': pad_edit.text(),
                'country': country_edit.text(),
                'latitude': lat_spin.value() if lat_spin.value() != 0 else None,
                'longitude': lon_spin.value() if lon_spin.value() != 0 else None,
                'site_type': 'LAUNCH'
            }
            
            try:
                site_id = self.db.add_site(site_data)
                
                # Add to combo box
                display = f"{site_data['location']} - {site_data['launch_pad']}"
                self.site_combo.addItem(display, site_id)
                self.site_combo.setCurrentIndex(self.site_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Launch site added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add site: {e}")
    
    def add_new_rocket(self):
        """Open dialog to add a new rocket"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Rocket")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g., Falcon 9 Block 5, Long March 2D")
        layout.addRow("Rocket Name:", name_edit)
        
        family_edit = QLineEdit()
        family_edit.setPlaceholderText("e.g., Falcon, Long March")
        layout.addRow("Family (optional):", family_edit)
        
        variant_edit = QLineEdit()
        variant_edit.setPlaceholderText("e.g., Block 5, CZ-2D")
        layout.addRow("Variant (optional):", variant_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country (optional):", country_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rocket_name = name_edit.text().strip()
            
            if not rocket_name:
                QMessageBox.warning(self, "Validation Error", "Please enter a rocket name.")
                return
            
            # Save new rocket
            rocket_data = {
                'name': rocket_name,
                'family': family_edit.text().strip() or None,
                'variant': variant_edit.text().strip() or None,
                'country': country_edit.text().strip() or None
            }
            
            try:
                rocket_id = self.db.add_rocket(rocket_data)
                
                # Add to combo box
                self.rocket_combo.addItem(rocket_name, rocket_id)
                self.rocket_combo.setCurrentIndex(self.rocket_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Rocket added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add rocket: {e}")
    
    def save_launch(self):
        """Save launch data"""
        
        # Get site_id (if selected from dropdown)
        site_id = self.site_combo.currentData()
        
        # If site was typed in manually, create it
        if site_id is None and self.site_combo.currentText().strip():
            site_text = self.site_combo.currentText().strip()
            # Quick site creation - parse "Location - Pad" format
            parts = site_text.split('-', 1)
            location = parts[0].strip() if parts else site_text
            pad = parts[1].strip() if len(parts) > 1 else "Main Pad"
            
            site_data = {
                'location': location,
                'launch_pad': pad,
                'country': None,
                'latitude': None,
                'longitude': None,
                'site_type': 'LAUNCH'
            }
            
            try:
                site_id = self.db.add_site(site_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create site: {e}")
                return
        
        # Get rocket_id (if selected from dropdown)
        rocket_id = self.rocket_combo.currentData()
        
        # If rocket was typed in manually, create it
        if rocket_id is None and self.rocket_combo.currentText().strip():
            rocket_name = self.rocket_combo.currentText().strip()
            
            rocket_data = {
                'name': rocket_name,
                'family': None,
                'variant': None,
                'country': None
            }
            
            try:
                rocket_id = self.db.add_rocket(rocket_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create rocket: {e}")
                return
        
        # Validate we have required data
        if not site_id:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a launch site.")
            return
        
        if not rocket_id:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a rocket.")
            return
        
        launch_data = {
            'launch_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'launch_time': self.time_edit.time().toString('HH:mm:ss'),
            'site_id': site_id,
            'rocket_id': rocket_id,
            'mission_name': self.mission_edit.text(),
            'payload_name': self.payload_edit.text(),
            'orbit_type': self.orbit_combo.currentText(),
            'status_id': self.status_combo.currentData(),
            'notam_reference': None,
            'remarks': self.remarks_edit.toPlainText(),
            'data_source': 'MANUAL'
        }

        # NOTAM data
        notam_data = [self.notam_edit.item(0, col).data(0) for col in range(self.notam_edit.columnCount())]
        
        try:
            if self.launch_id:
                self.db.update_launch(self.launch_id, launch_data)
                self.db.conn.cursor().execute("""
                                                UPDATE launch_notam  
                                            """
                                             )

                                            
                
                QMessageBox.information(self, "Success", "Launch updated successfully!")
            else:
                self.db.add_launch(launch_data)
                QMessageBox.information(self, "Success", "Launch added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save launch: {e}")


QApplication.setHighDpiScaleFactorRoundingPolicy(

        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
 
app = QApplication(sys.argv)
window = QMainWindow()

db = LaunchDatabase()

test = LaunchEditorDialog(db, launch_id=1)
test.show()
sys.exit(app.exec())