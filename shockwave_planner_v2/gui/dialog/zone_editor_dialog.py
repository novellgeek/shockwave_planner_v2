from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt

# import data models
from data.db.models.reentry_site import ReentrySite

class ZoneEditorDialog(QDialog):
    """Dialog for adding/editing drop zones"""
    
    def __init__(self, zone_id=None, parent=None):
        super().__init__(parent)
        self.zone_id = zone_id
        self.setWindowTitle("Add Drop Zone" if not zone_id else "Edit Drop Zone")
        self.setModal(True)
        self.init_ui()
        
        if zone_id:
            self.load_zone_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QFormLayout()
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., Pacific Ocean, Atlantic Ocean, Inner Mongolia")
        layout.addRow("Region/Location:", self.location_edit)
        
        # Drop Zone
        self.zone_edit = QLineEdit()
        self.zone_edit.setPlaceholderText("e.g., Zone A, LZ-1, Recovery Area 3")
        layout.addRow("Drop Zone:", self.zone_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Recovery Time
        self.recovery_spin = QSpinBox()
        self.recovery_spin.setRange(1, 90)
        self.recovery_spin.setValue(7)
        self.recovery_spin.setSuffix(" days")
        self.recovery_spin.setToolTip("Number of days required for zone recovery/cleanup after re-entry")
        layout.addRow("Zone Recovery:", self.recovery_spin)
        
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
        
        # Zone Type (optional)
        self.zone_type_edit = QLineEdit()
        self.zone_type_edit.setPlaceholderText("e.g., Ocean, Land, Desert (optional)")
        layout.addRow("Zone Type:", self.zone_type_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_zone)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_zone_data(self):
        """Load existing zone data"""
        # FIXED: Use get_all_reentry_sites() instead of get_all_sites()
        zones = ReentrySite.objects.all()
        zone = next((z for z in zones if z.pk == self.zone_id), None)
        
        if zone:
            self.location_edit.setText(zone.name)
            self.zone_edit.setText(zone.drop_zone)
            self.country_edit.setText(zone.country)
            
            # Recovery time
            if zone.turnaround_days is not None:
                self.recovery_spin.setValue(zone.turnaround_days)
            
            if zone.latitude is not None:
                self.lat_spin.setValue(zone.latitude)
            
            if zone.longitude is not None:
                self.lon_spin.setValue(zone.longitude)
            
            # Zone type (if available from database)
            if zone.zone_type is not None:
                self.zone_type_edit.setText(zone.zone_type)
    
    def save_zone(self):
        """Save the drop zone"""
        location = self.location_edit.text().strip()
        zone = self.zone_edit.text().strip()
        
        if not location or not zone:
            QMessageBox.warning(self, "Validation Error", 
                              "Please enter both location and drop zone.")
            return
        
        zone_data = {
            'name': location,
            'drop_zone': zone,
            'latitude': self.lat_spin.value(),
            'longitude': self.lon_spin.value(),
            'country': self.country_edit.text().strip() or None,
            'zone_type': self.zone_type_edit.text().strip() or None,
            'turnaround_days': self.recovery_spin.value()
        }
        
        try:           
            _, created = ReentrySite.objects.update_or_create(pk=self.zone_id, defaults=zone_data)
            
            if created:
                QMessageBox.information(self, "Success", "Site added successfully!")
            else:
                QMessageBox.information(self, "Success", "Site updated successfully!")

            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save drop zone: {e}")