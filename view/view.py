"""
Inventory Management System - View
Handles all UI components and user interactions
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QTabWidget, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtGui import QPalette, QColor, QFont, QPixmap
import os
from view.kpi_dashboard import KPIDashboard


class InventoryView(QMainWindow):
    """Main view class for inventory system"""

    # Existing signals
    add_item_signal = pyqtSignal(dict)
    edit_item_signal = pyqtSignal(str, dict)
    delete_item_signal = pyqtSignal(str)
    adjust_stock_signal = pyqtSignal(str, int)
    filter_changed_signal = pyqtSignal()
    refresh_low_stock_signal = pyqtSignal()

    # NEW SIGNALS for suppliers and approvals
    request_stock_signal = pyqtSignal(str, int, str)  # item_name, quantity, reason
    approve_request_signal = pyqtSignal(int, bool, str)  # request_id, approve, notes
    refresh_approvals_signal = pyqtSignal()
    view_suppliers_signal = pyqtSignal()
    add_supplier_signal = pyqtSignal(dict)
    edit_supplier_signal = pyqtSignal(int, dict)
    delete_supplier_signal = pyqtSignal(int)
    place_order_signal = pyqtSignal(dict)
    refresh_activity_log_signal = pyqtSignal()

    def __init__(self, user_role="staff", username="User", db_config=None, order_controller=None):
        super().__init__()
        self.user_role = user_role
        self.username = username
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': '',
            'port': 3308
        }
        self.order_controller = order_controller
        self.setWindowTitle("Inventoria")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_theme()
        self.setup_ui()

    # ---------------------------------------------------------
    # THEME
    # ---------------------------------------------------------
    def setup_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(200, 200, 255))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow { background-color: #ffffff; }
            QWidget { background-color: #ffffff; color: #000000; }
            QTableWidget { background-color: #ffffff; alternate-background-color: #f4f4f4; color: #000000; gridline-color: #cfcfcf; border: 1px solid #cfcfcf; }
            QTableWidget::item:selected { background-color: #c9dcff; }
            QHeaderView::section { background-color: #e6e6e6; color: #000000; padding: 8px; border: 1px solid #d0d0d0; font-weight: bold; }
            QPushButton { background-color: #e6e6e6; color: #000000; border: 1px solid #bfbfbf; padding: 8px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed { background-color: #c0c0c0; }
            
            /* Button Color Classes */
            QPushButton#add_btn { background-color: #4CAF50; color: white; border: 1px solid #45a049; }
            QPushButton#add_btn:hover { background-color: #45a049; }
            QPushButton#add_btn:pressed { background-color: #3d8b40; }
            
            QPushButton#edit_btn { background-color: #2196F3; color: white; border: 1px solid #1976D2; }
            QPushButton#edit_btn:hover { background-color: #1976D2; }
            QPushButton#edit_btn:pressed { background-color: #1565C0; }
            
            QPushButton#delete_btn { background-color: #f44336; color: white; border: 1px solid #d32f2f; }
            QPushButton#delete_btn:hover { background-color: #d32f2f; }
            QPushButton#delete_btn:pressed { background-color: #c62828; }
            
            QPushButton#refresh_btn { background-color: #FF9800; color: white; border: 1px solid #F57C00; }
            QPushButton#refresh_btn:hover { background-color: #F57C00; }
            QPushButton#refresh_btn:pressed { background-color: #E65100; }
            
            QPushButton#report_btn { background-color: #9C27B0; color: white; border: 1px solid #7B1FA2; }
            QPushButton#report_btn:hover { background-color: #7B1FA2; }
            QPushButton#report_btn:pressed { background-color: #6A1B9A; }
            
            QPushButton#logout_btn { background-color: #607D8B; color: white; border: 1px solid #455A64; }
            QPushButton#logout_btn:hover { background-color: #455A64; }
            QPushButton#logout_btn:pressed { background-color: #37474F; }
            

            
            QPushButton#adjust_btn { background-color: #00BCD4; color: white; border: 1px solid #0097A7; }
            QPushButton#adjust_btn:hover { background-color: #0097A7; }
            QPushButton#adjust_btn:pressed { background-color: #00838F; }
            
            QPushButton#request_btn { background-color: #FFC107; color: #000; border: 1px solid #FFA000; }
            QPushButton#request_btn:hover { background-color: #FFA000; }
            QPushButton#request_btn:pressed { background-color: #FF8F00; }
            
            QPushButton#approve_btn { background-color: #8BC34A; color: white; border: 1px solid #689F38; }
            QPushButton#approve_btn:hover { background-color: #689F38; }
            QPushButton#approve_btn:pressed { background-color: #558B2F; }
            
            QPushButton#reject_btn { background-color: #E91E63; color: white; border: 1px solid #C2185B; }
            QPushButton#reject_btn:hover { background-color: #C2185B; }
            QPushButton#reject_btn:pressed { background-color: #AD1457; }
            
            QPushButton#order_btn { background-color: #673AB7; color: white; border: 1px solid #512DA8; }
            QPushButton#order_btn:hover { background-color: #512DA8; }
            QPushButton#order_btn:pressed { background-color: #4527A0; }
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background-color: #ffffff; color: #000000; border: 1px solid #bfbfbf; padding: 6px; border-radius: 3px; }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #7aaaff; }
            QLabel { color: #000000; }
            QTabWidget::pane { border: 1px solid #d0d0d0; background-color: #ffffff; }
            QTabBar::tab { background-color: #e6e6e6; color: #000000; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #ffffff; border-bottom: 2px solid #7aaaff; }
            QTabBar::tab:hover { background-color: #dcdcdc; }
        """)

    # ---------------------------------------------------------
    # MAIN UI
    # ---------------------------------------------------------
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        header = self._create_header()
        main_layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_inventory_tab(), "Inventory")
        self.tabs.addTab(self._create_low_stock_tab(), "Low Stock Alerts")

        # Add Statistics tab only for admin
        if self.user_role == "admin":
            self.tabs.addTab(self._create_stats_tab(), "Statistics")

        # Add suppliers tab for all users
        self.tabs.addTab(self._create_suppliers_tab(), "Suppliers")

        # Add approvals tab only for admin
        if self.user_role == "admin":
            self.tabs.addTab(self._create_approvals_tab(), "Activity Log")

        # Wire KPI dashboard to tabs (kpi_controller wired later by InventoryController)
        if self.user_role == "admin":
            self.kpi_dashboard.set_tabs(self.tabs)

        main_layout.addWidget(self.tabs)

    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------
    def _create_header(self):
        header_widget = QWidget()
        layout = QHBoxLayout(header_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Logo
        logo_label = QLabel()
        logo_path = "inventoria.jpeg"
        possible_paths = [
            logo_path,
            os.path.join(os.path.dirname(__file__), logo_path),
            os.path.expanduser(f"~/Downloads/{logo_path}"),
            os.path.expanduser(f"~/Desktop/{logo_path}")
        ]
        loaded = False
        for path in possible_paths:
            if os.path.exists(path):
                pix = QPixmap(path)
                if not pix.isNull():
                    pix = pix.scaledToHeight(100, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(pix)
                    loaded = True
                    break
        if not loaded:
            logo_label.setText("Inventoria")
            logo_label.setFont(QFont("Arial", 30))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # Title and user info
        title_layout = QVBoxLayout()
        title_label = QLabel("Inventoria")
        title_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        title_label.setStyleSheet("padding: 0px; margin: 0px;")

        # NEW: User role display
        user_info = QLabel(f"{self.username} ({self.user_role.upper()})")
        user_info.setFont(QFont("Arial", 12))
        user_info.setStyleSheet("color: #666; padding: 0px; margin: 0px;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(user_info)

        title_widget = QWidget()
        title_widget.setLayout(title_layout)

        # Create User button (admin only)
        if self.user_role == "admin":
            self.create_user_btn = QPushButton("👤 Create User")
            self.create_user_btn.setObjectName("create_user_btn")
            self.create_user_btn.setFixedHeight(40)
            self.create_user_btn.setFixedWidth(140)
            # Connection will be done in main.py

        # Report button
        self.report_btn = QPushButton("📊 Generate Report")
        self.report_btn.setObjectName("report_btn")
        self.report_btn.setFixedHeight(40)
        self.report_btn.setFixedWidth(160)
        self.report_btn.clicked.connect(self._on_generate_report_clicked)

        # Logout button
        self.logout_btn = QPushButton("🚪 Logout")
        self.logout_btn.setObjectName("logout_btn")
        self.logout_btn.setFixedHeight(40)
        self.logout_btn.setFixedWidth(120)
        # Connection will be done in main.py

        # Add widgets to layout
        layout.addWidget(logo_label)
        layout.addSpacing(15)
        layout.addWidget(title_widget)
        layout.addStretch()
        if self.user_role == "admin":
            layout.addWidget(self.create_user_btn)
        layout.addWidget(self.report_btn)
        layout.addWidget(self.logout_btn)

        return header_widget

    # ---------------------------------------------------------
    # INVENTORY TAB
    # ---------------------------------------------------------
    def _create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by item name...")
        self.search_input.textChanged.connect(self.filter_changed_signal.emit)

        filter_label = QLabel("Category:")
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All", "Linens", "Toiletries", "Cleaning",
            "Kitchen", "Furniture", "Electronics", "Other"
        ])
        self.category_filter.currentTextChanged.connect(self.filter_changed_signal.emit)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(filter_label)
        search_layout.addWidget(self.category_filter)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Table - FIXED: Remove Actions column for admin
        self.inventory_table = QTableWidget()
        if self.user_role == "admin":
            # Admin: 8 columns (without Actions)
            self.inventory_table.setColumnCount(8)
            self.inventory_table.setHorizontalHeaderLabels([
                "Item Name", "Category", "Quantity", "Min Stock",
                "Unit Price", "Total Value", "Supplier", "Status"
            ])
        else:
            # Staff: 9 columns (with Actions for requesting stock)
            self.inventory_table.setColumnCount(9)
            self.inventory_table.setHorizontalHeaderLabels([
                "Item Name", "Category", "Quantity", "Min Stock",
                "Unit Price", "Total Value", "Supplier", "Status", "Actions"
            ])

        # MAKE TABLE READ-ONLY
        self.inventory_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.inventory_table)

        # Buttons - Role-based access control
        button_layout = QHBoxLayout()

        if self.user_role == "admin":
            # ADMIN: Full control - Add, Edit, Delete, Adjust Stock
            add_btn = QPushButton("➕ Add Item")
            add_btn.setObjectName("add_btn")
            edit_btn = QPushButton("✏️ Edit Item")
            edit_btn.setObjectName("edit_btn")
            delete_btn = QPushButton("🗑️ Delete Item")
            delete_btn.setObjectName("delete_btn")
            adjust_btn = QPushButton("📊 Adjust Stock")
            adjust_btn.setObjectName("adjust_btn")

            add_btn.clicked.connect(self._on_add_item_clicked)
            edit_btn.clicked.connect(self._on_edit_item_clicked)
            delete_btn.clicked.connect(self._on_delete_item_clicked)
            adjust_btn.clicked.connect(self._on_adjust_stock_clicked)

            button_layout.addWidget(add_btn)
            button_layout.addWidget(edit_btn)
            button_layout.addWidget(delete_btn)
            button_layout.addWidget(adjust_btn)
        else:
            # STAFF: Can only adjust stock quantities (no add/edit/delete items)
            adjust_btn = QPushButton("📊 Adjust Stock")
            adjust_btn.setObjectName("adjust_btn")
            adjust_btn.clicked.connect(self._on_adjust_stock_clicked)
            button_layout.addWidget(adjust_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)
        return tab

    # ---------------------------------------------------------
    # LOW STOCK TAB
    # ---------------------------------------------------------
    def _create_low_stock_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        label = QLabel("LOW STOCK ALERTS")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setStyleSheet("padding: 10px; color: #ff6600;")
        layout.addWidget(label)

        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(5)
        self.low_stock_table.setHorizontalHeaderLabels([
            "Item Name", "Category", "Current Stock", "Min Stock", "Shortage"
        ])

        # MAKE TABLE READ-ONLY
        self.low_stock_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.low_stock_table.setAlternatingRowColors(True)
        layout.addWidget(self.low_stock_table)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.refresh_low_stock_signal.emit)
        layout.addWidget(refresh_btn)
        return tab

    # ---------------------------------------------------------
    # STATISTICS TAB
    # ---------------------------------------------------------
    def _create_stats_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        label = QLabel("📈 Inventory Statistics")
        label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        label.setStyleSheet("padding: 10px; color: #2C3E50;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Add KPI Dashboard
        self.kpi_dashboard = KPIDashboard(tab)
        layout.addWidget(self.kpi_dashboard)

        # Keep old stats label for compatibility (hidden by default)
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("padding: 20px; font-size: 13px;")
        self.stats_label.setVisible(False)  # Hidden, KPI dashboard replaces it
        layout.addWidget(self.stats_label)

        layout.addStretch()
        return tab

    # ---------------------------------------------------------
    # SUPPLIERS TAB
    # ---------------------------------------------------------
    def _create_suppliers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        label = QLabel("SUPPLIER MANAGEMENT")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setStyleSheet("padding: 10px; color: #2C3E50;")
        layout.addWidget(label)

        # Supplier buttons - Role-based access control
        button_layout = QHBoxLayout()

        if self.user_role == "admin":
            # ADMIN: Full supplier management
            add_supplier_btn = QPushButton("➕ Add Supplier")
            add_supplier_btn.setObjectName("add_btn")
            edit_supplier_btn = QPushButton("✏️ Edit Supplier")
            edit_supplier_btn.setObjectName("edit_btn")
            delete_supplier_btn = QPushButton("🗑️ Delete Supplier")
            delete_supplier_btn.setObjectName("delete_btn")
            place_order_btn = QPushButton("📦 Place Order")
            place_order_btn.setObjectName("order_btn")
            view_orders_btn = QPushButton("📋 View Orders")
            view_orders_btn.setObjectName("refresh_btn")

            add_supplier_btn.clicked.connect(self._on_add_supplier_clicked)
            edit_supplier_btn.clicked.connect(self._on_edit_supplier_clicked)
            delete_supplier_btn.clicked.connect(self._on_delete_supplier_clicked)
            place_order_btn.clicked.connect(self._on_place_order_clicked)
            view_orders_btn.clicked.connect(self._on_view_orders_clicked)

            button_layout.addWidget(add_supplier_btn)
            button_layout.addWidget(edit_supplier_btn)
            button_layout.addWidget(delete_supplier_btn)
            button_layout.addWidget(place_order_btn)
            button_layout.addWidget(view_orders_btn)
        else:
            # STAFF: Can place orders and view them (no supplier management)
            place_order_btn = QPushButton("📦 Place Order")
            place_order_btn.setObjectName("order_btn")
            view_orders_btn = QPushButton("📋 View Orders")
            view_orders_btn.setObjectName("refresh_btn")

            place_order_btn.clicked.connect(self._on_place_order_clicked)
            view_orders_btn.clicked.connect(self._on_view_orders_clicked)

            button_layout.addWidget(place_order_btn)
            button_layout.addWidget(view_orders_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Suppliers table
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(8)
        self.suppliers_table.setHorizontalHeaderLabels([
            "Supplier Name", "Contact Person", "Phone", "Email",
            "Address", "Status", "Items Supplied", "ID"
        ])

        # MAKE TABLE READ-ONLY
        self.suppliers_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Hide the ID column
        self.suppliers_table.setColumnHidden(7, True)

        layout.addWidget(self.suppliers_table)

        return tab

    # ---------------------------------------------------------
    # ACTIVITY LOG TAB (Admin Only) - Shows all staff requests
    # ---------------------------------------------------------
    def _create_approvals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ── Stock Requests Section ──────────────────────────────
        label = QLabel("📋 Stock Requests")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setStyleSheet("padding: 10px; color: #27AE60;")
        layout.addWidget(label)

        self.approvals_table = QTableWidget()
        self.approvals_table.setColumnCount(10)
        self.approvals_table.setHorizontalHeaderLabels([
            "Request ID", "Date", "Staff Name", "Item", "Category",
            "Current Qty", "Requested Qty", "Reason", "Status", "Actions"
        ])
        self.approvals_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.approvals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.approvals_table.setAlternatingRowColors(True)
        layout.addWidget(self.approvals_table)

        refresh_btn = QPushButton("🔄 Refresh Requests")
        refresh_btn.setObjectName("refresh_btn")
        refresh_btn.clicked.connect(self.refresh_approvals_signal.emit)
        layout.addWidget(refresh_btn)

        # ── Activity Log Section ────────────────────────────────
        activity_label = QLabel("Activity Log — Who Did What & When")
        activity_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        activity_label.setStyleSheet("padding: 10px; color: #2980B9; margin-top: 10px;")
        layout.addWidget(activity_label)

        self.activity_log_table = QTableWidget()
        self.activity_log_table.setColumnCount(4)
        self.activity_log_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Details"
        ])
        self.activity_log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.activity_log_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.activity_log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activity_log_table.setAlternatingRowColors(True)
        layout.addWidget(self.activity_log_table)

        refresh_activity_btn = QPushButton("🔄 Refresh Activity Log")
        refresh_activity_btn.clicked.connect(self.refresh_activity_log_signal.emit)
        layout.addWidget(refresh_activity_btn)

        return tab

    # ---------------------------------------------------------
    # TABLE POPULATION
    # ---------------------------------------------------------
    def populate_inventory_table(self, items):
        self.inventory_table.setRowCount(0)
        for item in items:
            row = self.inventory_table.rowCount()
            self.inventory_table.insertRow(row)

            # Common columns (0-6)
            name_item = QTableWidgetItem(item.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 0, name_item)

            category_item = QTableWidgetItem(item.category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 1, category_item)

            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 2, qty_item)

            min_stock_item = QTableWidgetItem(str(item.min_stock))
            min_stock_item.setFlags(min_stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 3, min_stock_item)

            price_item = QTableWidgetItem(f"PHP {item.unit_price:.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 4, price_item)

            value_item = QTableWidgetItem(f"PHP {item.total_value:.2f}")
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 5, value_item)

            supplier_item = QTableWidgetItem(item.supplier)
            supplier_item.setFlags(supplier_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.inventory_table.setItem(row, 6, supplier_item)

            # Status column
            status = "LOW STOCK" if item.is_low_stock else "OK"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if item.is_low_stock:
                status_item.setForeground(QColor("#FF6B6B"))

            if self.user_role == "admin":
                # Admin: Status at column 7, no Actions column
                self.inventory_table.setItem(row, 7, status_item)
            else:
                # Staff: Status at column 7, Actions at column 8
                self.inventory_table.setItem(row, 7, status_item)

                # Actions column - only for staff (Request button)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)

                request_btn = QPushButton("📝 Request")
                request_btn.setObjectName("request_btn")
                request_btn.setFixedSize(90, 25)
                request_btn.clicked.connect(lambda checked, r=row: self._on_request_stock_row(r))
                actions_layout.addWidget(request_btn)

                actions_layout.addStretch()
                self.inventory_table.setCellWidget(row, 8, actions_widget)

            # Highlight low stock rows
            if item.is_low_stock:
                if self.user_role == "admin":
                    for col in range(8):
                        table_item = self.inventory_table.item(row, col)
                        if table_item:
                            table_item.setBackground(QColor(255, 240, 240))
                else:
                    for col in range(8):
                        table_item = self.inventory_table.item(row, col)
                        if table_item:
                            table_item.setBackground(QColor(255, 240, 240))

    def populate_low_stock_table(self, items):
        self.low_stock_table.setRowCount(0)
        for item in items:
            row = self.low_stock_table.rowCount()
            self.low_stock_table.insertRow(row)

            name_item = QTableWidgetItem(item.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.low_stock_table.setItem(row, 0, name_item)

            category_item = QTableWidgetItem(item.category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.low_stock_table.setItem(row, 1, category_item)

            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.low_stock_table.setItem(row, 2, qty_item)

            min_stock_item = QTableWidgetItem(str(item.min_stock))
            min_stock_item.setFlags(min_stock_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.low_stock_table.setItem(row, 3, min_stock_item)

            shortage_item = QTableWidgetItem(str(item.shortage))
            shortage_item.setFlags(shortage_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.low_stock_table.setItem(row, 4, shortage_item)

    def populate_suppliers_table(self, suppliers):
        """Populate suppliers table with data"""
        self.suppliers_table.setRowCount(0)

        if suppliers is None:
            return

        for supplier in suppliers:
            row = self.suppliers_table.rowCount()
            self.suppliers_table.insertRow(row)

            # Store supplier ID in hidden column
            id_item = QTableWidgetItem(str(supplier.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.suppliers_table.setItem(row, 7, id_item)

            # Visible columns
            name_item = QTableWidgetItem(supplier.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.suppliers_table.setItem(row, 0, name_item)

            contact_item = QTableWidgetItem(supplier.contact_person)
            contact_item.setFlags(contact_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.suppliers_table.setItem(row, 1, contact_item)

            phone_item = QTableWidgetItem(supplier.phone)
            phone_item.setFlags(phone_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.suppliers_table.setItem(row, 2, phone_item)

            email_item = QTableWidgetItem(supplier.email)
            email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.suppliers_table.setItem(row, 3, email_item)

            address_text = supplier.address if supplier.address is not None else ""
            if address_text and len(address_text) > 50:
                address_display = address_text[:50] + "..."
            else:
                address_display = address_text

            address_item = QTableWidgetItem(address_display)
            address_item.setFlags(address_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            address_item.setToolTip(address_text)
            self.suppliers_table.setItem(row, 4, address_item)

            status_item = QTableWidgetItem(supplier.status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if supplier.status == 'active':
                status_item.setForeground(QColor('#27AE60'))
            else:
                status_item.setForeground(QColor('#E74C3C'))
            self.suppliers_table.setItem(row, 5, status_item)

            items_text = f"{supplier.items_supplied_count} item(s)"
            if supplier.items_list:
                items_text = f"{supplier.items_supplied_count} item(s)\n{supplier.items_list[:50]}..."
            items_item = QTableWidgetItem(items_text)
            items_item.setFlags(items_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            items_item.setToolTip(supplier.items_list if supplier.items_list else "No items")
            self.suppliers_table.setItem(row, 6, items_item)

    def populate_approvals_table(self, approvals):
        """Populate Activity Log table with staff requests"""
        # FIXED: Only update approvals if the table exists (admin only)
        if not hasattr(self, 'approvals_table'):
            return

        self.approvals_table.setRowCount(0)

        if approvals is None:
            return

        for approval in approvals:
            row = self.approvals_table.rowCount()
            self.approvals_table.insertRow(row)

            # Column 0: Request ID
            id_item = QTableWidgetItem(str(approval.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 0, id_item)

            # Column 1: Date (formatted)
            date_item = QTableWidgetItem(approval.request_date)
            date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 1, date_item)

            # Column 2: Staff Name
            staff_item = QTableWidgetItem(approval.requested_by)
            staff_item.setFlags(staff_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 2, staff_item)

            # Column 3: Item Name
            name_item = QTableWidgetItem(approval.item_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 3, name_item)

            # Column 4: Category
            category_item = QTableWidgetItem(approval.item_category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 4, category_item)

            # Column 5: Current Quantity
            current_qty_item = QTableWidgetItem(str(approval.current_quantity))
            current_qty_item.setFlags(current_qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 5, current_qty_item)

            # Column 6: Requested Quantity
            requested_qty_item = QTableWidgetItem(str(approval.requested_quantity))
            requested_qty_item.setFlags(requested_qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.approvals_table.setItem(row, 6, requested_qty_item)

            # Column 7: Reason
            reason_text = approval.reason[:50] + "..." if len(approval.reason) > 50 else approval.reason
            reason_item = QTableWidgetItem(reason_text)
            reason_item.setFlags(reason_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            reason_item.setToolTip(approval.reason)
            self.approvals_table.setItem(row, 7, reason_item)

            # Column 8: Status with color coding
            status_item = QTableWidgetItem(approval.status.upper())
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Color code the status
            if approval.status == 'pending':
                status_item.setForeground(Qt.GlobalColor.blue)
            elif approval.status == 'approved':
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif approval.status == 'rejected':
                status_item.setForeground(Qt.GlobalColor.red)

            self.approvals_table.setItem(row, 8, status_item)

            # Column 9: Actions - Show buttons ONLY for pending requests
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)

            if approval.status == 'pending':
                # Show Approve/Reject buttons for pending requests
                approve_btn = QPushButton("Approve")
                approve_btn.setObjectName("approve_btn")
                approve_btn.setFixedSize(75, 24)
                approve_btn.clicked.connect(lambda checked, rid=approval.id: self._on_approve_request(rid, True))

                reject_btn = QPushButton("Reject")
                reject_btn.setObjectName("reject_btn")
                reject_btn.setFixedSize(70, 24)
                reject_btn.clicked.connect(lambda checked, rid=approval.id: self._on_approve_request(rid, False))

                actions_layout.addWidget(approve_btn)
                actions_layout.addWidget(reject_btn)
            else:
                # Show who processed it and when
                if approval.approved_by:
                    processed_label = QLabel(f"By: {approval.approved_by}")
                    processed_label.setStyleSheet("font-size: 10px; color: #666;")
                    actions_layout.addWidget(processed_label)

                if approval.approval_date:
                    date_label = QLabel(f"{approval.approval_date}")
                    date_label.setStyleSheet("font-size: 9px; color: #888;")
                    actions_layout.addWidget(date_label)

            actions_layout.addStretch()
            self.approvals_table.setCellWidget(row, 9, actions_widget)

    def populate_activity_log(self, logs):
        """Populate the real activity log table"""
        if not hasattr(self, 'activity_log_table'):
            return

        self.activity_log_table.setRowCount(0)

        if not logs:
            return

        # Action color map
        action_colors = {
            "Added Item":             "#27AE60",
            "Edited Item":            "#2980B9",
            "Deleted Item":           "#E74C3C",
            "Adjusted Stock":         "#8E44AD",
            "Added Supplier":         "#16A085",
            "Edited Supplier":        "#2471A3",
            "Deleted Supplier":       "#C0392B",
            "Placed Order":           "#D35400",
            "Approved Stock Request": "#1E8449",
            "Rejected Stock Request": "#922B21",
        }

        for log in logs:
            row = self.activity_log_table.rowCount()
            self.activity_log_table.insertRow(row)

            # Timestamp
            ts = str(log.get('timestamp', ''))
            ts_item = QTableWidgetItem(ts)
            ts_item.setForeground(QColor("#555555"))
            self.activity_log_table.setItem(row, 0, ts_item)

            # User
            user_item = QTableWidgetItem(log.get('username', ''))
            user_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.activity_log_table.setItem(row, 1, user_item)

            # Action
            action = log.get('action', '')
            action_item = QTableWidgetItem(action)
            color = action_colors.get(action, "#2C3E50")
            action_item.setForeground(QColor(color))
            action_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.activity_log_table.setItem(row, 2, action_item)

            # Details
            details = log.get('details', '')
            details_item = QTableWidgetItem(details)
            details_item.setToolTip(details)
            self.activity_log_table.setItem(row, 3, details_item)

    # ---------------------------------------------------------
    # STATISTICS DISPLAY
    # ---------------------------------------------------------
    def display_statistics(self, stats):
        # Update KPI dashboard if it exists (admin only)
        if hasattr(self, 'kpi_dashboard'):
            self.kpi_dashboard.update_kpis(stats)

        # Keep old stats label updated for compatibility
        if hasattr(self, 'stats_label'):
            stats_text = f"""
            <h3>Overall Statistics</h3>
            <p><b>Total Items:</b> {stats['total_items']}</p>
            <p><b>Total Inventory Value:</b> ₱{stats['total_value']:,.2f}</p>
            <p><b>Low Stock Items:</b> {stats['low_stock_count']}</p>
            <h3>Category Breakdown</h3>
            """
            for cat, count in sorted(stats['categories'].items()):
                stats_text += f"<p><b>{cat}:</b> {count} items</p>"
            self.stats_label.setText(stats_text)

    # ---------------------------------------------------------
    # SIGNAL HELPERS
    # ---------------------------------------------------------
    def get_search_text(self):
        return self.search_input.text()

    def get_category_filter(self):
        return self.category_filter.currentText()

    def get_current_user(self):
        return self.username

    def get_user_role(self):
        return self.user_role

    # ---------------------------------------------------------
    # BUTTON HANDLERS
    # ---------------------------------------------------------
    def _on_add_item_clicked(self):
        from .dialogs import InventoryDialog
        dlg = InventoryDialog(self)
        if dlg.exec():
            self.add_item_signal.emit(dlg.get_data())

    def _on_edit_item_clicked(self):
        row = self.inventory_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select an item to edit.", QMessageBox.Icon.Warning)
            return
        item_name = self.inventory_table.item(row, 0).text()

        supplier_col = 6
        item_data = {
            'name': item_name,
            'category': self.inventory_table.item(row, 1).text(),
            'quantity': int(self.inventory_table.item(row, 2).text()),
            'min_stock': int(self.inventory_table.item(row, 3).text()),
            'unit_price': float(self.inventory_table.item(row, 4).text().replace('PHP', '').replace('₱', '').strip()),
            'supplier': self.inventory_table.item(row, supplier_col).text()
        }

        from .dialogs import InventoryDialog
        dlg = InventoryDialog(self, item_data)
        if dlg.exec():
            self.edit_item_signal.emit(item_name, dlg.get_data())

    def _on_delete_item_clicked(self):
        row = self.inventory_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select an item to delete.", QMessageBox.Icon.Warning)
            return
        item_name = self.inventory_table.item(row, 0).text()
        self.delete_item_signal.emit(item_name)

    def _on_adjust_stock_clicked(self):
        row = self.inventory_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select an item to adjust stock.", QMessageBox.Icon.Warning)
            return
        item_name = self.inventory_table.item(row, 0).text()
        qty = int(self.inventory_table.item(row, 2).text())
        from .dialogs import StockAdjustmentDialog
        dlg = StockAdjustmentDialog(self, item_name, qty)
        if dlg.exec():
            self.adjust_stock_signal.emit(item_name, dlg.get_adjustment())

    def _on_request_stock_clicked(self):
        """Handle request stock button click from main button (staff only)"""
        if self.user_role != "staff":
            self.show_message("Error", "Only staff can request stock.", QMessageBox.Icon.Warning)
            return

        row = self.inventory_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select an item to request stock.", QMessageBox.Icon.Warning)
            return
        self._on_request_stock_row(row)

    def _on_request_stock_row(self, row):
        """Handle request stock from table row (staff only)"""
        if self.user_role != "staff":
            return

        item_name = self.inventory_table.item(row, 0).text()
        current_qty = int(self.inventory_table.item(row, 2).text())

        try:
            from view.supplier_views import StockRequestDialog
            dlg = StockRequestDialog(self, item_name, current_qty)
            if dlg.exec():
                quantity = dlg.get_quantity()
                reason = dlg.get_reason()
                # Emit signal to controller
                self.request_stock_signal.emit(item_name, quantity, reason)
        except ImportError:
            self.show_message("Error", "Stock request dialog not available.", QMessageBox.Icon.Critical)

    def _on_approve_request(self, request_id, approve):
        """Handle approve/reject request from approvals table (admin only)"""
        action = "approve" if approve else "reject"

        # Get notes from user
        notes, ok = QInputDialog.getText(
            self,
            f"{action.capitalize()} Request",
            f"Enter notes for {action} (optional):",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok or True:  # Allow empty notes
            # Emit signal to controller
            self.approve_request_signal.emit(request_id, approve, notes)

    def _on_generate_report_clicked(self):
        """Handle report generation button click"""
        db_config = {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': '',
            'port': 3308
        }
        try:
            from .report_generator import ReportDialog
            dlg = ReportDialog(self, db_config)
            dlg.exec()
        except ImportError as e:
            self.show_message("Error", f"Report module not available: {str(e)}", QMessageBox.Icon.Critical)
        except Exception as e:
            self.show_message("Error", f"Failed to generate report: {str(e)}", QMessageBox.Icon.Critical)

    def _on_add_supplier_clicked(self):
        """Handle add supplier button click"""
        try:
            from view.supplier_views import SupplierDialog
            dlg = SupplierDialog(self)
            if dlg.exec():
                self.add_supplier_signal.emit(dlg.get_data())
        except ImportError:
            self.show_message("Error", "Supplier module not available.", QMessageBox.Icon.Critical)

    def _on_edit_supplier_clicked(self):
        """Handle edit supplier button click"""
        row = self.suppliers_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select a supplier to edit.", QMessageBox.Icon.Warning)
            return

        try:
            supplier_id = int(self.suppliers_table.item(row, 7).text())

            from view.supplier_views import SupplierDialog

            supplier_name = self.suppliers_table.item(row, 0).text()
            contact_person = self.suppliers_table.item(row, 1).text()
            phone = self.suppliers_table.item(row, 2).text()
            email = self.suppliers_table.item(row, 3).text()

            address_item = self.suppliers_table.item(row, 4)
            address = address_item.toolTip() if address_item.toolTip() else address_item.text()

            status = self.suppliers_table.item(row, 5).text()

            supplier_data = {
                'name': supplier_name,
                'contact_person': contact_person,
                'phone': phone,
                'email': email,
                'address': address,
                'status': status,
                'notes': ""
            }

            dlg = SupplierDialog(self, supplier_data)
            if dlg.exec():
                self.edit_supplier_signal.emit(supplier_id, dlg.get_data())

        except ImportError:
            self.show_message("Error", "Supplier module not available.", QMessageBox.Icon.Critical)
        except Exception as e:
            self.show_message("Error", f"Failed to edit supplier: {str(e)}", QMessageBox.Icon.Critical)

    def _on_delete_supplier_clicked(self):
        """Handle delete supplier button click"""
        row = self.suppliers_table.currentRow()
        if row < 0:
            self.show_message("Warning", "Please select a supplier to delete.", QMessageBox.Icon.Warning)
            return

        supplier_id = int(self.suppliers_table.item(row, 7).text())
        self.delete_supplier_signal.emit(supplier_id)

    def _on_place_order_clicked(self):
        """Handle place order button click"""
        try:
            from view.supplier_views import OrderDialog

            dlg = OrderDialog(self, None, "Auto-detect Supplier", self.db_config, self.order_controller)

            if dlg.exec():
                order_data = dlg.get_data()
                self.place_order_signal.emit(order_data)

        except ImportError:
            self.show_message("Error", "Order module not available.", QMessageBox.Icon.Critical)
        except Exception as e:
            self.show_message("Error", f"Failed to place order: {str(e)}", QMessageBox.Icon.Critical)

    def _on_view_orders_clicked(self):
        """Handle view orders button click"""
        try:
            from view.supplier_views import OrdersDialog

            dlg = OrdersDialog(self, self.db_config, self.user_role, self.order_controller)
            dlg.exec()
        except ImportError as e:
            self.show_message("Error", f"Orders dialog not available: {str(e)}", QMessageBox.Icon.Critical)
        except Exception as e:
            self.show_message("Error", f"Failed to open orders: {str(e)}", QMessageBox.Icon.Critical)

    # ---------------------------------------------------------
    # MESSAGE HELPERS
    # ---------------------------------------------------------
    def show_message(self, title, message, icon=QMessageBox.Icon.Information):
        QMessageBox(icon, title, message, QMessageBox.StandardButton.Ok, self).exec()

    def confirm_action(self, title, message):
        reply = QMessageBox.question(self, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes