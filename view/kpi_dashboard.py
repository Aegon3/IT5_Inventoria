"""
Inventoria - KPI Dashboard Widget
Simple, clean KPI display with accurate system data
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class KPICard(QFrame):
    """Single KPI card widget"""

    def __init__(self, title, value, subtitle="", color="#4CAF50"):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #f9f9f9;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; border: none; padding: 0;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(str(value))
        value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #2C3E50; border: none; padding: 0;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # Subtitle (optional)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("Arial", 9))
            subtitle_label.setStyleSheet("color: #7F8C8D; border: none; padding: 0;")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(subtitle_label)


class KPIDashboard(QWidget):
    """Main KPI Dashboard Widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the KPI dashboard UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Key Performance Indicators")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # KPI Grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(15)

        # Initialize with placeholder values
        self.total_items_card = KPICard("Total Items", "0", "", "#3498DB")
        self.total_value_card = KPICard("Total Value", "₱0.00", "", "#2ECC71")
        self.low_stock_card = KPICard("Low Stock Items", "0", "", "#E74C3C")
        self.categories_card = KPICard("Categories", "0", "", "#9B59B6")

        # Add cards to grid (2x2)
        kpi_grid.addWidget(self.total_items_card, 0, 0)
        kpi_grid.addWidget(self.total_value_card, 0, 1)
        kpi_grid.addWidget(self.low_stock_card, 1, 0)
        kpi_grid.addWidget(self.categories_card, 1, 1)

        layout.addLayout(kpi_grid)
        layout.addStretch()

    def update_kpis(self, stats):
        """Update KPI cards with new statistics

        Args:
            stats (dict): Statistics dictionary with keys:
                - total_items (int)
                - total_value (float)
                - low_stock_count (int)
                - categories (dict)
        """
        if not stats:
            return

        # Update Total Items
        total_items = stats.get('total_items', 0)
        value_labels = [child for child in self.total_items_card.findChildren(QLabel)
                        if child.font().pointSize() == 28]
        if value_labels:
            value_labels[0].setText(str(total_items))

        # Update Total Value
        total_value = stats.get('total_value', 0.0)
        value_labels = [child for child in self.total_value_card.findChildren(QLabel)
                        if child.font().pointSize() == 28]
        if value_labels:
            value_labels[0].setText(f"₱{total_value:,.2f}")

        # Update Low Stock Count
        low_stock = stats.get('low_stock_count', 0)
        value_labels = [child for child in self.low_stock_card.findChildren(QLabel)
                        if child.font().pointSize() == 28]
        if value_labels:
            value_labels[0].setText(str(low_stock))

        # Update Categories Count
        categories = stats.get('categories', {})
        cat_count = len(categories)
        value_labels = [child for child in self.categories_card.findChildren(QLabel)
                        if child.font().pointSize() == 28]
        if value_labels:
            value_labels[0].setText(str(cat_count))