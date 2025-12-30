"""
SHOCKWAVE PLANNER v2.0 - Launch Sites Management View
View, edit, and delete launch sites

Author: Remix Astronautics
Date: December 2025
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QHeaderView,
                              QMessageBox, QDialog, QFormLayout, QLineEdit,
                              QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox)
from PyQt6.QtCore import Qt

from .site_editor_dialog import SiteEditorDialog

# import data models
from data.db.models.launch_site import LaunchSite


class LaunchSitesView(QWidget):
    """Management view for launch sites"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Add Launch Site")
        add_btn.clicked.connect(self.add_site)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.clicked.connect(self.edit_site)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self.delete_site)
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
            'ID', 'Location', 'Launch Pad', 'Country', 'Turnaround (days)', 'Latitude', 'Longitude'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_site)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the sites table"""
        sites = LaunchSite.objects.filter(site_type="LAUNCH")

        self.table.setRowCount(len(sites))
        
        for row, site in enumerate(sites):
            self.table.setItem(row, 0, QTableWidgetItem(str(site.pk)))
            self.table.setItem(row, 1, QTableWidgetItem(site.name))
            self.table.setItem(row, 2, QTableWidgetItem(site.launch_pad))
            self.table.setItem(row, 3, QTableWidgetItem(site.country))
            
            # Turnaround days
            turnaround = site.turnaround_days
            self.table.setItem(row, 4, QTableWidgetItem(str(turnaround)))
            
            lat = site.latitude
            self.table.setItem(row, 5, QTableWidgetItem(f"{lat:.4f}°" if lat else ''))
            
            lon = site.longitude
            self.table.setItem(row, 6, QTableWidgetItem(f"{lon:.4f}°" if lon else ''))
    
    def add_site(self):
        """Add a new launch site"""
        dialog = SiteEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window() is not None:
                self.window().refresh_all()
    
    def edit_site(self):
        """Edit the selected site"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a site to edit.")
            return
        
        site_id = int(self.table.item(current_row, 0).text())
        dialog = SiteEditorDialog(site_id=site_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_table()
            if self.window() is not None:
                self.window().refresh_all()
    
    def delete_site(self):
        """Delete the selected site"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a site to delete.")
            return
        
        site_id = int(self.table.item(current_row, 0).text())
        location = self.table.item(current_row, 1).text()
        pad = self.table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this site?\n\n{location} - {pad}\n\n"
            "This may delete launches from this site.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                LaunchSite.objects.filter(pk=site_id).delete()
                
                self.refresh_table()
                if self.window() is not None:
                    self.window().refresh_all()
                QMessageBox.information(self, "Success", "Site deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete site: {e}")