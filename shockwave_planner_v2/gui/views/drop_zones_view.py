"""
SHOCKWAVE PLANNER v2.0 - Drop Zones Management View
View, edit, and delete re-entry drop zones

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt

from .zone_editor_dialog import ZoneEditorDialog

# import data models
from data.db.models.reentry_site import ReentrySite


class DropZonesView(QWidget):
    """Management view for re-entry drop zones"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Drop Zone")
        add_btn.clicked.connect(self.add_zone)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_zone)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_zone)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_table)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Location', 'Drop Zone', 'Country', 'Recovery (days)', 'Latitude', 'Longitude'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_zone)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the zones table"""
        zones = ReentrySite.objects.all()

        self.table.setRowCount(len(zones))
        
        for row, zone in enumerate(zones):
            self.table.setItem(row, 0, QTableWidgetItem(str(zone.pk)))
            self.table.setItem(row, 1, QTableWidgetItem(zone.name))
            self.table.setItem(row, 2, QTableWidgetItem(zone.drop_zone))
            self.table.setItem(row, 3, QTableWidgetItem(zone.country))
            
            # Recovery time
            turnaround = zone.turnaround_days
            self.table.setItem(row, 4, QTableWidgetItem(str(turnaround)))
            
            lat = zone.latitude
            self.table.setItem(row, 5, QTableWidgetItem(f"{lat:.4f}°" if lat else ''))
            
            lon = zone.longitude
            self.table.setItem(row, 6, QTableWidgetItem(f"{lon:.4f}°" if lon else ''))
    
    def add_zone(self):
        """Add a new drop zone"""
        dialog = ZoneEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def edit_zone(self):
        """Edit the selected zone"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a drop zone to edit.")
            return
        
        zone_id = int(self.table.item(current_row, 0).text())
        dialog = ZoneEditorDialog(zone_id=zone_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def delete_zone(self):
        """Delete the selected zone"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a drop zone to delete.")
            return
        
        zone_id = int(self.table.item(current_row, 0).text())
        location = self.table.item(current_row, 1).text()
        zone = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this drop zone?\n\n{location} - {zone}\n\n"
            "This will NOT delete re-entries from this zone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ReentrySite.objects.filter(pk=zone_id).delete()
                
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Drop zone deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete drop zone: {e}")
