"""
SHOCKWAVE PLANNER v1.1 - Timeline View
Gantt-chart style launch timeline with grouped launch sites
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                              QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from datetime import datetime
import calendar


class TimelineView(QWidget):
    """Gantt-chart style timeline showing launches across a month"""
    
    launch_selected = pyqtSignal(int)
    
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.show_only_active = True
        self.pad_turnaround_days = 7
        
        # Country groupings
        self.country_groups = {
            'China': ['Jiuquan', 'Taiyuan', 'Xichang', 'Wenchang', 'Dong feng', 'LOP NOR'],
            'USA': ['Cape Canaveral', 'Vandenberg', 'Kennedy', 'Wallops'],
            'Russia': ['Baikonur', 'Plesetsk', 'Vostochny'],
            'Europe': ['Kourou', 'Guiana'],
            'Pacific': ['Mahia', 'Rocket Lab'],
            'India': ['Satish Dhawan'],
            'Japan': ['Tanegashima', 'Uchinoura'],
        }
        
        self.expanded_groups = set(['China'])
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        controls = self.create_controls()
        layout.addLayout(controls)
        
        self.timeline_table = QTableWidget()
        self.timeline_table.verticalHeader().setVisible(True)
        self.timeline_table.setShowGrid(True)
        self.timeline_table.cellClicked.connect(self.cell_clicked)
        
        layout.addWidget(self.timeline_table)
        self.setLayout(layout)
        
        self.update_timeline()
    
    def create_controls(self):
        layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀ Previous Month")
        self.prev_btn.clicked.connect(self.previous_month)
        layout.addWidget(self.prev_btn)
        
        self.month_label = QLabel()
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.month_label.setFont(font)
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.month_label, 1)
        
        self.next_btn = QPushButton("Next Month ▶")
        self.next_btn.clicked.connect(self.next_month)
        layout.addWidget(self.next_btn)
        
        layout.addSpacing(20)
        
        self.active_only_cb = QCheckBox("Show only sites with launches")
        self.active_only_cb.setChecked(True)
        self.active_only_cb.stateChanged.connect(self.toggle_active_only)
        layout.addWidget(self.active_only_cb)
        
        layout.addSpacing(20)
        
        layout.addWidget(QLabel("Pad turnaround (days):"))
        self.turnaround_spin = QSpinBox()
        self.turnaround_spin.setMinimum(0)
        self.turnaround_spin.setMaximum(30)
        self.turnaround_spin.setValue(self.pad_turnaround_days)
        self.turnaround_spin.valueChanged.connect(self.update_turnaround)
        layout.addWidget(self.turnaround_spin)
        
        return layout
    
    def update_timeline(self):
        month_name = calendar.month_name[self.current_month]
        self.month_label.setText(f"{month_name} {self.current_year}")
        
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        launches = self.db.get_launches_by_month(self.current_year, self.current_month)
        
        site_launches = {}
        for launch in launches:
            key = (launch.get('location', ''), launch.get('launch_pad', ''))
            if key not in site_launches:
                site_launches[key] = []
            site_launches[key].append(launch)
        
        rows = []
        for country, locations in self.country_groups.items():
            country_has_launches = False
            country_sites = []
            
            for location in locations:
                location_sites = [s for s in self.db.get_all_sites() 
                                 if s['location'] == location]
                
                for site in location_sites:
                    site_key = (site['location'], site['launch_pad'])
                    has_launches = site_key in site_launches
                    
                    if has_launches or not self.show_only_active:
                        country_sites.append({
                            'type': 'site',
                            'country': country,
                            'location': site['location'],
                            'pad': site['launch_pad'],
                            'site_id': site['site_id'],
                            'launches': site_launches.get(site_key, [])
                        })
                        if has_launches:
                            country_has_launches = True
            
            if country_sites and (country_has_launches or not self.show_only_active):
                rows.append({
                    'type': 'group',
                    'country': country,
                    'expanded': country in self.expanded_groups
                })
                
                if country in self.expanded_groups:
                    rows.extend(country_sites)
        
        self.timeline_table.setRowCount(len(rows))
        self.timeline_table.setColumnCount(3 + days_in_month)
        
        headers = ['LOCATION', 'LAUNCH PAD', 'ROCKET']
        for day in range(1, days_in_month + 1):
            headers.append(str(day))
        self.timeline_table.setHorizontalHeaderLabels(headers)
        
        self.timeline_table.setColumnWidth(0, 120)
        self.timeline_table.setColumnWidth(1, 120)
        self.timeline_table.setColumnWidth(2, 150)
        
        for col in range(3, 3 + days_in_month):
            self.timeline_table.setColumnWidth(col, 30)
        
        for row_idx, row_data in enumerate(rows):
            if row_data['type'] == 'group':
                country = row_data['country']
                expanded = row_data['expanded']
                
                expand_icon = "▼" if expanded else "▶"
                item = QTableWidgetItem(f"{expand_icon} {country}")
                font = item.font()
                font.setBold(True)
                font.setPointSize(10)
                item.setFont(font)
                item.setBackground(QColor(67, 25, 218))
                item.setForeground(Qt.GlobalColor.white) 
                item.setData(Qt.ItemDataRole.UserRole, {'type': 'group', 'country': country})
                
                self.timeline_table.setItem(row_idx, 0, item)
                self.timeline_table.setSpan(row_idx, 0, 1, 3 + days_in_month)
                
            else:
                location_item = QTableWidgetItem(row_data['location'])
                location_item.setBackground(QColor(240, 240, 245))
                self.timeline_table.setItem(row_idx, 0, location_item)
                location_item.setForeground(Qt.GlobalColor.black)
                
                pad_item = QTableWidgetItem(row_data['pad'])
                pad_item.setBackground(QColor(240, 240, 245))
                self.timeline_table.setItem(row_idx, 1, pad_item)
                pad_item.setForeground(Qt.GlobalColor.black)
                
                rockets = set()
                for launch in row_data['launches']:
                    if launch.get('rocket_name'):
                        rockets.add(launch['rocket_name'])
                
                rocket_item = QTableWidgetItem(", ".join(sorted(rockets)[:2]))
                rocket_item.setBackground(QColor(240, 240, 245))
                self.timeline_table.setItem(row_idx, 2, rocket_item)
                rocket_item.setForeground(Qt.GlobalColor.black)
                
                for col_day in range(1, days_in_month + 1):
                    col_idx = 2 + col_day
                    item = QTableWidgetItem("")
                    
                    day_launches = [l for l in row_data['launches'] 
                                   if datetime.strptime(l['launch_date'], '%Y-%m-%d').day == col_day]
                    
                    if day_launches:
                        launch = day_launches[0]
                        status_color = launch.get('status_color', '#FFFF00')
                        item.setBackground(QColor(status_color))
                        item.setText(str(len(day_launches)))
                        item.setData(Qt.ItemDataRole.UserRole, {
                            'type': 'launch',
                            'launch_id': launch['launch_id'],
                            'count': len(day_launches)
                        })
                    else:
                        in_turnaround = False
                        for launch in row_data['launches']:
                            launch_day = datetime.strptime(launch['launch_date'], '%Y-%m-%d').day
                            if launch_day < col_day <= launch_day + self.pad_turnaround_days:
                                in_turnaround = True
                                break
                        
                        if in_turnaround:
                            item.setBackground(QColor(200, 200, 200))
                        else:
                            item.setBackground(QColor(255, 255, 255))
                    
                    self.timeline_table.setItem(row_idx, col_idx, item)
        
        for row in range(len(rows)):
            self.timeline_table.setRowHeight(row, 30)
    
    def cell_clicked(self, row: int, col: int):
        item = self.timeline_table.item(row, col)
        if not item:
            return
        
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        if data.get('type') == 'group':
            country = data['country']
            if country in self.expanded_groups:
                self.expanded_groups.remove(country)
            else:
                self.expanded_groups.add(country)
            self.update_timeline()
        
        elif data.get('type') == 'launch':
            self.launch_selected.emit(data['launch_id'])
    
    def previous_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_timeline()
    
    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_timeline()
    
    def toggle_active_only(self, state):
        self.show_only_active = (state == Qt.CheckState.Checked.value)
        self.update_timeline()
    
    def update_turnaround(self, value):
        self.pad_turnaround_days = value
        self.update_timeline()
