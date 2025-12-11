"""
SHOCKWAVE PLANNER v2.0 - Re-entry Vehicles Management View
View, edit, and delete re-entry vehicles

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QScrollArea, QTextEdit, QSpinBox)
from PyQt6.QtCore import Qt


class ReentryVehiclesView(QWidget):
    """Management view for re-entry vehicles"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Re-entry Vehicle")
        add_btn.clicked.connect(self.add_vehicle)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_vehicle)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_vehicle)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_table)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Vehicle Name', 'Alt Name', 'Family', 'Variant', 'Manufacturer', 'Country', 'Decelerator'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_vehicle)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the re-entry vehicles table"""
        vehicles = self.db.get_all_reentry_vehicles()
        
        self.table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
            # Helper function to safely convert values to strings
            def safe_str(value):
                return str(value) if value is not None else ''
            
            self.table.setItem(row, 0, QTableWidgetItem(safe_str(vehicle.get('vehicle_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(safe_str(vehicle.get('name', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(safe_str(vehicle.get('alternative_name', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(safe_str(vehicle.get('family', ''))))
            self.table.setItem(row, 4, QTableWidgetItem(safe_str(vehicle.get('variant', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(safe_str(vehicle.get('manufacturer', ''))))
            self.table.setItem(row, 6, QTableWidgetItem(safe_str(vehicle.get('country', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(safe_str(vehicle.get('decelerator', ''))))

    def add_vehicle(self):
        """Add a new re-entry vehicle"""
        dialog = ReentryVehicleEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def edit_vehicle(self):
        """Edit the selected re-entry vehicle"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a re-entry vehicle to edit.")
            return
        
        # Safely get the vehicle_id from the table
        id_item = self.table.item(current_row, 0)
        if not id_item or not id_item.text().strip():
            QMessageBox.warning(self, "Invalid Selection", "The selected row has no valid ID.")
            return
        
        try:
            vehicle_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", f"Invalid vehicle ID: {id_item.text()}")
            return
        
        dialog = ReentryVehicleEditorDialog(self.db, vehicle_id=vehicle_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def delete_vehicle(self):
        """Delete the selected re-entry vehicle"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a re-entry vehicle to delete.")
            return
        
        # Safely get the vehicle_id from the table
        id_item = self.table.item(current_row, 0)
        if not id_item or not id_item.text().strip():
            QMessageBox.warning(self, "Invalid Selection", "The selected row has no valid ID.")
            return
        
        try:
            vehicle_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", f"Invalid vehicle ID: {id_item.text()}")
            return
        
        name = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this re-entry vehicle?\n\n{name}\n\n"
            "This will NOT delete re-entry operations using this vehicle.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_reentry_vehicle(vehicle_id)
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Re-entry vehicle deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete re-entry vehicle: {e}")


class ReentryVehicleEditorDialog(QDialog):
    """Dialog for adding/editing re-entry vehicles"""
    
    def __init__(self, db, vehicle_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.vehicle_id = vehicle_id
        self.setWindowTitle("Add Re-entry Vehicle" if not vehicle_id else "Edit Re-entry Vehicle")
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
        vehicles = self.db.get_all_reentry_vehicles()
        vehicle = next((v for v in vehicles if v['vehicle_id'] == self.vehicle_id), None)
        
        if not vehicle:
            QMessageBox.critical(self, "Error", f"Could not find re-entry vehicle with ID {self.vehicle_id}")
            self.reject()
            return
        
        # Helper function to safely convert values to strings
        def safe_str(value):
            return str(value) if value is not None else ''
        
        self.name_edit.setText(safe_str(vehicle.get('name', '')))
        self.alternative_name_edit.setText(safe_str(vehicle.get('alternative_name', '')))
        self.family_edit.setText(safe_str(vehicle.get('family', '')))
        self.variant_edit.setText(safe_str(vehicle.get('variant', '')))
        self.manufacturer_edit.setText(safe_str(vehicle.get('manufacturer', '')))
        self.country_edit.setText(safe_str(vehicle.get('country', '')))
        
        payload = vehicle.get('payload')
        if payload:
            try:
                self.payload_spin.setValue(int(payload))
            except (ValueError, TypeError):
                self.payload_spin.setValue(0)
        
        self.decelerator_edit.setText(safe_str(vehicle.get('decelerator', '')))
        self.remarks_edit.setPlainText(safe_str(vehicle.get('remarks', '')))
    
    def save_vehicle(self):
        """Save the re-entry vehicle"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a vehicle name.")
            return
        
        vehicle_data = {
            'name': name,
            'alternative_name': self.alternative_name_edit.text().strip() or None,
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
            if self.vehicle_id:
                self.db.update_reentry_vehicle(self.vehicle_id, vehicle_data)
                QMessageBox.information(self, "Success", "Re-entry vehicle updated successfully!")
            else:
                self.db.add_reentry_vehicle(vehicle_data)
                QMessageBox.information(self, "Success", "Re-entry vehicle added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save re-entry vehicle: {e}")
