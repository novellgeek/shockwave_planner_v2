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
        rockets = self.db.get_all_rockets()
        
        self.table.setRowCount(len(rockets))
        
        for row, rocket in enumerate(rockets):
            # Helper function to safely convert values to strings
            def safe_str(value):
                return str(value) if value is not None else ''
            
            self.table.setItem(row, 0, QTableWidgetItem(safe_str(rocket.get('rocket_id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(safe_str(rocket.get('country', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(safe_str(rocket.get('name', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(safe_str(rocket.get('alternative_name', ''))))   
            self.table.setItem(row, 4, QTableWidgetItem(safe_str(rocket.get('family', ''))))
            self.table.setItem(row, 5, QTableWidgetItem(safe_str(rocket.get('variant', ''))))
            self.table.setItem(row, 6, QTableWidgetItem(safe_str(rocket.get('stages', ''))))
            self.table.setItem(row, 7, QTableWidgetItem(safe_str(rocket.get('boosters', ''))))
            self.table.setItem(row, 8, QTableWidgetItem(safe_str(rocket.get('payload_leo', ''))))
            self.table.setItem(row, 9, QTableWidgetItem(safe_str(rocket.get('payload_sso', ''))))
            self.table.setItem(row, 10, QTableWidgetItem(safe_str(rocket.get('payload_gto', ''))))
            self.table.setItem(row, 11, QTableWidgetItem(safe_str(rocket.get('payload_tli', ''))))

    def add_rocket(self):
        """Add a new rocket"""
        dialog = RocketEditorDialog(self.db, parent=self)
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
        if not id_item or not id_item.text().strip():
            QMessageBox.warning(self, "Invalid Selection", "The selected row has no valid ID.")
            return
        
        try:
            rocket_id = int(id_item.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", f"Invalid rocket ID: {id_item.text()}")
            return
        
        dialog = RocketEditorDialog(self.db, rocket_id=rocket_id, parent=self)
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
                self.db.delete_rocket(rocket_id)
                self.refresh_table()
                if self.window():
                    self.window().refresh_all()
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
        # Create a scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(500)
        
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        
        # Basic Information
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., Falcon 9 Block 5, Long March 2D")
        layout.addRow("Rocket Name:*", self.name_edit)
        
        self.alternative_name_edit = QLineEdit()
        self.alternative_name_edit.setPlaceholderText("e.g., F9, CZ-2D")
        layout.addRow("Alternative Name:", self.alternative_name_edit)
        
        self.family_edit = QLineEdit()
        self.family_edit.setPlaceholderText("e.g., Falcon, Long March, Soyuz")
        layout.addRow("Family:", self.family_edit)
        
        self.variant_edit = QLineEdit()
        self.variant_edit.setPlaceholderText("e.g., Block 5, CZ-2D, 2.1a")
        layout.addRow("Variant:", self.variant_edit)
        
        self.country_edit = QLineEdit()
        self.country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", self.country_edit)
        
        # Configuration
        self.stages_edit = QLineEdit()
        self.stages_edit.setPlaceholderText("e.g., 2, 3")
        layout.addRow("Stages:", self.stages_edit)
        
        self.boosters_edit = QLineEdit()
        self.boosters_edit.setPlaceholderText("e.g., 0, 2, 4")
        layout.addRow("Boosters:", self.boosters_edit)
        
        # Payload Capacities
        self.payload_leo_edit = QLineEdit()
        self.payload_leo_edit.setPlaceholderText("e.g., 22800 kg")
        layout.addRow("Payload to LEO:", self.payload_leo_edit)
        
        self.payload_sso_edit = QLineEdit()
        self.payload_sso_edit.setPlaceholderText("e.g., 15600 kg")
        layout.addRow("Payload to SSO:", self.payload_sso_edit)
        
        self.payload_gto_edit = QLineEdit()
        self.payload_gto_edit.setPlaceholderText("e.g., 8300 kg")
        layout.addRow("Payload to GTO:", self.payload_gto_edit)
        
        self.payload_tli_edit = QLineEdit()
        self.payload_tli_edit.setPlaceholderText("e.g., 4020 kg")
        layout.addRow("Payload to TLI:", self.payload_tli_edit)
        
        scroll.setWidget(form_widget)
        
        # Main layout with scroll area and buttons
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_rocket)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self.setLayout(main_layout)
    
    def load_rocket_data(self):
        """Load existing rocket data"""
        rockets = self.db.get_all_rockets()
        rocket = next((r for r in rockets if r['rocket_id'] == self.rocket_id), None)
        
        if not rocket:
            QMessageBox.critical(self, "Error", f"Could not find rocket with ID {self.rocket_id}")
            self.reject()
            return
        
        # Helper function to safely convert values to strings
        def safe_str(value):
            return str(value) if value is not None else ''
        
        self.name_edit.setText(safe_str(rocket.get('name', '')))
        self.alternative_name_edit.setText(safe_str(rocket.get('alternative_name', '')))
        self.family_edit.setText(safe_str(rocket.get('family', '')))
        self.variant_edit.setText(safe_str(rocket.get('variant', '')))
        self.country_edit.setText(safe_str(rocket.get('country', '')))
        self.stages_edit.setText(safe_str(rocket.get('stages', '')))
        self.boosters_edit.setText(safe_str(rocket.get('boosters', '')))
        self.payload_leo_edit.setText(safe_str(rocket.get('payload_leo', '')))
        self.payload_sso_edit.setText(safe_str(rocket.get('payload_sso', '')))
        self.payload_gto_edit.setText(safe_str(rocket.get('payload_gto', '')))
        self.payload_tli_edit.setText(safe_str(rocket.get('payload_tli', '')))
    
    def save_rocket(self):
        """Save the rocket"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a rocket name.")
            return
        
        rocket_data = {
            'name': name,
            'alternative_name': self.alternative_name_edit.text().strip() or None,
            'family': self.family_edit.text().strip() or None,
            'variant': self.variant_edit.text().strip() or None,
            'country': self.country_edit.text().strip() or None,
            'stages': self.stages_edit.text().strip() or None,
            'boosters': self.boosters_edit.text().strip() or None,
            'payload_leo': self.payload_leo_edit.text().strip() or None,
            'payload_sso': self.payload_sso_edit.text().strip() or None,
            'payload_gto': self.payload_gto_edit.text().strip() or None,
            'payload_tli': self.payload_tli_edit.text().strip() or None
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


