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

# import gui
from .reentry_vehicle_editor_dialog import ReentryVehicleEditorDialog

# import data models
from data.db.models.reentry_vehicle import ReentryVehicle

class ReentryVehiclesView(QWidget):
    """Management view for re-entry vehicles"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        vehicles = ReentryVehicle.objects.all()
        
        self.table.setRowCount(len(vehicles))
        
        for row, vehicle in enumerate(vehicles):
            self.table.setItem(row, 0, QTableWidgetItem(str(vehicle.pk)))
            self.table.setItem(row, 1, QTableWidgetItem(vehicle.name))
            self.table.setItem(row, 2, QTableWidgetItem(vehicle.alt_name))
            self.table.setItem(row, 3, QTableWidgetItem(vehicle.family))
            self.table.setItem(row, 4, QTableWidgetItem(vehicle.variant))
            self.table.setItem(row, 5, QTableWidgetItem(vehicle.manufacturer))
            self.table.setItem(row, 6, QTableWidgetItem(vehicle.country))
            self.table.setItem(row, 7, QTableWidgetItem(vehicle.decelerator))

    def add_vehicle(self):
        """Add a new re-entry vehicle"""
        dialog = ReentryVehicleEditorDialog(parent=self)
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
        
        dialog = ReentryVehicleEditorDialog(vehicle_id=vehicle_id, parent=self)
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
                ReentryVehicle.objects.filter(pk=vehicle_id).delete()
                
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Re-entry vehicle deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete re-entry vehicle: {e}")