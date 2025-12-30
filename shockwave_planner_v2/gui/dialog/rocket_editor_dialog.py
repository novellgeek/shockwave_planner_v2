from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QScrollArea)
from PyQt6.QtCore import Qt

# import data models
from data.db.models.rocket import Rocket

class RocketEditorDialog(QDialog):
    """Dialog for adding/editing rockets"""
    
    def __init__(self, rocket_id=None, parent=None):
        super().__init__(parent)
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
        rockets = Rocket.objects.all()
        rocket = next((r for r in rockets if r.pk == self.rocket_id), None)
        
        if not rocket:
            QMessageBox.critical(self, "Error", f"Could not find rocket with ID {self.rocket_id}")
            self.reject()
            return
        
        self.name_edit.setText(rocket.name)
        self.alternative_name_edit.setText(rocket.alt_name)
        self.family_edit.setText(rocket.family)
        self.variant_edit.setText(rocket.variant)
        self.country_edit.setText(rocket.country)
        self.stages_edit.setText(str(rocket.stages))
        self.boosters_edit.setText(str(rocket.boosters))
        self.payload_leo_edit.setText(str(rocket.payload_leo))
        self.payload_sso_edit.setText(str(rocket.payload_sso))
        self.payload_gto_edit.setText(str(rocket.payload_gto))
        self.payload_tli_edit.setText(str(rocket.payload_tli))
    
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
            _, created = Rocket.objects.update_or_create(pk=self.rocket_id, defaults=rocket_data)
            if created:
                QMessageBox.information(self, "Success", "Site added successfully!")
            else:
                QMessageBox.information(self, "Success", "Site updated successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save rocket: {e}")