"""
SHOCKWAVE PLANNER v2.0 - Rockets Management View
View, edit, and delete rockets

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox)
from PyQt6.QtCore import Qt


class RocketsView(QWidget):
    """Management view for rockets"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Family', 'Variant', 'Country'
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
        rockets = self.db.get_all_rockets()
        
        self.table.setRowCount(len(rockets))
        
        for row, rocket in enumerate(rockets):
            self.table.setItem(row, 0, QTableWidgetItem(str(rocket.get('rocket_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(rocket.get('name', '')))
            self.table.setItem(row, 2, QTableWidgetItem(rocket.get('family', '')))
            self.table.setItem(row, 3, QTableWidgetItem(rocket.get('variant', '')))
            self.table.setItem(row, 4, QTableWidgetItem(rocket.get('country', '')))
    
    def add_rocket(self):
        """Add a new rocket"""
        dialog = RocketEditorDialog(self.db, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.parent():
                self.parent().refresh_all()
    
    def edit_rocket(self):
        """Edit the selected rocket"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a rocket to edit.")
            return
        
        rocket_id = int(self.table.item(current_row, 0).text())
        dialog = RocketEditorDialog(self.db, rocket_id=rocket_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.parent():
                self.parent().refresh_all()
    
    def delete_rocket(self):
        """Delete the selected rocket"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a rocket to delete.")
            return
        
        rocket_id = int(self.table.item(current_row, 0).text())
        name = self.table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this rocket?\n\n{name}\n\n"
            "This will NOT delete launches using this rocket.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_rocket(rocket_id)
                self.refresh_table()
                if self.parent():
                    self.parent().refresh_all()
                QMessageBox.information(self, "Success", "Rocket deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete rocket: {e}")


class RocketEditorDialog(QDialog):
    """Dialog for adding/editing rockets"""
    
    def __init__(self, db, rocket_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.rocket_id = rocket_id
        self.setWindowTitle("Add Rocket" if not rocket_id else "Edit Rocket")
        self.setModal(True)
        self.init_ui()
        
        if rocket_id:
            self.load_rocket_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Falcon 9 Block 5, Long March 2D")
        layout.addRow("Rocket Name:", self.name_edit)
        
        # Family
        self.family_edit = QLineEdit()
        self.family_edit.setPlaceholderText("e.g., Falcon, Long March, Soyuz")
        layout.addRow("Family:", self.family_edit)
        
        # Variant
        self.variant_edit = QLineEdit()
        self.variant_edit.setPlaceholderText("e.g., Block 5, CZ-2D, 2.1a")
        layout.addRow("Variant:", self.variant_edit)
        
        # Country
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_rocket)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
    
    def load_rocket_data(self):
        """Load existing rocket data"""
        rockets = self.db.get_all_rockets()
        rocket = next((r for r in rockets if r['rocket_id'] == self.rocket_id), None)
        
        if rocket:
            self.name_edit.setText(rocket.get('name', ''))
            self.family_edit.setText(rocket.get('family', ''))
            self.variant_edit.setText(rocket.get('variant', ''))
            self.country_edit.setText(rocket.get('country', ''))
    
    def save_rocket(self):
        """Save the rocket"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a rocket name.")
            return
        
        rocket_data = {
            'name': name,
            'family': self.family_edit.text().strip() or None,
            'variant': self.variant_edit.text().strip() or None,
            'country': self.country_edit.text().strip() or None
        }
        
        try:
            if self.rocket_id:
                self.db.update_rocket(self.rocket_id, rocket_data)
                QMessageBox.information(self, "Success", "Rocket updated successfully!")
            else:
                self.db.add_rocket(rocket_data)
                QMessageBox.information(self, "Success", "Rocket added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save rocket: {e}")
