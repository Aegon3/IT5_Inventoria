"""
Inventory Management System - View
Handles all UI components and user interactions
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QTabWidget, QMessageBox, QHeaderView,
    QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt6.QtWidgets import QStyle
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
    damage_report_signal = pyqtSignal(int, str, int, str)  # item_id, item_name, quantity, reason
    stock_issuance_signal = pyqtSignal(int, str, int, str)  # item_id, item_name, quantity, notes

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
        self.setGeometry(60, 60, 1280, 800)
        self.setMinimumSize(1080, 680)
        self.setup_theme()
        self.setup_ui()

    # ---------------------------------------------------------
    # THEME
    # ---------------------------------------------------------
    def setup_theme(self):
        self.setStyleSheet("""
            QMainWindow  { background:#F1F5F9; }
            QWidget      { background:#F1F5F9; color:#0F172A;
                           font-family:'Segoe UI',Arial,sans-serif; font-size:13px; }

            QWidget#sidebar  { background:#0D1117; }
            QWidget#topbar   { background:#FFFFFF; border-bottom:1px solid #E2E8F0; }
            QWidget#content_area { background:#F1F5F9; }
            QStackedWidget   { background:#F1F5F9; }

            QPushButton#nav_btn {
                background:transparent; color:#6B7280; border:none;
                border-radius:9px; padding:9px 14px; text-align:left;
                font-size:13px; font-weight:normal;
            }
            QPushButton#nav_btn:hover   { background:#161B27; color:#D1D5DB; }
            QPushButton#nav_btn:checked { background:rgba(99,102,241,0.15);
                                          color:#A5B4FC; font-weight:600; border-radius:9px; }
            QPushButton#nav_logout {
                background:transparent; color:#F87171; border:none;
                border-radius:9px; padding:9px 14px; text-align:left; font-size:13px;
            }
            QPushButton#nav_logout:hover { background:#161B27; color:#FCA5A5; }

            QTableWidget {
                background:#FFFFFF; alternate-background-color:#FAFAFA;
                color:#0F172A; gridline-color:#F1F5F9;
                border:1px solid #E2E8F0; border-radius:12px; font-size:13px;
            }
            QTableWidget::item          { padding:5px 8px; }
            QTableWidget::item:selected { background:#EEF2FF; color:#1E1B4B; }
            QHeaderView::section {
                background:#F8FAFC; color:#94A3B8; padding:11px 16px;
                border:none; border-bottom:1px solid #E2E8F0;
                font-weight:700; font-size:11px; letter-spacing:0.6px;
            }

            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background:#F8FAFC; color:#0F172A; border:1px solid #E2E8F0;
                border-radius:8px; padding:7px 11px; font-size:13px;
            }
            QComboBox QAbstractItemView {
                background:#FFFFFF; color:#0F172A; border:1px solid #E2E8F0;
                selection-background-color:#EEF2FF; selection-color:#3730A3;
                outline:none; padding:4px;
            }
            QComboBox::drop-down { border:none; }

            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border:1.5px solid #6366F1; background:#FFFFFF;
            }

            QPushButton {
                background:#F8FAFC; color:#475569; border:1px solid #E2E8F0;
                border-radius:8px; padding:8px 16px; font-size:13px; font-weight:500;
            }
            QPushButton:hover   { background:#F1F5F9; }
            QPushButton:pressed { background:#E2E8F0; }

            QPushButton#add_btn    { background:#6366F1; color:#fff; border:none; }
            QPushButton#add_btn:hover { background:#4F46E5; }
            QPushButton#edit_btn   { background:#EEF2FF; color:#3730A3; border:1px solid #C7D2FE; }
            QPushButton#edit_btn:hover { background:#E0E7FF; }
            QPushButton#delete_btn { background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; }
            QPushButton#delete_btn:hover { background:#FEE2E2; }
            QPushButton#refresh_btn { background:#FFFBEB; color:#92400E; border:1px solid #FDE68A; }
            QPushButton#refresh_btn:hover { background:#FEF3C7; }
            QPushButton#report_btn  { background:#F5F3FF; color:#5B21B6; border:1px solid #DDD6FE; }
            QPushButton#report_btn:hover { background:#EDE9FE; }
            QPushButton#adjust_btn  { background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; }
            QPushButton#adjust_btn:hover { background:#DCFCE7; }
            QPushButton#request_btn { background:#FFFBEB; color:#92400E; border:1px solid #FDE68A; }
            QPushButton#request_btn:hover { background:#FEF3C7; }
            QPushButton#approve_btn { background:#F0FDF4; color:#166534; border:1px solid #BBF7D0; }
            QPushButton#approve_btn:hover { background:#DCFCE7; }
            QPushButton#reject_btn  { background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; }
            QPushButton#reject_btn:hover { background:#FEE2E2; }
            QPushButton#order_btn   { background:#EEF2FF; color:#3730A3; border:1px solid #C7D2FE; }
            QPushButton#order_btn:hover { background:#E0E7FF; }
            QPushButton#logout_btn  { background:transparent; color:#F87171; border:none; }
            QPushButton#logout_btn:hover { background:#161B27; }

            QLabel { color:#0F172A; background:transparent; }

            QScrollBar:vertical { background:#F1F5F9; width:6px; border-radius:3px; }
            QScrollBar::handle:vertical { background:#CBD5E1; border-radius:3px; min-height:24px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }

            QTabWidget::pane { border:none; }
            QTabBar::tab { background:transparent; color:transparent;
                           border:none; padding:0; margin:0; width:0; height:0; }
        """)
    # ---------------------------------------------------------
    # MAIN UI
    # ---------------------------------------------------------
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._create_sidebar())

        right = QWidget()
        right.setObjectName("content_area")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._create_topbar())

        self.stack = QStackedWidget()
        self._pages = {}
        idx = 0

        self.stack.addWidget(self._create_inventory_tab())
        self._pages["Inventory"] = idx; idx += 1

        self.stack.addWidget(self._create_low_stock_tab())
        self._pages["Low Stock"] = idx; idx += 1

        if self.user_role == "admin":
            self.stack.addWidget(self._create_stats_tab())
            self._pages["Statistics"] = idx; idx += 1

        self.stack.addWidget(self._create_suppliers_tab())
        self._pages["Suppliers"] = idx; idx += 1

        if self.user_role == "admin":
            self.stack.addWidget(self._create_approvals_tab())
            self._pages["Activity Log"] = idx; idx += 1

        if self.user_role == "staff":
            from view.damage_report_view import create_damage_report_tab
            self.stack.addWidget(create_damage_report_tab(self))
            self._pages["Damage Report"] = idx; idx += 1

        if self.user_role == "staff":
            from view.stock_issuance_view import create_stock_issuance_tab
            self.stack.addWidget(create_stock_issuance_tab(self))
            self._pages["Stock Issuance"] = idx; idx += 1

        rl.addWidget(self.stack)
        root.addWidget(right, 1)

        # Hidden QTabWidget kept for kpi_controller.set_tabs() compatibility
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)
        for name in self._pages:
            self.tabs.addTab(QWidget(), name)
        if self.user_role == "admin":
            self.kpi_dashboard.set_tabs(self.tabs)

        self._connect_nav()
        self._set_btn_icons()

    # ---------------------------------------------------------
    # BUTTON ICONS
    # ---------------------------------------------------------
    def _set_btn_icons(self):
        """Assign QStyle standard icons to all action buttons after UI is built."""
        SP = QStyle.StandardPixmap
        si = self.style().standardIcon
        sz = QSize(16, 16)
        icon_map = {
            "add_btn":     si(SP.SP_FileDialogNewFolder),
            "edit_btn":    si(SP.SP_FileDialogDetailedView),
            "delete_btn":  si(SP.SP_TrashIcon),
            "adjust_btn":  si(SP.SP_FileDialogContentsView),
            "refresh_btn": si(SP.SP_BrowserReload),
            "order_btn":   si(SP.SP_ArrowForward),
            "request_btn": si(SP.SP_MessageBoxQuestion),
            "approve_btn": si(SP.SP_DialogApplyButton),
            "reject_btn":  si(SP.SP_DialogCancelButton),
            "report_btn":  si(SP.SP_FileDialogContentsView),
        }
        for obj_name, icon in icon_map.items():
            for btn in self.findChildren(QPushButton):
                if btn.objectName() == obj_name:
                    btn.setIcon(icon)
                    btn.setIconSize(sz)

    # ---------------------------------------------------------
    # SIDEBAR
    # ---------------------------------------------------------
    def _create_sidebar(self):
        sb = QWidget()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(230)
        lay = QVBoxLayout(sb)
        lay.setContentsMargins(14, 26, 14, 18)
        lay.setSpacing(0)

        # Logo
        # ── Logo block — centered, prominent ───────────────
        logo_col = QVBoxLayout()
        logo_col.setSpacing(8)
        logo_col.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(72, 72)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setScaledContents(False)
        _logo_paths = [
            "inventoria.jpeg",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "inventoria.jpeg"),
            os.path.join(os.path.dirname(__file__), "inventoria.jpeg"),
            os.path.expanduser("~/Downloads/inventoria.jpeg"),
        ]
        _logo_loaded = False
        for _p in _logo_paths:
            if os.path.exists(_p):
                _pix = QPixmap(_p)
                if not _pix.isNull():
                    icon_lbl.setPixmap(_pix.scaled(
                        72, 72,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                    _logo_loaded = True
                    break
        if not _logo_loaded:
            icon_lbl.setText("INV")
            icon_lbl.setStyleSheet(
                "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 #818CF8,stop:1 #6366F1);"
                "border-radius:16px;font-size:18px;font-weight:700;color:#fff;"
            )
        else:
            icon_lbl.setStyleSheet("border-radius:12px;")

        lbl_app = QLabel("Inventoria")
        lbl_app.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_app.setStyleSheet("font-size:15px;font-weight:700;color:#F9FAFB;background:transparent;")
        lbl_sub = QLabel("Hotel Inventory Management")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_sub.setStyleSheet("font-size:10px;color:#4B5563;background:transparent;")

        logo_col.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        logo_col.addWidget(lbl_app)
        logo_col.addWidget(lbl_sub)
        lay.addLayout(logo_col)
        lay.addSpacing(16)

        # User card
        uc = QWidget()
        uc.setStyleSheet(
            "QWidget{background:rgba(255,255,255,0.04);"
            "border:1px solid rgba(255,255,255,0.07);border-radius:12px;}"
        )
        uc_lay = QHBoxLayout(uc)
        uc_lay.setContentsMargins(10, 10, 10, 10)
        uc_lay.setSpacing(10)
        av = QLabel(self.username[0].upper())
        av.setFixedSize(34, 34)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "stop:0 #818CF8,stop:1 #6366F1);"
            "border-radius:17px;font-size:14px;font-weight:700;color:#fff;"
        )
        ui_w = QWidget()
        ui_w.setStyleSheet("background:transparent;")
        ui_col = QVBoxLayout(ui_w)
        ui_col.setContentsMargins(0, 0, 0, 0)
        ui_col.setSpacing(1)
        lbl_un = QLabel(self.username)
        lbl_un.setStyleSheet("font-size:12px;font-weight:600;color:#E5E7EB;background:transparent;")
        lbl_ur = QLabel(self.user_role.capitalize())
        lbl_ur.setStyleSheet("font-size:10px;color:#6B7280;background:transparent;")
        ui_col.addWidget(lbl_un)
        ui_col.addWidget(lbl_ur)
        uc_lay.addWidget(av)
        uc_lay.addWidget(ui_w)
        uc_lay.addStretch()
        lay.addWidget(uc)
        lay.addSpacing(22)

        # Section label
        sec = QLabel("MAIN MENU")
        sec.setStyleSheet("font-size:10px;font-weight:700;color:#374151;letter-spacing:1.2px;background:transparent;padding:0 8px;")
        lay.addWidget(sec)
        lay.addSpacing(6)

        # Nav buttons
        nav_items = self._nav_items()
        self._nav_btns = {}
        for sp_name, label in nav_items:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setIconSize(QSize(16, 16))
            sp = getattr(QStyle.StandardPixmap, sp_name, None)
            if sp:
                btn.setIcon(self.style().standardIcon(sp))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            lay.addWidget(btn)
            lay.addSpacing(2)
            self._nav_btns[label] = btn

        lay.addStretch()

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:rgba(255,255,255,0.06);border:none;max-height:1px;")
        lay.addWidget(div)
        lay.addSpacing(8)

        # Report
        self.report_btn = QPushButton("  Generate Report")
        self.report_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.report_btn.setIconSize(QSize(16, 16))
        self.report_btn.setObjectName("nav_btn")
        self.report_btn.setFixedHeight(40)
        self.report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.report_btn.clicked.connect(self._on_generate_report_clicked)
        lay.addWidget(self.report_btn)
        lay.addSpacing(2)

        # Logout
        self.logout_btn = QPushButton("  Logout")
        self.logout_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        self.logout_btn.setIconSize(QSize(16, 16))
        self.logout_btn.setObjectName("nav_logout")
        self.logout_btn.setFixedHeight(40)
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(self.logout_btn)

        return sb

    def _nav_items(self):
        items = [("SP_FileIcon", "Inventory"), ("SP_MessageBoxWarning", "Low Stock")]
        if self.user_role == "admin":
            items.append(("SP_FileDialogInfoView", "Statistics"))
        items.append(("SP_DriveNetIcon", "Suppliers"))
        if self.user_role == "admin":
            items.append(("SP_FileDialogDetailedView", "Activity Log"))
        if self.user_role == "staff":
            items.append(("SP_MessageBoxCritical", "Damage Report"))
            items.append(("SP_ArrowUp", "Stock Issuance"))
        return items

    def _connect_nav(self):
        def make_fn(label):
            def fn():
                for b in self._nav_btns.values():
                    b.setChecked(False)
                self._nav_btns[label].setChecked(True)
                self.stack.setCurrentIndex(self._pages[label])
                self.tabs.setCurrentIndex(self._pages[label])
                if hasattr(self, '_topbar_title'):
                    self._topbar_title.setText(label)
            return fn
        for label, btn in self._nav_btns.items():
            btn.clicked.connect(make_fn(label))
        first = list(self._nav_btns.keys())[0]
        self._nav_btns[first].setChecked(True)

        # Sync stack when KPI dashboard cards change self.tabs index
        # This allows kpi_dashboard card clicks to navigate the sidebar stack
        def _on_tabs_changed(index):
            self.stack.setCurrentIndex(index)
            # Sync sidebar button highlight
            for label, idx in self._pages.items():
                if idx == index:
                    for b in self._nav_btns.values():
                        b.setChecked(False)
                    if label in self._nav_btns:
                        self._nav_btns[label].setChecked(True)
                    if hasattr(self, '_topbar_title'):
                        self._topbar_title.setText(label)
                    break
        self.tabs.currentChanged.connect(_on_tabs_changed)

    # ---------------------------------------------------------
    # TOPBAR
    # ---------------------------------------------------------
    def _create_topbar(self):
        tb = QWidget()
        tb.setObjectName("topbar")
        tb.setFixedHeight(60)
        lay = QHBoxLayout(tb)
        lay.setContentsMargins(28, 0, 28, 0)
        lay.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self._topbar_title = QLabel("Inventory")
        self._topbar_title.setStyleSheet(
            "font-size:16px;font-weight:700;color:#0F172A;background:transparent;"
        )
        sub = QLabel("Manage your hotel stock")
        sub.setStyleSheet("font-size:11px;color:#94A3B8;background:transparent;")
        title_col.addWidget(self._topbar_title)
        title_col.addWidget(sub)
        lay.addLayout(title_col)
        lay.addStretch()

        if self.user_role == "admin":
            self.view_users_btn = QPushButton("  View Users")
            self.view_users_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
            self.view_users_btn.setIconSize(QSize(16, 16))
            self.view_users_btn.setObjectName("refresh_btn")
            self.view_users_btn.setFixedHeight(34)
            self.view_users_btn.setMinimumWidth(120)
            lay.addWidget(self.view_users_btn)

            self.create_user_btn = QPushButton("  Create User")
            self.create_user_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
            self.create_user_btn.setIconSize(QSize(16, 16))
            self.create_user_btn.setObjectName("edit_btn")
            self.create_user_btn.setFixedHeight(34)
            self.create_user_btn.setMinimumWidth(120)
            lay.addWidget(self.create_user_btn)

        return tb
    # _create_header removed — replaced by _create_sidebar + _create_topbar
    # ---------------------------------------------------------
    # INVENTORY TAB
    # ---------------------------------------------------------
    def _create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Search card
        sc = QWidget()
        sc.setStyleSheet("QWidget{background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;}")
        sc_lay = QHBoxLayout(sc)
        sc_lay.setContentsMargins(14, 0, 14, 0)
        sc_lay.setSpacing(10)
        sc.setFixedHeight(46)
        lbl_s = QLabel("Search")
        lbl_s.setStyleSheet("font-size:12px;color:#94A3B8;background:transparent;font-weight:500;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.setStyleSheet("border:none;background:transparent;font-size:13px;color:#0F172A;padding:0;")
        self.search_input.textChanged.connect(self.filter_changed_signal.emit)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("background:#E2E8F0;border:none;")
        lbl_c = QLabel("Category:")
        lbl_c.setStyleSheet("color:#94A3B8;font-size:12px;background:transparent;")
        self.category_filter = QComboBox()
        self.category_filter.setStyleSheet("QComboBox{border:none;background:transparent;font-size:13px;color:#0F172A;padding:0;}QComboBox QAbstractItemView{background:#FFFFFF;color:#0F172A;border:1px solid #E2E8F0;selection-background-color:#EEF2FF;selection-color:#3730A3;}")
        self.category_filter.addItems(["All","Linens","Toiletries","Cleaning","Kitchen","Furniture","Electronics","Other"])
        self.category_filter.currentTextChanged.connect(self.filter_changed_signal.emit)
        sc_lay.addWidget(lbl_s)
        sc_lay.addWidget(self.search_input, 1)
        sc_lay.addWidget(sep)
        sc_lay.addWidget(lbl_c)
        sc_lay.addWidget(self.category_filter)
        layout.addWidget(sc)

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
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.inventory_table.setAlternatingRowColors(True)
        self.inventory_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.inventory_table)

        # Buttons - Role-based access control
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 4, 0, 0)

        if self.user_role == "admin":
            # ADMIN: Full control - Add, Edit, Delete, Adjust Stock
            add_btn = QPushButton(" Add Item")
            add_btn.setObjectName("add_btn")
            edit_btn = QPushButton(" Edit Item")
            edit_btn.setObjectName("edit_btn")
            delete_btn = QPushButton(" Delete Item")
            delete_btn.setObjectName("delete_btn")
            adjust_btn = QPushButton(" Adjust Stock")
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
            pass

        button_layout.addStretch()

        layout.addLayout(button_layout)
        return tab

    # ---------------------------------------------------------
    # LOW STOCK TAB
    # ---------------------------------------------------------
    def _create_low_stock_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

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

        refresh_btn = QPushButton(" Refresh")
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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        label = QLabel("Inventory Statistics")
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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        label = QLabel("SUPPLIER MANAGEMENT")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setStyleSheet("padding: 10px; color: #2C3E50;")
        layout.addWidget(label)

        # Supplier buttons - Role-based access control
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 4, 0, 0)

        if self.user_role == "admin":
            # ADMIN: Full supplier management
            add_supplier_btn = QPushButton(" Add Supplier")
            add_supplier_btn.setObjectName("add_btn")
            edit_supplier_btn = QPushButton(" Edit Supplier")
            edit_supplier_btn.setObjectName("edit_btn")
            delete_supplier_btn = QPushButton(" Delete Supplier")
            delete_supplier_btn.setObjectName("delete_btn")
            place_order_btn = QPushButton(" Place Order")
            place_order_btn.setObjectName("order_btn")
            view_orders_btn = QPushButton(" View Orders")
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
            place_order_btn = QPushButton(" Place Order")
            place_order_btn.setObjectName("order_btn")
            view_orders_btn = QPushButton(" View Orders")
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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── Stock Requests Section ──────────────────────────────
        label = QLabel("Stock Requests")
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
        self.approvals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.approvals_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.approvals_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.approvals_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.approvals_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)
        self.approvals_table.setColumnWidth(9, 180)
        self.approvals_table.setWordWrap(True)
        self.approvals_table.setAlternatingRowColors(True)
        layout.addWidget(self.approvals_table)

        refresh_btn = QPushButton(" Refresh Requests")
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
        self.activity_log_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.activity_log_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.activity_log_table.setColumnWidth(0, 140)
        self.activity_log_table.setColumnWidth(1, 100)
        self.activity_log_table.setColumnWidth(2, 160)
        self.activity_log_table.setWordWrap(True)
        self.activity_log_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.activity_log_table.setAlternatingRowColors(True)
        layout.addWidget(self.activity_log_table)

        refresh_activity_btn = QPushButton(" Refresh Activity Log")
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
            category_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            _cc={"Linens":("#EEF2FF","#3730A3"),"Toiletries":("#FDF4FF","#7E22CE"),"Cleaning":("#F0FDFA","#134E4A"),"Kitchen":("#FFF7ED","#9A3412"),"Furniture":("#F0F9FF","#0C4A6E"),"Electronics":("#FFFBEB","#92400E"),"Other":("#F9FAFB","#374151")}
            if item.category in _cc:
                category_item.setBackground(QColor(_cc[item.category][0]))
                category_item.setForeground(QColor(_cc[item.category][1]))
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

            # Status column — color pill
            status = "LOW STOCK" if item.is_low_stock else "OK"
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if item.is_low_stock:
                status_item.setForeground(QColor("#991B1B"))
                status_item.setBackground(QColor("#FEE2E2"))
            else:
                status_item.setForeground(QColor("#166534"))
                status_item.setBackground(QColor("#DCFCE7"))

            if self.user_role == "admin":
                # Admin: Status at column 7, no Actions column
                self.inventory_table.setItem(row, 7, status_item)
            else:
                # Staff: Status at column 7, Actions at column 8
                self.inventory_table.setItem(row, 7, status_item)

                # Actions column - only for staff (Request button)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)

                # Set margins to provide padding inside the cell
                actions_layout.setContentsMargins(12, 4, 12, 4)
                actions_layout.setSpacing(0)

                # FIX: Center the button so it doesn't stretch to the cell edges
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                request_btn = QPushButton("Request")
                request_btn.setObjectName("request_btn")

                # FIX: Set a fixed size for a consistent "pill" look
                request_btn.setFixedSize(100, 32)

                request_btn.clicked.connect(lambda checked, r=row: self._on_request_stock_row(r))
                actions_layout.addWidget(request_btn)

                actions_layout.addStretch()
                self.inventory_table.setRowHeight(row, 40)
                self.inventory_table.setCellWidget(row, 8, actions_widget)
                self.inventory_table.setColumnWidth(8, 120)

            # Highlight low stock rows
            if item.is_low_stock:
                if self.user_role == "admin":
                    for col in range(8):
                        table_item = self.inventory_table.item(row, col)
                        if table_item:
                            table_item.setBackground(QColor(255, 252, 252))
                else:
                    for col in range(8):
                        table_item = self.inventory_table.item(row, col)
                        if table_item:
                            table_item.setBackground(QColor(255, 252, 252))

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
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if supplier.status == 'active':
                status_item.setForeground(QColor('#166534'))
                status_item.setBackground(QColor('#DCFCE7'))
            else:
                status_item.setForeground(QColor('#991B1B'))
                status_item.setBackground(QColor('#FEE2E2'))
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
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if approval.status == 'pending':
                status_item.setForeground(QColor('#92400E'))
                status_item.setBackground(QColor('#FEF3C7'))
            elif approval.status == 'approved':
                status_item.setForeground(QColor('#166534'))
                status_item.setBackground(QColor('#DCFCE7'))
            elif approval.status == 'rejected':
                status_item.setForeground(QColor('#991B1B'))
                status_item.setBackground(QColor('#FEE2E2'))

            self.approvals_table.setItem(row, 8, status_item)

            # Column 9: Actions - Show buttons ONLY for pending requests
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 1, 2, 1)
            actions_layout.setSpacing(3)

            if approval.status == 'pending':
                # Show Approve/Reject buttons for pending requests
                approve_btn = QPushButton("Approve")
                approve_btn.setObjectName("approve_btn")
                approve_btn.setFixedSize(80, 26)
                approve_btn.clicked.connect(lambda checked, rid=approval.id: self._on_approve_request(rid, True))

                reject_btn = QPushButton("Reject")
                reject_btn.setObjectName("reject_btn")
                reject_btn.setFixedSize(80, 26)
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

            # Details — full text visible with word wrap
            details = log.get('details', '')
            details_item = QTableWidgetItem(details)
            details_item.setToolTip(details)
            details_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
    # DAMAGE REPORT HELPERS
    # ---------------------------------------------------------
    def load_damage_item_combo(self, items):
        from view.damage_report_view import load_damage_item_combo
        load_damage_item_combo(self, items)

    def populate_damage_table(self, reports):
        from view.damage_report_view import populate_damage_table
        populate_damage_table(self, reports)

    def clear_damage_form(self):
        from view.damage_report_view import clear_damage_form
        clear_damage_form(self)

    # ---------------------------------------------------------
    # STOCK ISSUANCE HELPERS
    # ---------------------------------------------------------
    def load_issuance_item_combo(self, items):
        from view.stock_issuance_view import load_issuance_item_combo
        load_issuance_item_combo(self, items)

    def populate_issuance_table(self, issuances):
        from view.stock_issuance_view import populate_issuance_table
        populate_issuance_table(self, issuances)

    def clear_issuance_form(self):
        from view.stock_issuance_view import clear_issuance_form
        clear_issuance_form(self)

    # ---------------------------------------------------------
    # MESSAGE HELPERS
    # ---------------------------------------------------------
    def show_message(self, title, message, icon=QMessageBox.Icon.Information):
        QMessageBox(icon, title, message, QMessageBox.StandardButton.Ok, self).exec()

    def confirm_action(self, title, message):
        reply = QMessageBox.question(self, title, message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes