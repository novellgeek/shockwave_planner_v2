from PyQt6.QtWidgets import (QPushButton, QDialog, QFormLayout, QDialogButtonBox, 
                              QLineEdit, QComboBox, QDateEdit, QTimeEdit, QTextEdit,
                              QMessageBox, QTableWidget, QTableWidgetItem)
from PyQt6.QtCore import QDate, QTime
from datetime import datetime
from django.db.models import Q
from django.db import transaction

# import data models
from data.db.models.launch import Launch
from data.db.models.launch_site import LaunchSite
from data.db.models.rocket import Rocket
from data.db.models.status import Status
from data.db.models.launch_notam import LaunchNotam
from data.db.models.notam import Notam

class LaunchEditorDialog(QDialog):
    """Dialog for adding/editing launch records"""
    
    def __init__(self, launch_id: int = None, parent=None):
        super().__init__(parent)
        self.launch_id = launch_id
        self.init_ui()
        
        if launch_id is not None:
            self.load_launch_data()
    
    def init_ui(self):
        self.setWindowTitle("Launch Editor" if not self.launch_id else "Edit Launch")
        self.setMinimumWidth(600)
        
        layout = QFormLayout()
        
        # Date and Time
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow("Launch Date:", self.date_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm:ss")
        layout.addRow("Launch Time:", self.time_edit)
        
        # Launch Site
        self.site_combo = QComboBox()
        self.site_combo.setEditable(True)
        sites = LaunchSite.objects.all()
        for site in sites:
            self.site_combo.addItem(f"{site.name} - {site.launch_pad}", site.pk)
        layout.addRow("Launch Site:", self.site_combo)
        
        # Add Site button
        add_site_btn = QPushButton("Add New Site...")
        add_site_btn.clicked.connect(self.add_new_site)
        layout.addRow("", add_site_btn)
        
        # Rocket
        self.rocket_combo = QComboBox()
        self.rocket_combo.setEditable(True)
        rockets = Rocket.objects.all()
        for rocket in rockets:
            self.rocket_combo.addItem(rocket.name, rocket.pk)
        layout.addRow("Rocket:", self.rocket_combo)
        
        # Add Rocket button
        add_rocket_btn = QPushButton("Add New Rocket...")
        add_rocket_btn.clicked.connect(self.add_new_rocket)
        layout.addRow("", add_rocket_btn)
        
        # Mission Details
        self.mission_edit = QLineEdit()
        layout.addRow("Mission Name:", self.mission_edit)
        
        self.payload_edit = QLineEdit()
        layout.addRow("Payload:", self.payload_edit)
        
        # Orbit
        self.orbit_combo = QComboBox()
        self.orbit_combo.addItems(['LEO', 'SSO', 'GTO', 'GEO', 'MEO', 'HEO', 'Lunar', 'Other'])
        layout.addRow("Orbit Type:", self.orbit_combo)
        
        # NOTAM
        self.notam_edit = QTableWidget()
        self.notam_edit.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        self.notam_edit.setColumnCount(4)
        self.notam_edit.setRowCount(1)
        self.notam_edit.setMaximumSize(405,self.notam_edit.rowHeight(0))
        self.notam_edit.verticalHeader().hide()
        self.notam_edit.horizontalHeader().hide()
        layout.addRow("NOTAM Reference:", self.notam_edit)
        self.notam_edit.editTriggers()
        
        # new NOTAM button
        add_notam_btn = QPushButton("Add New NOTAM...")
        add_notam_btn.clicked.connect(self.add_new_notam)
        layout.addRow("", add_notam_btn)


        # Status
        self.status_combo = QComboBox()
        statuses = Status.objects.all()
        for status in statuses:
            self.status_combo.addItem(status.name, status.pk)
        layout.addRow("Status:", self.status_combo)
        
        # Remarks
        self.remarks_edit = QTextEdit()
        self.remarks_edit.setMaximumHeight(100)
        layout.addRow("Remarks:", self.remarks_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_launch)
        button_box.rejected.connect(self.reject)
        
        layout.addRow(button_box)
        self.setLayout(layout)
    
    def load_launch_data(self):
        """Load existing launch data"""
        launches = Launch.objects.all()
        launch = next((l for l in launches if l.pk == self.launch_id), None)
        
        if launch is not None:
            if launch.launch_date is not None:
                date_obj = launch.launch_date
                self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            
            if launch.launch_time is not None:
                time_obj = launch.launch_time
                self.time_edit.setTime(QTime(time_obj.hour, time_obj.minute, time_obj.second))
            
            if launch.site.pk is not None:
                index = self.site_combo.findData(launch.site.pk)
                if index >= 0:
                    self.site_combo.setCurrentIndex(index)
            
            if launch.rocket.pk is not None:
                index = self.rocket_combo.findData(launch.rocket.pk)
                if index >= 0:
                    self.rocket_combo.setCurrentIndex(index)
            
            if launch.status.pk is not None:
                index = self.status_combo.findData(launch.status.pk)
                if index >= 0:
                    self.status_combo.setCurrentIndex(index)
            
            self.mission_edit.setText(launch.mission_name)
            self.payload_edit.setText(launch.payload_name)
            
            notam_data = list(launch.notams.all())
            
            for col in range(len(notam_data)):
                serial = notam_data[col].serial
                self.notam_edit.setItem(0, col, QTableWidgetItem(serial))

            if launch.orbit_type is not None:
                index = self.orbit_combo.findText(launch.orbit_type)
                if index >= 0:
                    self.orbit_combo.setCurrentIndex(index)
            
            self.remarks_edit.setPlainText(launch.remarks)
    
    def add_new_notam(self):
        """Open dialog to add a new NOTAM"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add NOTAM")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        serial_edit = QLineEdit()
        serial_edit.setPlaceholderText("e.g. F0271/25")
        layout.addRow("NOTAM serial:", serial_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)


        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save new site
            notam_data = {
                'serial': serial_edit.text()
           }
            
            try:
                # TODO validate NOTAM serial
                Notam.objects.create(**notam_data)
                              
                QMessageBox.information(self, "Success", "NOTAM added successfully!")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add NOTAM: {e}")


    def add_new_site(self):
        """Open dialog to add a new launch site"""
        from PyQt6.QtWidgets import QDoubleSpinBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Launch Site")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        location_edit = QLineEdit()
        location_edit.setPlaceholderText("e.g., Cape Canaveral, Vandenberg")
        layout.addRow("Location:", location_edit)
        
        pad_edit = QLineEdit()
        pad_edit.setPlaceholderText("e.g., LC-39A, SLC-4E")
        layout.addRow("Launch Pad:", pad_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country:", country_edit)
        
        lat_spin = QDoubleSpinBox()
        lat_spin.setRange(-90, 90)
        lat_spin.setDecimals(4)
        lat_spin.setSuffix("°")
        layout.addRow("Latitude:", lat_spin)
        
        lon_spin = QDoubleSpinBox()
        lon_spin.setRange(-180, 180)
        lon_spin.setDecimals(4)
        lon_spin.setSuffix("°")
        layout.addRow("Longitude:", lon_spin)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save new site
            site_data = {
                'name': location_edit.text(),
                'launch_pad': pad_edit.text(),
                'country': country_edit.text(),
                'latitude': lat_spin.value() if lat_spin.value() != 0 else None,
                'longitude': lon_spin.value() if lon_spin.value() != 0 else None,
                'site_type': 'LAUNCH'
            }
            
            try:
                site_id = LaunchSite.objects.create(**site_data)
                
                # Add to combo box
                display = f"{site_data['name']} - {site_data['launch_pad']}"
                self.site_combo.addItem(display, site_id)
                self.site_combo.setCurrentIndex(self.site_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Launch site added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add site: {e}")
    
    def add_new_rocket(self):
        """Open dialog to add a new rocket"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Rocket")
        dialog.setModal(True)
        
        layout = QFormLayout()
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g., Falcon 9 Block 5, Long March 2D")
        layout.addRow("Rocket Name:", name_edit)
        
        family_edit = QLineEdit()
        family_edit.setPlaceholderText("e.g., Falcon, Long March")
        layout.addRow("Family (optional):", family_edit)
        
        variant_edit = QLineEdit()
        variant_edit.setPlaceholderText("e.g., Block 5, CZ-2D")
        layout.addRow("Variant (optional):", variant_edit)
        
        country_edit = QLineEdit()
        country_edit.setPlaceholderText("e.g., USA, China, Russia")
        layout.addRow("Country (optional):", country_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            rocket_name = name_edit.text().strip()
            
            if not rocket_name:
                QMessageBox.warning(self, "Validation Error", "Please enter a rocket name.")
                return
            
            # Save new rocket
            rocket_data = {
                'name': rocket_name,
                'family': family_edit.text().strip() or None,
                'variant': variant_edit.text().strip() or None,
                'country': country_edit.text().strip() or None
            }
            
            try:
                rocket_id = Rocket.objects.create(**rocket_data)
                
                # Add to combo box
                self.rocket_combo.addItem(rocket_name, rocket_id)
                self.rocket_combo.setCurrentIndex(self.rocket_combo.count() - 1)
                
                QMessageBox.information(self, "Success", "Rocket added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add rocket: {e}")
    
    def save_launch(self):
        """Save launch data"""
        
        # Get site_id (if selected from dropdown)
        site_id = self.site_combo.currentData()
        
        # If site was typed in manually, create it
        if site_id is None and self.site_combo.currentText().strip():
            site_text = self.site_combo.currentText().strip()
            # Quick site creation - parse "Location - Pad" format
            parts = site_text.split('-', 1)
            location = parts[0].strip() if parts else site_text
            pad = parts[1].strip() if len(parts) > 1 else "Main Pad"
            
            site_data = {
                'location': location,
                'launch_pad': pad,
                'country': None,
                'latitude': None,
                'longitude': None,
                'site_type': 'LAUNCH'
            }
            
            try:
                LaunchSite.objects.create(**site_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create site: {e}")
                return
        
        # Get rocket_id (if selected from dropdown)
        rocket_id = self.rocket_combo.currentData()
        
        # If rocket was typed in manually, create it
        if rocket_id is None and self.rocket_combo.currentText().strip():
            rocket_name = self.rocket_combo.currentText().strip()
            
            rocket_data = {
                'name': rocket_name,
                'family': None,
                'variant': None,
                'country': None
            }
            
            try:
                rocket_id = Rocket.objects.create(**rocket_data)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create rocket: {e}")
                return
        
        # Validate we have required data
        if site_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a launch site.")
            return
        
        if rocket_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select or enter a rocket.")
            return
        
        launch_data = {
            'launch_date': self.date_edit.date().toString('yyyy-MM-dd'),
            'launch_time': self.time_edit.time().toString('HH:mm:ss'),
            'site_id': site_id,
            'rocket_id': rocket_id,
            'mission_name': self.mission_edit.text(),
            'payload_name': self.payload_edit.text(),
            'orbit_type': self.orbit_combo.currentText(),
            'status_id': self.status_combo.currentData(),
            'notam_reference': None,
            'remarks': self.remarks_edit.toPlainText(),
            'data_source': 'MANUAL'
        }
       
        try:
            with transaction.atomic():
                
                if self.launch_id is not None:
                    launch = Launch.objects.filter(pk=self.launch_id)
                    curr_launch = launch[0]

                    # update fields except NOTAM
                    launch.update(**launch_data)
                    
                    # Update NOTAM entries
                    curr_notam = list(launch[0].notams.all())
                                    
                    user_inputs = []
                    for col in range(self.notam_edit.columnCount()):
                        try:
                            user_inputs.append(self.notam_edit.item(0, col).data(0))
                        except:
                            pass

                    for col in range(len(user_inputs)):
                        new_serial = user_inputs[col]   
                        try:
                            old_serial = curr_notam[col].serial
                        except:
                            old_serial = ""
                        
                        if new_serial != old_serial:
                            if new_serial == "":
                                curr_launch.notams.filter(Q(launch__pk=self.launch_id) & Q(serial=old_serial)).delete()

                                continue
                            
                            curr_launch.notams.filter(Q(launch__pk=self.launch_id) & Q(serial=old_serial)).delete()
                            
                            new_notam = Notam.objects.filter(serial=new_serial).first()
                            
                            launch_notam_data = {"launch_id":curr_launch, "serial": new_notam}
                            
                            LaunchNotam.objects.create(**launch_notam_data)

                    
                    QMessageBox.information(self, "Success", "Launch updated successfully!")
                
                else:
                    curr_launch = Launch.objects.create(**launch_data)
                    
                    user_inputs = []
                    for col in range(self.notam_edit.columnCount()):
                        try:
                            user_inputs.append(self.notam_edit.item(0, col).data(0))
                        except:
                            pass

                    # Update NOTAM entries                    
                    for col in range(len(user_inputs)):
                        new_serial = user_inputs[col]   
                        old_serial = ""
                        
                        if new_serial != old_serial:
                            if new_serial == "":
                                curr_launch.notams.filter(Q(launch__pk=self.launch_id) & Q(serial=old_serial)).delete()

                                continue
                            
                            curr_launch.notams.filter(Q(launch__pk=self.launch_id) & Q(serial=old_serial)).delete()
                            
                            new_notam = Notam.objects.filter(serial=new_serial).first()
                            
                            launch_notam_data = {"launch_id":curr_launch, "serial": new_notam}
                            
                            LaunchNotam.objects.create(**launch_notam_data)

                    QMessageBox.information(self, "Success", "Launch added successfully!")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save launch: {e}")

