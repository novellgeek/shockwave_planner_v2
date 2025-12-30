from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QScrollArea, QTextEdit, QSpinBox)
from PyQt6.QtCore import Qt

# import data models
from data.db.models.reentry_vehicle import ReentryVehicle


class ReentryVehicleEditorDialog(QDialog):
    """Dialog for adding/editing re-entry vehicles"""
    
    def __init__(self, vehicle_id=None, parent=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.setWindowTitle("Add Re-entry Vehicle" if vehicle_id is None else "Edit Re-entry Vehicle")
        self.setModal(True)
        self.init_ui()
        
        if vehicle_id:
            self.load_vehicle_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create a scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(500)
        
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        
        # Vehicle Name (required)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Dragon 2, Crew Dragon C206, Soyuz MS-25")
        layout.addRow("Vehicle Name:*", self.name_edit)
        
        # Alternative Name
        self.alternative_name_edit = QLineEdit()
        self.alternative_name_edit.setPlaceholderText("e.g., C206, MS-25")
        layout.addRow("Alternative Name:", self.alternative_name_edit)
        
        # Family
        self.family_edit = QLineEdit()
        self.family_edit.setPlaceholderText("e.g., Dragon, Soyuz, Crew Dragon, Cargo Dragon")
        layout.addRow("Family:", self.family_edit)
        
        # Variant
        self.variant_edit = QLineEdit()
        self.variant_edit.setPlaceholderText("e.g., C206, Block 1, MS-25")
        layout.addRow("Variant:", self.variant_edit)
        
        # Manufacturer
        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setPlaceholderText("e.g., SpaceX, Roscosmos, Boeing")
        layout.addRow("Manufacturer:", self.manufacturer_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, Russia, China")
        layout.addRow("Country:", self.country_edit)
        
        # Payload Capacity
        self.payload_spin = QSpinBox()
        self.payload_spin.setRange(0, 999999)
        self.payload_spin.setSuffix(" kg")
        self.payload_spin.setSpecialValueText("N/A")
        layout.addRow("Payload Capacity:", self.payload_spin)
        
        # Decelerator
        self.decelerator_edit = QLineEdit()
        self.decelerator_edit.setPlaceholderText("e.g., Parachute, Heat Shield, Retropropulsion")
        layout.addRow("Decelerator Type:", self.decelerator_edit)
        
        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setPlaceholderText("Additional notes, specifications, history...")
        self.remarks_edit.setMaximumHeight(100)
        layout.addRow("Remarks:", self.remarks_edit)
        
        scroll.setWidget(form_widget)
        
        # Main layout with scroll area and buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_vehicle)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
    
    def load_vehicle_data(self):
        """Load existing vehicle data"""
        vehicles = ReentryVehicle.objects.all()
        vehicle = next((v for v in vehicles if v.pk == self.vehicle_id), None)
        
        if not vehicle:
            QMessageBox.critical(self, "Error", f"Could not find re-entry vehicle with ID {self.vehicle_id}")
            self.reject()
            return
        
        self.name_edit.setText(vehicle.name)
        self.alternative_name_edit.setText(vehicle.alt_name)
        self.family_edit.setText(vehicle.family)
        self.variant_edit.setText(vehicle.variant)
        self.manufacturer_edit.setText(vehicle.manufacturer)
        self.country_edit.setText(vehicle.country)
        
        payload = vehicle.payload
        if payload is not None:
            try:
                self.payload_spin.setValue(int(payload))
            except (ValueError, TypeError):
                self.payload_spin.setValue(0)
        
        self.decelerator_edit.setText(vehicle.decelerator)
        self.remarks_edit.setPlainText(vehicle.remarks)
    
    def save_vehicle(self):
        """Save the re-entry vehicle"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a vehicle name.")
            return
        
        vehicle_data = {
            'name': name,
            'alt_name': self.alternative_name_edit.text().strip() or None,
            'family': self.family_edit.text().strip() or None,
            'variant': self.variant_edit.text().strip() or None,
            'manufacturer': self.manufacturer_edit.text().strip() or None,
            'country': self.country_edit.text().strip() or None,
            'payload': self.payload_spin.value() if self.payload_spin.value() > 0 else None,
            'decelerator': self.decelerator_edit.text().strip() or None,
            'remarks': self.remarks_edit.toPlainText().strip() or None,
            'external_id': None
        }

        try:
            _, created = ReentryVehicle.objects.update_or_create(pk=self.vehicle_id, defaults=vehicle_data)
            if created:
                QMessageBox.information(self, "Success", "Re-entry vehicle added successfully!")
            else:
                QMessageBox.information(self, "Success", "Re-entry vehicle updated successfully!")
            
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save re-entry vehicle: {e}")
