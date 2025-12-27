from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QTabWidget, QGroupBox,
                              QDialog, QFormLayout, QDialogButtonBox, QLineEdit,
                              QComboBox, QDateEdit, QTimeEdit, QTextEdit,
                              QMessageBox, QProgressDialog, QTableWidget, QTableWidgetItem,
                              QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from datetime import datetime
import sys
import os

# import data models
from data.db.models.launch_site import LaunchSite

class SiteEditorDialog(QDialog):
    """Dialog for adding/editing launch sites"""
    
    def __init__(self, site_id=None, parent=None):
        super().__init__(parent)
        self.site_id = site_id
        self.setWindowTitle("Add Launch Site" if not site_id else "Edit Launch Site")
        self.setModal(True)
        self.init_ui()
        
        if site_id:
            self.load_site_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QFormLayout()
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Cape Canaveral, Vandenberg, Jiuquan")
        layout.addRow("Location:", self.location_edit)
        
        # Launch Pad
        self.pad_edit = QLineEdit()
        self.pad_edit.setPlaceholderText("e.g., LC-39A, SLC-4E, LC-43/95")
        layout.addRow("Launch Pad:", self.pad_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Turnaround Days
        self.turnaround_spin = QSpinBox()
        self.turnaround_spin.setRange(1, 90)
        self.turnaround_spin.setValue(7)
        self.turnaround_spin.setSuffix(" days")
        self.turnaround_spin.setToolTip("Number of days required between launches at this pad")
        layout.addRow("Pad Turnaround:", self.turnaround_spin)
        
        # Latitude
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(4)
        self.lat_spin.setSuffix("°")
        self.lat_spin.setSpecialValueText("Not Set")
        layout.addRow("Latitude:", self.lat_spin)
        
        # Longitude
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(4)
        self.lon_spin.setSuffix("°")
        self.lon_spin.setSpecialValueText("Not Set")
        layout.addRow("Longitude:", self.lon_spin)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_site)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_site_data(self):
        """Load existing site data"""
        sites = LaunchSite.objects.all()
        
        site = next((s for s in sites if s.pk == self.site_id), None)
        
        if site:
            self.location_edit.setText(site.name)
            self.pad_edit.setText(site.launch_pad)
            self.country_edit.setText(site.country)
            
            # Turnaround days
            if site.turnaround_days is not None:
                self.turnaround_spin.setValue(site.turnaround_days)
            
            if site.latitude is not None:
                self.lat_spin.setValue(site.latitude)
            
            if site.longitude is not None:
                self.lon_spin.setValue(site.longitude)
    
    def save_site(self):
        """Save the site"""
        location = self.location_edit.text().strip()
        pad = self.pad_edit.text().strip()
        
        if not location or not pad:
            QMessageBox.warning(self, "Validation Error", 
                              "Please enter both location and launch pad.")
            return
        
        site_data = {
            'name': location,
            'launch_pad': pad,
            'latitude': self.lat_spin.value(),
            'longitude': self.lon_spin.value(),
            'country': self.country_edit.text().strip() or None,
            'site_type': 'LAUNCH',
            'turnaround_days': self.turnaround_spin.value()
        }
        
        try:
            _, created = LaunchSite.objects.update_or_create(pk=self.site_id, defaults=site_data)
            if created:
                QMessageBox.information(self, "Success", "Site added successfully!")
            else:
                QMessageBox.information(self, "Success", "Site updated successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save site: {e}")
