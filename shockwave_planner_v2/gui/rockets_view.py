"""
SHOCKWAVE PLANNER v2.0 - Rockets Management View
View, edit, and delete rockets

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QScrollArea)
from PyQt6.QtCore import Qt

from rocket_editor_dialog import RocketEditorDialog

# import data models
from data.db.models.rocket import Rocket

class RocketsView(QWidget):
    """Management view for rockets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Rocket")
        add_btn.clicked.connect(self.add_rocket)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_rocket)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_rocket)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_table)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Country', 'Name', 'Alt Name', 'Family', 'Variant', 'Stages', 'Boosters', 'Payload Leo', 'Payload SSO', 'Payload GTO', 'Payload TLI'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_rocket)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the rockets table"""
        rockets = Rocket.objects.all()

        self.table.setRowCount(len(rockets))
        
        for row, rocket in enumerate(rockets):           
            self.table.setItem(row, 0, QTableWidgetItem(str(rocket.pk)))
            self.table.setItem(row, 1, QTableWidgetItem(rocket.country))
            self.table.setItem(row, 2, QTableWidgetItem(rocket.name))
            self.table.setItem(row, 3, QTableWidgetItem(rocket.alt_name))
            self.table.setItem(row, 4, QTableWidgetItem(rocket.family))
            self.table.setItem(row, 5, QTableWidgetItem(rocket.variant))
            self.table.setItem(row, 6, QTableWidgetItem(rocket.stages))
            self.table.setItem(row, 7, QTableWidgetItem(rocket.boosters)) #FIXME possibly use len(launcher_stages) rocket["configuration"]
            self.table.setItem(row, 8, QTableWidgetItem(str(rocket.payload_leo)))
            self.table.setItem(row, 9, QTableWidgetItem(str(rocket.payload_sso)))
            self.table.setItem(row, 10, QTableWidgetItem(str(rocket.payload_gto)))
            self.table.setItem(row, 11, QTableWidgetItem(str(rocket.payload_tli))) #FIXME

    def add_rocket(self):
        """Add a new rocket"""
        dialog = RocketEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def edit_rocket(self):
        """Edit the selected rocket"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a rocket to edit.")
            return
        
        # Safely get the rocket_id from the table
        id_item = self.table.item(current_row, 0)
        if id_item is None or id_item.text().strip() is None:
            QMessageBox.warning(self, "Invalid Selection", "The selected row has no valid ID.")
            return
        id_item.data
        try:
            rocket_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", f"Invalid rocket ID: {id_item.text()}")
            return
        
        dialog = RocketEditorDialog(rocket_id=rocket_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window():
                self.window().refresh_all()
    
    def delete_rocket(self):
        """Delete the selected rocket"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a rocket to delete.")
            return
        
        # Safely get the rocket_id from the table
        id_item = self.table.item(current_row, 0)
        if not id_item or not id_item.text().strip():
            QMessageBox.warning(self, "Invalid Selection", "The selected row has no valid ID.")
            return
        
        try:
            rocket_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", f"Invalid rocket ID: {id_item.text()}")
            return
        
        name = self.table.item(current_row, 2).text()  # Fixed: was using column 1, should be 2 for name
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this rocket?\n\n{name}\n\n"
            "This will NOT delete launches using this rocket.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                Rocket.objects.filter(pk=rocket_id).delete()

                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Rocket deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete rocket: {e}")