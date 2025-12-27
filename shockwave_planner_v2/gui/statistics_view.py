"""
SHOCKWAVE PLANNER v2.0 - Statistics View
Launch statistics and analytics overview with interactive charts

Author: Remix Astronautics
Date: December 2025
"""
import calendar
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                              QFormLayout, QLabel, QTableWidget,
                              QTableWidgetItem, QHeaderView, QComboBox,
                              QCheckBox, QSpinBox, QPushButton)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from django.db.models import Count
from django.db.models import Q

# import data models
from data.db.models.launch import Launch
from data.db.models.launch_site import LaunchSite
from data.db.models.rocket import Rocket

class StatisticsView(QWidget):
    """Statistics and analytics view for launch data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # 5-Year Launch Overview (at the top)
        curr_yr = datetime.now().year
        date_range = (str(curr_yr-5), str(curr_yr))
        stored_years = Launch.objects.filter(launch_date__year__range=date_range).values("launch_date__year").distinct().reverse()
        stored_years = [yr['launch_date__year'] for yr in stored_years]

        launches_per_yr = Launch.objects.values("launch_date__year").annotate(total=Count("launch_date__year"))
        success_per_yr = Launch.objects.filter(status__name="Success").values("launch_date__year").annotate(total=Count("launch_date__year"))
        fail_per_yr = Launch.objects.filter(Q(status__name="Failure") | Q(status__name="Partial Failure")).values("launch_date__year").annotate(total=Count("launch_date__year"))
        
        yearly_stats = []
        
        for year in stored_years:
            total = launches_per_yr.filter(launch_date__year=year)
            success = success_per_yr.filter(launch_date__year=year)
            fail = fail_per_yr.filter(launch_date__year=year)

            total_count = total[0]["total"] if len(total) > 0 else 0
            success_count = success[0]["total"] if len(success) > 0 else 0
            fail_count = fail[0]["total"] if len(fail) > 0 else 0

            pending_count = total_count - success_count - fail_count

            success_rate = 0
            if success_count + fail_count > 0:
                success_rate = (success_count / (success_count + fail_count)) * 100
            
            yearly_stats.append({
                'year': year,
                'total': total_count,
                'successful': success_count,
                'failed': fail_count,
                'pending': pending_count,
                'success_rate': success_rate
            })      
        
        overview_group = QGroupBox("Launch Statistics - Past 5 Years")
        overview_layout = QVBoxLayout()
        
        # Create table for yearly statistics
        year_table = QTableWidget()
        year_table.setRowCount(len(yearly_stats))
        year_table.setColumnCount(6)
        year_table.setHorizontalHeaderLabels([
            'Year', 'Total', 'Successful', 'Failed', 'Pending', 'Success Rate'
        ])
        year_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        year_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        year_table.setMaximumHeight(200)
        
        for row, year_data in enumerate(yearly_stats):
            # Center-aligned items
            def create_centered_item(text):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                return item
            
            year_table.setItem(row, 0, create_centered_item(year_data['year']))
            year_table.setItem(row, 1, create_centered_item(year_data['total']))
            year_table.setItem(row, 2, create_centered_item(year_data['successful']))
            year_table.setItem(row, 3, create_centered_item(year_data['failed']))
            year_table.setItem(row, 4, create_centered_item(year_data['pending']))
            year_table.setItem(row, 5, create_centered_item(f"{year_data['success_rate']:.1f}%"))
        
        overview_layout.addWidget(year_table)
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Interactive Chart Section
        chart_group = QGroupBox("Interactive Launch Analysis")
        chart_layout = QVBoxLayout()
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # X-Axis Controls
        x_axis_layout = QVBoxLayout()
        x_axis_label = QLabel("Time Period:")
        x_axis_label.setStyleSheet("font-weight: bold;")
        x_axis_layout.addWidget(x_axis_label)
        
        self.time_period_combo = QComboBox()
        self.time_period_combo.addItems([
            "1 Month (days)",
            "3 Months (days)", 
            "12 Months (calendar)"
        ])
        self.time_period_combo.setCurrentIndex(2)  # Default to 12 months
        self.time_period_combo.currentIndexChanged.connect(self.on_time_period_changed)
        x_axis_layout.addWidget(self.time_period_combo)
        
        # Custom months input (for 1 and 3 month options)
        months_input_layout = QHBoxLayout()
        self.months_label = QLabel("Select Month:")
        months_input_layout.addWidget(self.months_label)
        self.month_selector = QComboBox()
        # Populate with months
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        current_month = datetime.now().month
        for i, month in enumerate(month_names, 1):
            self.month_selector.addItem(month, i)
        self.month_selector.setCurrentIndex(current_month - 1)  # Set to current month
        self.month_selector.currentIndexChanged.connect(self.update_chart)
        months_input_layout.addWidget(self.month_selector)
        months_input_layout.addStretch()
        x_axis_layout.addLayout(months_input_layout)
        
        # Month range label (shows the actual date range being plotted)
        self.month_range_label = QLabel("")
        self.month_range_label.setStyleSheet("font-style: italic; color: #666;")
        x_axis_layout.addWidget(self.month_range_label)
        
        # Hide months input by default (shown for 1 and 3 month options)
        self.month_selector.setVisible(False)
        self.months_label.setVisible(False)
        self.month_range_label.setVisible(False)
        
        x_axis_layout.addStretch()
        controls_layout.addLayout(x_axis_layout)
        
        # Y-Axis Controls
        y_axis_layout = QVBoxLayout()
        y_axis_label = QLabel("Filter By:")
        y_axis_label.setStyleSheet("font-weight: bold;")
        y_axis_layout.addWidget(y_axis_label)
        
        # Country selector
        country_layout = QHBoxLayout()
        country_layout.addWidget(QLabel("Country:"))
        self.country_combo = QComboBox()
        self.country_combo.currentIndexChanged.connect(self.on_country_changed)
        country_layout.addWidget(self.country_combo)
        y_axis_layout.addLayout(country_layout)
        
        # Filter type selector (Sites or Rockets)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("View by:"))
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["Launch Sites", "Rockets"])
        self.filter_type_combo.currentIndexChanged.connect(self.on_filter_type_changed)
        filter_layout.addWidget(self.filter_type_combo)
        y_axis_layout.addLayout(filter_layout)
        
        # Specific site/rocket selector
        entity_layout = QHBoxLayout()
        self.entity_label = QLabel("Launch Site:")
        entity_layout.addWidget(self.entity_label)
        self.entity_combo = QComboBox()
        self.entity_combo.currentIndexChanged.connect(self.update_chart)
        entity_layout.addWidget(self.entity_combo)
        y_axis_layout.addLayout(entity_layout)
        
        y_axis_layout.addStretch()
        controls_layout.addLayout(y_axis_layout)
        
        # Year Comparison Controls
        comparison_layout = QVBoxLayout()
        comparison_label = QLabel("Compare with:")
        comparison_label.setStyleSheet("font-weight: bold;")
        comparison_layout.addWidget(comparison_label)
        
        self.prev_year_1_check = QCheckBox("Include previous year")
        self.prev_year_1_check.stateChanged.connect(self.update_chart)
        comparison_layout.addWidget(self.prev_year_1_check)
        
        self.prev_year_2_check = QCheckBox("Include past 2 years")
        self.prev_year_2_check.stateChanged.connect(self.update_chart)
        comparison_layout.addWidget(self.prev_year_2_check)
        
        self.prev_year_3_check = QCheckBox("Include past 3 years")
        self.prev_year_3_check.stateChanged.connect(self.update_chart)
        comparison_layout.addWidget(self.prev_year_3_check)
        
        comparison_layout.addStretch()
        controls_layout.addLayout(comparison_layout)
        
        # Update button
        update_button_layout = QVBoxLayout()
        update_button_layout.addStretch()
        self.update_button = QPushButton("Update Chart")
        self.update_button.clicked.connect(self.update_chart)
        update_button_layout.addWidget(self.update_button)
        update_button_layout.addStretch()
        controls_layout.addLayout(update_button_layout)
        
        chart_layout.addLayout(controls_layout)
        
        # Matplotlib chart
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Initialize data
        self.populate_countries()
        self.populate_entities()
        self.update_chart()
    
    def populate_countries(self):
        """Populate the country dropdown"""
        countries = LaunchSite.objects.values("country").distinct()
        
        self.country_combo.clear()
        self.country_combo.addItem("Global (All Countries)")
        for country in countries:
            if country:  # Only add non-empty country names
                self.country_combo.addItem(country["country"])
    
    def populate_entities(self):
        """Populate launch sites or rockets based on selected country and filter type"""
        self.entity_combo.clear()
        
        country = self.country_combo.currentText()
        if country == "Global (All Countries)":
            country = None
        
        filter_type = self.filter_type_combo.currentText()
        
        if filter_type == "Launch Sites":
            if country is None:
                entities = LaunchSite.objects.values("name").distinct()
            else:
                entities = LaunchSite.objects.filter(country=country).values("name").distinct()
            
            self.entity_combo.addItem("All Sites")
            for entity in entities:
                self.entity_combo.addItem(entity["name"])
        
        else:  # Rockets
            if country is None:
                entities = Rocket.objects.values("name").distinct()
            else:
                entities = Rocket.objects.filter(country=country).values("name").distinct()

            self.entity_combo.addItem("All Rockets")
            for entity in entities:
                self.entity_combo.addItem(entity["name"])
    
    def on_country_changed(self):
        """Handle country selection change"""
        self.populate_entities()
        self.update_chart()
    
    def on_filter_type_changed(self):
        """Handle filter type change (Sites/Rockets)"""
        filter_type = self.filter_type_combo.currentText()
        if filter_type == "Launch Sites":
            self.entity_label.setText("Launch Site:")
        else:
            self.entity_label.setText("Rocket:")
        self.populate_entities()
        self.update_chart()
    
    def on_time_period_changed(self):
        """Handle time period selection change"""
        time_period = self.time_period_combo.currentText()
        
        # Show/hide months input based on selection
        if time_period in ["1 Month (days)", "3 Months (days)"]:
            self.month_selector.setVisible(True)
            self.months_label.setVisible(True)
            self.month_range_label.setVisible(True)
        else:
            self.month_selector.setVisible(False)
            self.months_label.setVisible(False)
            self.month_range_label.setVisible(False)
        
        self.update_chart()
    
    def update_chart(self):
        """Update the chart with current selections"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Get current selections
        time_period = self.time_period_combo.currentText()
        country = self.country_combo.currentText()
        if country == "Global (All Countries)":
            country = None
        
        filter_type = self.filter_type_combo.currentText()
        entity = self.entity_combo.currentText()
        if entity.startswith("All "):
            entity = None
        
        # Get comparison years
        current_year = datetime.now().year
        years_to_plot = [current_year]
        
        if self.prev_year_1_check.isChecked():
            years_to_plot.append(current_year - 1)
        if self.prev_year_2_check.isChecked():
            years_to_plot.append(current_year - 2)
        if self.prev_year_3_check.isChecked():
            years_to_plot.append(current_year - 3)
        
        years_to_plot.sort()
        
        # Determine time granularity
        if time_period == "1 Month (days)" or time_period == "3 Months (days)":
            selected_month = self.month_selector.currentData()  # Get the month number (1-12)
            num_months = 1 if time_period == "1 Month (days)" else 3
            is_daily = True
        else:  # 12 Months (calendar)
            selected_month = None
            num_months = 12
            is_daily = False
        
        # Custom year colors - darkest to lightest (oldest to newest)
        # Map years to colors based on age relative to current year
        current_year = datetime.now().year
        year_colors = {}
        for year in years_to_plot:
            years_ago = current_year - year
            if years_ago == 0:
                year_colors[year] = '#ff3838'  # Current year: RED (bright red like map)
            elif years_ago == 1:
                year_colors[year] = '#ff9500'  # Previous year: ORANGE (bright orange like map)
            elif years_ago == 2:
                year_colors[year] = '#ffb347'  # 2 years ago: LIGHTER ORANGE
            elif years_ago == 3:
                year_colors[year] = '#ffdd00'  # 3 years ago: YELLOW (bright yellow like map)
            else:
                year_colors[year] = '#808080'  # Older: Gray
        
        for idx, year in enumerate(years_to_plot):
            if is_daily:
                # Daily data - pass the selected month
                site = entity if filter_type == "Launch Sites" else None
                rocket = entity if filter_type == "Rockets" else None

                # Calculate date range based on selected month and number of months
                start_date = datetime(year, selected_month, 1)
                
                # Calculate end date
                end_month = selected_month + num_months - 1
                end_year = year
                if end_month > 12:
                    end_month = end_month - 12
                    end_year = year + 1
                
                # Get last day of the end month
                last_day = calendar.monthrange(end_year, end_month)[1]
                end_date = datetime(end_year, end_month, last_day)

                daily_launch_counts = Launch.objects.filter(launch_date__range=(start_date, end_date))                

                if country is not None or site is not None:
                    if country is not None:
                        daily_launch_counts = daily_launch_counts.filter(site__country=country)
                        
                    if site is not None:
                        daily_launch_counts = daily_launch_counts.filter(site__name=site)
                
                if rocket is not None:
                    daily_launch_counts = daily_launch_counts.filter(rocket__name=rocket)

                # get values
                daily_launch_counts = daily_launch_counts.values("launch_date").annotate(Count("launch_date"))
            
                # Create continuous date range with all days
                date_counts = {row["launch_date"].strftime('%Y-%m-%d'): row["launch_date__count"] for row in daily_launch_counts}
                
                dates = []
                counts = []
                current = start_date
                while current <= end_date:
                    date_str = current.strftime('%Y-%m-%d')
                    dates.append(str(current.day))  # Just the day number
                    counts.append(date_counts.get(date_str, 0))
                    current += timedelta(days=1)
                
                # Create date range string for display
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                if num_months == 1:
                    date_range = f"{month_names[selected_month-1]} {year}"
                else:
                    date_range = f"{month_names[selected_month-1]} - {month_names[end_month-1]} {year}"

                # Plot with fewer labels on X-axis (show only day numbers)
                ax.plot(range(len(dates)), counts, marker='o', markersize=3, 
                       label=str(year), color=year_colors[year], linewidth=2)
                
                # Set X-axis to show only day numbers, reduced frequency
                num_ticks = min(len(dates), 15)  # Show max 15 labels
                tick_indices = [i * len(dates) // num_ticks for i in range(num_ticks)]
                ax.set_xticks(tick_indices)
                ax.set_xticklabels([dates[i] for i in tick_indices], rotation=0, fontsize=9)
                
                # Update the month range label
                if idx == 0:  # Only update once
                    self.month_range_label.setText(f"({date_range})")
            else:
                # Monthly data
                site = entity if filter_type == "Launch Sites" else None
                rocket = entity if filter_type == "Rockets" else None

                launch_count_by_mth = Launch.objects

                if country is not None or site is not None:
                    if country is not None:
                        launch_count_by_mth = launch_count_by_mth.filter(site__country=country)

                    if site is not None:
                        launch_count_by_mth = launch_count_by_mth.filter(site__name=site)
                                
                if rocket is not None:
                    launch_count_by_mth = launch_count_by_mth.filter(rocket__name=rocket)

                if entity is not None:
                    launch_count_by_mth = launch_count_by_mth.filter(site__name=entity)
                
                launch_count_by_mth = launch_count_by_mth.values("launch_date__month").annotate(Count("launch_date__month")) 

                month_counts = {int(row['launch_date__month']): row["launch_date__month__count"] for row in launch_count_by_mth}
                months = list(range(1, 13))
                counts = [month_counts.get(m, 0) for m in months]

                month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                ax.plot(months, counts, marker='o', markersize=5,
                       label=str(year), color=year_colors[year], linewidth=2)
                ax.set_xticks(range(1, 13))
                ax.set_xticklabels(month_labels)
        
        # Dark theme chart styling
        # Set dark background colors
        self.figure.patch.set_facecolor('#0f0f1e')  # Dark background (like map)
        ax.set_facecolor('#1a1a2e')  # Dark plot area (like map ocean)
        
        # No title - clean look (like map)
        
        # Axis labels in purple (matching tick colors and grid)
        ax.set_xlabel('Time Period', fontsize=11, color='#533483')
        ax.set_ylabel('Number of Launches', fontsize=11, color='#533483')
        
        # Legend with dark theme
        legend = ax.legend(loc='best', facecolor='#1a1a2e', edgecolor='#533483', 
                          framealpha=0.9, labelcolor='white')
        legend.get_frame().set_linewidth(1.5)
        
        # Grid in subtle purple (like map)
        ax.grid(True, alpha=0.3, color='#533483', linewidth=0.5)
        
        # Tick colors in purple (like map coordinates)
        ax.tick_params(colors='#533483', which='both')
        
        # Spine colors in purple
        for spine in ax.spines.values():
            spine.set_edgecolor('#533483')
            spine.set_linewidth(1)
        
        # Set integer y-axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def refresh(self):
        """Refresh the statistics display"""
        # Delete the old layout properly
        old_layout = self.layout()
        if old_layout:
            # Remove all widgets from layout
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Delete the layout itself
            QWidget().setLayout(old_layout)
        
        # Rebuild the UI with fresh data
        self.init_ui()
