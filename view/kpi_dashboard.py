"""
Inventoria - KPI Dashboard Widget
Clickable KPI cards that navigate to relevant tabs.
Total Value card opens a full analytics dialog.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QCursor

try:
    from PyQt6.QtCharts import (
        QChart, QChartView, QBarSeries, QBarSet,
        QBarCategoryAxis, QValueAxis, QPieSeries
    )
    from PyQt6.QtCore import QMargins
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ PyQt6-Qt6Charts not installed — charts will be skipped.")


# ---------------------------------------------------------------------------
# Clickable KPI Card
# ---------------------------------------------------------------------------

class KPICard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, value, subtitle="", color="#4CAF50", icon=""):
        super().__init__()
        self._color = color
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style(False)
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 12, 16, 12)

        top_row = QHBoxLayout()
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Arial", 18))
            icon_label.setStyleSheet("border: none; padding: 0; background: transparent;")
            top_row.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color}; border: none; padding: 0; background: transparent;")
        top_row.addWidget(title_label)
        top_row.addStretch()


        layout.addLayout(top_row)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        self.value_label.setStyleSheet("color: #2C3E50; border: none; padding: 0; background: transparent;")
        layout.addWidget(self.value_label)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setFont(QFont("Arial", 9))
            sub.setStyleSheet("color: #7F8C8D; border: none; padding: 0; background: transparent;")
            layout.addWidget(sub)

    def _apply_style(self, hovered):
        bg = "#f0f8ff" if hovered else "white"
        self.setStyleSheet(f"KPICard {{ background-color: {bg}; border: 2px solid {self._color}; border-radius: 10px; }}")

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_value(self, value):
        self.value_label.setText(str(value))


# ---------------------------------------------------------------------------
# Value Analytics Dialog
# ---------------------------------------------------------------------------

class ValueAnalyticsDialog(QDialog):

    def __init__(self, parent, stats, category_data=None):
        super().__init__(parent)
        self.stats = stats or {}
        # category_data is provided by KPIController — no DB query needed here
        self.category_data = category_data or []
        self.setWindowTitle("📊 Total Value Analytics")
        self.setMinimumSize(1000, 750)
        self.resize(1060, 800)
        self.setModal(True)
        self._setup_ui()


    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 16)

        title = QLabel("💰 Inventory Value Analytics")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Summary cards
        total_value = self.stats.get('total_value', 0.0)
        total_items = self.stats.get('total_items', 0)
        low_stock   = self.stats.get('low_stock_count', 0)
        avg_value   = total_value / total_items if total_items > 0 else 0.0

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)
        for lbl_text, val_text, color in [
            ("Total Value",     f"₱{total_value:,.2f}",  "#2ECC71"),
            ("Avg. Item Value", f"₱{avg_value:,.2f}",    "#3498DB"),
            ("Categories",      str(len(self.category_data)), "#9B59B6"),
            ("Low Stock Items", str(low_stock),           "#E74C3C"),
        ]:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: white; border: 2px solid {color}; border-radius: 8px; padding: 8px; }}")
            cl = QVBoxLayout(card)
            cl.setSpacing(4)
            ll = QLabel(lbl_text)
            ll.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            ll.setStyleSheet(f"color: {color}; border: none;")
            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vl = QLabel(val_text)
            vl.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            vl.setStyleSheet("color: #2C3E50; border: none;")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(ll)
            cl.addWidget(vl)
            summary_row.addWidget(card)
        layout.addLayout(summary_row)

        # Charts row
        if CHARTS_AVAILABLE and self.category_data:
            charts_row = QHBoxLayout()
            charts_row.setSpacing(12)

            bar_view = self._build_bar_chart()
            if bar_view:
                bar_view.setMinimumSize(520, 290)
                bar_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                charts_row.addWidget(bar_view, 3)

            pie_view = self._build_pie_chart()
            if pie_view:
                pie_view.setMinimumSize(340, 290)
                pie_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                charts_row.addWidget(pie_view, 2)

            layout.addLayout(charts_row)

        # Breakdown table
        table_label = QLabel("📋 Value Breakdown by Category")
        table_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        table_label.setStyleSheet("color: #2C3E50;")
        layout.addWidget(table_label)

        self._build_table(layout, total_value)

        # Close button
        close_btn = QPushButton("✕  Close")
        close_btn.setFixedWidth(120)
        close_btn.setStyleSheet("""
            QPushButton { background-color: #607D8B; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #455A64; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _build_bar_chart(self):
        try:
            bar_set = QBarSet("Value (PHP)")
            bar_set.setColor(QColor("#3498DB"))
            cat_names = []
            values = []
            for row in self.category_data:
                bar_set.append(row["total_value"])
                cat_names.append(row["category"])
                values.append(row["total_value"])

            series = QBarSeries()
            series.append(bar_set)

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Value by Category (PHP)")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            chart.setBackgroundBrush(QBrush(QColor("white")))
            chart.legend().setVisible(False)
            chart.setMargins(QMargins(10, 10, 10, 10))

            axis_x = QBarCategoryAxis()
            axis_x.append(cat_names)
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            max_val = max(values) if values else 1
            # Round up max to a clean ceiling so bars never get clipped
            import math
            magnitude = 10 ** math.floor(math.log10(max_val))
            nice_max = math.ceil(max_val / magnitude) * magnitude
            axis_y.setRange(0, nice_max)
            axis_y.setTickCount(6)
            axis_y.setLabelFormat("%.0f")
            axis_y.setTitleText("Amount (PHP)")
            axis_y.setTitleVisible(True)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            view = QChartView(chart)
            view.setRenderHint(QPainter.RenderHint.Antialiasing)
            return view
        except Exception as e:
            print(f"Bar chart error: {e}")
            return None

    def _build_pie_chart(self):
        try:
            COLORS = ["#3498DB", "#2ECC71", "#E74C3C", "#9B59B6",
                      "#F39C12", "#1ABC9C", "#E67E22", "#95A5A6"]
            series = QPieSeries()
            series.setHoleSize(0.35)

            for i, row in enumerate(self.category_data):
                if row['total_value'] > 0:
                    sl = series.append(row['category'], row['total_value'])
                    sl.setColor(QColor(COLORS[i % len(COLORS)]))
                    sl.setLabelVisible(False)   # legend shows the names cleanly

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("Distribution")
            chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            chart.setBackgroundBrush(QBrush(QColor("white")))
            chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
            chart.setMargins(QMargins(5, 5, 5, 5))

            view = QChartView(chart)
            view.setRenderHint(QPainter.RenderHint.Antialiasing)
            return view
        except Exception as e:
            print(f"Pie chart error: {e}")
            return None

    def _build_table(self, layout, total_value):
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Category", "Total Value", "% of Total", "Items"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(150)
        table.setMaximumHeight(220)
        table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; }
            QHeaderView::section { background-color: #ecf0f1; font-weight: bold; padding: 6px; }
        """)

        table.setRowCount(len(self.category_data))
        for row_idx, row in enumerate(self.category_data):
            val = row['total_value']
            cnt = row['count']
            pct = (val / total_value * 100) if total_value > 0 else 0.0

            table.setItem(row_idx, 0, QTableWidgetItem(row['category']))
            table.setItem(row_idx, 1, QTableWidgetItem(f"₱{val:,.2f}"))
            table.setItem(row_idx, 2, QTableWidgetItem(f"{pct:.1f}%"))
            table.setItem(row_idx, 3, QTableWidgetItem(str(cnt)))

        layout.addWidget(table)


# ---------------------------------------------------------------------------
# Main KPI Dashboard
# ---------------------------------------------------------------------------

class KPIDashboard(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs           = None
        self._stats          = {}
        self._kpi_controller = None
        self._setup_ui()

    def set_tabs(self, tabs_widget):
        self._tabs = tabs_widget

    def set_kpi_controller(self, kpi_controller):
        self._kpi_controller = kpi_controller

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Key Performance Indicators")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50; padding: 6px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        hint = QLabel("Click any card to navigate or view details")
        hint.setFont(QFont("Arial", 9))
        hint.setStyleSheet("color: #999;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.total_items_card = KPICard("Total Items",     "0",     "All inventory items",  "#3498DB", "📦")
        self.total_value_card = KPICard("Total Value",     "₱0.00", "Click for analytics",  "#2ECC71", "💰")
        self.low_stock_card   = KPICard("Low Stock Items", "0",     "Items below minimum",  "#E74C3C", "⚠️")
        self.categories_card  = KPICard("Categories",      "0",     "Active categories",    "#9B59B6", "🏷️")

        grid.addWidget(self.total_items_card, 0, 0)
        grid.addWidget(self.total_value_card, 0, 1)
        grid.addWidget(self.low_stock_card,   1, 0)
        grid.addWidget(self.categories_card,  1, 1)

        layout.addLayout(grid)
        layout.addStretch()

        self.total_items_card.clicked.connect(self._on_total_items_clicked)
        self.total_value_card.clicked.connect(self._on_total_value_clicked)
        self.low_stock_card.clicked.connect(self._on_low_stock_clicked)
        self.categories_card.clicked.connect(self._on_categories_clicked)

    def _on_total_items_clicked(self):
        if self._tabs:
            self._tabs.setCurrentIndex(0)

    def _on_total_value_clicked(self):
        category_data = []
        if self._kpi_controller:
            category_data = self._kpi_controller.get_category_breakdown()
        dlg = ValueAnalyticsDialog(self, self._stats, category_data)
        dlg.exec()

    def _on_low_stock_clicked(self):
        if self._tabs:
            self._tabs.setCurrentIndex(1)

    def _on_categories_clicked(self):
        if self._tabs:
            for i in range(self._tabs.count()):
                if "statistic" in self._tabs.tabText(i).lower():
                    self._tabs.setCurrentIndex(i)
                    break

    def update_kpis(self, stats):
        if not stats:
            return
        self._stats = stats
        self.total_items_card.set_value(str(stats.get('total_items', 0)))
        self.total_value_card.set_value(f"₱{stats.get('total_value', 0.0):,.2f}")
        self.low_stock_card.set_value(str(stats.get('low_stock_count', 0)))
        self.categories_card.set_value(str(len(stats.get('categories', {}))))