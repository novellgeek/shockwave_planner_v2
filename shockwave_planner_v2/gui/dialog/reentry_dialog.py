"""
SHOCKWAVE PLANNER v2.0 - Re-entry Dialog
Manual entry form for re-entry operations

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit,
                             QPushButton, QMessageBox, QLabel, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import QDate, QTime, Qt
from datetime import datetime

# import data models
from data.db.models.launch import Launch
from data.db.models.reentry_site import ReentrySite
from data.db.models.status import Status
from data.db.models.reentry import Reentry

class ReentryDialog(QDialog):
    """Dialog for adding/editing re-entry operations"""
    
    def __init__(self, parent=None, reentry_id=None):
        super().__init__(parent)
        self.reentry_id = reentry_id
        
        self.setWindowTitle("New Re-entry" if not reentry_id else "Edit Re-entry")
        self.setModal(True)
        self.resize(600, 500)
        
        self.init_ui()
        
        if reentry_id:
            self.load_reentry_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Form layout
        form = QFormLayout()
        
        # Launch selection
        self.launch_combo = QComboBox()
        self.launch_combo.addItem("(No associated launch)", None)
        launches = Launch.objects.all()
        for launch in launches:
            launch_date = launch.launch_date
            mission = launch.mission_name
            display = f"{launch_date} - {mission}"
            self.launch_combo.addItem(display, launch.pk)
        form.addRow("Associated Launch:", self.launch_combo)
        
        # Re-entry date and time
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Re-entry Date:", self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(12, 0))
        form.addRow("Re-entry Time (UTC):", self.time_edit)
        
        # Re-entry site
        self.site_combo = QComboBox()
        self.site_combo.setEditable(True)
        # FIXED: Use get_all_reentry_sites() instead of get_all_sites()
        reentry_sites = ReentrySite.objects.all()
        for site in reentry_sites:
            location = site.name
            drop_zone = site.drop_zone
            display = f"{location} - {drop_zone}"
            # FIXED: use 'site_id' which is aliased from reentry_site_id
            self.site_combo.addItem(display, site.pk)
        form.addRow("Re-entry Site:", self.site_combo)
        
        # Add new site button
        add_site_btn = QPushButton("Add New Site...")
        add_site_btn.clicked.connect(self.add_new_site)
        form.addRow("", add_site_btn)
        
        # Vehicle component
        self.component_edit = QLineEdit()
        self.component_edit.setPlaceholderText("e.g., First Stage, Fairing, Upper Stage")
        form.addRow("Vehicle Component:", self.component_edit)
        
        # Re-entry type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Controlled",
            "Uncontrolled",
            "Planned",
            "Debris",
            "Recovery",
            "Ocean Splashdown",
            "Land Recovery"
        ])
        form.addRow("Re-entry Type:", self.type_combo)
        
        # Status
        self.status_combo = QComboBox()
        statuses = Status.objects.all()
        for status in statuses:
            self.status_combo.addItem(
                status.name,
                status.pk
            )
        form.addRow("Status:", self.status_combo)
        
        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("Additional notes, coordinates, recovery details...")
        self.remarks_edit.setMaximumHeight(100)
        form.addRow("Remarks:", self.remarks_edit)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_reentry)
        save_btn.setDefault(True)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def add_new_site(self):
        """Open dialog to add a new re-entry site"""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Re-entry Site")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        location_edit = QLineEdit()
        location_edit.setPlaceholderText("e.g., Pacific Ocean, Kazakhstan")
        layout.addRow("Location:", location_edit)
        
        dropzone_edit = QLineEdit()
        dropzone_edit.setPlaceholderText("e.g., Primary Zone, Backup Zone")
        layout.addRow("Drop Zone:", dropzone_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, Russia, International Waters")
        layout.addRow("Country/Region:", country_edit)
        
        # Add turnaround days field
        turnaround_spin = QSpinBox()
        turnaround_spin.setRange(1, 90)
        turnaround_spin.setValue(7)
        turnaround_spin.setSuffix(" days")
        turnaround_spin.setToolTip("Number of days required for zone recovery/cleanup after re-entry")
        layout.addRow("Zone Recovery:", turnaround_spin)
        
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
        
        zone_type_combo = QComboBox()
        zone_type_combo.addItems(["Ocean", "Land", "Desert", "Remote"])
        layout.addRow("Zone Type:", zone_type_combo)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Validate location
            if not location_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a location.")
                return
            
            # Save new site
            site_data = {
                'name': location_edit.text().strip(),
                'drop_zone': dropzone_edit.text().strip() or 'Primary',
                'latitude': lat_spin.value() if lat_spin.value() != 0 else None,
                'longitude': lon_spin.value() if lon_spin.value() != 0 else None,
                'country': country_edit.text().strip() or None,
                'zone_type': zone_type_combo.currentText(),
                'turnaround_days': turnaround_spin.value()
            }
            
            try:
                reentry = ReentrySite.objects.create(**site_data)
                site_id = reentry.pk
                
                # Add to combo box
                display = f"{site_data['name']} - {site_data['drop_zone']}"
                self.site_combo.addItem(display, site_id)
                self.site_combo.setCurrentIndex(self.site_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Re-entry site added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add site: {e}")
    
    def load_reentry_data(self):
        """Load existing re-entry data for editing"""
        try:
            # Get reentries - try multiple methods since we don't know which exists
            reentries = Reentry.objects.all()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load re-entry data: {e}")
            return
        
        reentry = next((r for r in reentries if r.pk == self.reentry_id), None)
        
        if not reentry:
            QMessageBox.warning(self, "Error", "Re-entry not found.")
            return
        
        # Set launch combo
        launch_id = reentry.pk
        if launch_id:
            for i in range(self.launch_combo.count()):
                if self.launch_combo.itemData(i) == launch_id:
                    self.launch_combo.setCurrentIndex(i)
                    break
        
        # Set date and time
        reentry_date = reentry.reentry_date
        if reentry_date is not None:
            date_obj = reentry_date
            self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        
        reentry_time = reentry.reentry_time if reentry.reentry_time is not None else '12:00:00'
        if reentry_time is not None:
            if type(reentry_time) is str:
                time_parts = reentry_time.split(':')
                self.time_edit.setTime(QTime(int(time_parts[0]), int(time_parts[1]), int(time_parts[2])))
            else:
                self.time_edit.setTime(QTime(reentry_time.hour, reentry_time.minute, reentry_time.second))
        
        # Set site combo
        site_id = reentry.site.pk
        if site_id:
            for i in range(self.site_combo.count()):
                if self.site_combo.itemData(i) == site_id:
                    self.site_combo.setCurrentIndex(i)
                    break
        
        # Set other fields
        self.component_edit.setText(reentry.vehicle_component)
        
        reentry_type = reentry.reentry_type
        if reentry_type is not None:
            index = self.type_combo.findText(reentry_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        
        status_id = reentry.status.pk
        if status_id:
            for i in range(self.status_combo.count()):
                if self.status_combo.itemData(i) == status_id:
                    self.status_combo.setCurrentIndex(i)
                    break
        
        self.remarks_edit.setPlainText(reentry.remarks)
    
    def save_reentry(self):
        """Save the re-entry to database"""
        
        # Validate inputs
        if not self.component_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", 
                              "Please enter a vehicle component.")
            return
        
        # Get launch_id (if selected)
        launch_id = self.launch_combo.currentData()
        
        # Get site_id (if selected from dropdown)
        site_id = self.site_combo.currentData()
        
        # If site was typed in manually, create it
        if site_id is None and self.site_combo.currentText().strip():
            site_text = self.site_combo.currentText().strip()
            # Quick site creation - just location and drop zone
            parts = site_text.split('-', 1)
            location = parts[0].strip() if parts else site_text
            drop_zone = parts[1].strip() if len(parts) > 1 else "Primary"
            
            site_data = {
                'location': location,
                'drop_zone': drop_zone,
                'country': None,
                'turnaround_days': 7,
                'latitude': None,
                'longitude': None,
                'zone_type': 'Unknown'
            }
            
            try:
                reentry = ReentrySite.objects.create(**site_data)
                site_id = reentry.pk
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create site: {e}")
                return
        
        if not site_id:
            QMessageBox.warning(self, "Validation Error", 
                              "Please select or enter a re-entry site.")
            return
        
        # Build re-entry data
        reentry_data = {
            'launch_id': launch_id,
            'reentry_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'reentry_time': self.time_edit.time().toString('HH:mm:ss'),
            'site_id': site_id,
            'vehicle_component': self.component_edit.text().strip(),
            'reentry_type': self.type_combo.currentText(),
            'status_id': self.status_combo.currentData(),
            'remarks': self.remarks_edit.toPlainText().strip() or None,
            'data_source': 'MANUAL'
        }
        
        try:
            _, created = Reentry.objects.update_or_create(pk = self.reentry_id, defaults=reentry_data)
            
            if created:
                QMessageBox.information(self, "Success", "Re-entry added successfully!")
            else:
                QMessageBox.information(self, "Success", "Re-entry updated successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save re-entry: {e}")
