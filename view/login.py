"""
Inventory Management System - Login Interface
PROFESSIONAL GREY DESIGN - FULLY FIXED VERSION
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QIcon
from PyQt6.QtSvg import QSvgRenderer
import os
from model.database import DatabaseHandler


class LoginWindow(QDialog):
    """Modern professional login with grey palette"""

    def __init__(self, db_config=None):
        super().__init__()
        self.authenticated = False
        self.username = ""
        self.user_data = None
        self.password_visible = False
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': '',
            'port': 3308
        }
        self.setWindowTitle("Inventoria - Login")
        self.setFixedSize(500, 750)
        self.setup_ui()

    def setup_ui(self):
        """Setup beautiful grey UI"""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Apply background gradient
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF
                );
            }
        """)

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(50, 40, 50, 40)
        center_layout.setSpacing(25)

        # Logo
        logo_label = QLabel()
        logo_path = "inventoria.jpeg"
        paths = [
            logo_path,
            os.path.join(os.path.dirname(__file__), logo_path),
            os.path.expanduser("~/Downloads/inventoria.jpeg"),
            os.path.expanduser("~/Desktop/inventoria.jpeg"),
        ]

        logo_loaded = False
        for path in paths:
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(pixmap)
                    logo_loaded = True
                    break

        if not logo_loaded:
            logo_label.setText("📦")
            logo_label.setFont(QFont("Arial", 80))
            logo_label.setStyleSheet("color: #495057;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("margin-bottom: 10px;")
        center_layout.addWidget(logo_label)

        # Title
        title = QLabel("INVENTORIA")
        title.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50; margin: 0; padding: 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        subtitle = QLabel("Inventory Management System")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setStyleSheet("color: #6C757D; margin-bottom: 20px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        # Login card
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(15)

        # Username section
        user_label = QLabel("Username")
        user_label.setFont(QFont("Arial", 11, QFont.Weight.DemiBold))
        user_label.setStyleSheet("color: #495057; background: transparent;")
        card_layout.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                font-size: 14px;
                background: white;
                color: #212529;
            }
            QLineEdit:focus {
                border-color: #6C757D;
                background: white;
            }
        """)
        self.username_input.setFixedHeight(45)
        self.username_input.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.username_input)

        card_layout.addSpacing(10)

        # Password section
        pass_label = QLabel("Password")
        pass_label.setFont(QFont("Arial", 11, QFont.Weight.DemiBold))
        pass_label.setStyleSheet("color: #495057; background: transparent;")
        card_layout.addWidget(pass_label)

        # Password input with toggle button side by side
        password_container = QWidget()
        password_container.setStyleSheet("background: transparent; border: none;")
        password_container.setMinimumHeight(45)  # Ensure container height
        password_layout = QHBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                font-size: 14px;
                background: white;
                color: #212529;
                min-width: 280px;
            }
            QLineEdit:focus {
                border-color: #6C757D;
                background: white;
            }
        """)
        self.password_input.setFixedHeight(45)
        self.password_input.returnPressed.connect(self.handle_login)

        # Toggle button - now properly positioned and clickable
        self.toggle_btn = QPushButton()
        self.toggle_btn.setFixedSize(45, 45)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                padding: 0;
                margin: 0;
                min-width: 45px;
                max-width: 45px;
            }
            QPushButton:hover {
                background: #F8F9FA;
                border-color: #6C757D;
            }
            QPushButton:pressed {
                background: #E9ECEF;
            }
        """)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_password_visibility)
        self.update_toggle_icon()

        password_layout.addWidget(self.password_input, 1)  # Give password input stretch factor
        password_layout.addWidget(self.toggle_btn, 0)  # No stretch for button
        password_layout.setStretch(0, 1)  # Password input gets priority
        password_layout.setStretch(1, 0)  # Button stays fixed

        card_layout.addWidget(password_container)

        card_layout.addSpacing(10)

        # Info box - now with proper text display
        info = QLabel("💡 Default credentials: admin / admin")
        info.setWordWrap(True)
        info.setStyleSheet("""
            QLabel {
                background: #F8F9FA;
                border-left: 4px solid #6C757D;
                padding: 5px 5px;
                border-radius: 4px;
                color: #495057;
                font-size: 12px;
            }
        """)
        card_layout.addWidget(info)

        card_layout.addSpacing(5)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        login_btn = QPushButton("LOGIN")
        login_btn.setStyleSheet("""
            QPushButton {
                background: #495057;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #343A40;
            }
            QPushButton:pressed {
                background: #23272B;
            }
        """)
        login_btn.setFixedHeight(50)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self.handle_login)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ADB5BD;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #868E96;
            }
            QPushButton:pressed {
                background: #6C757D;
            }
        """)
        cancel_btn.setFixedHeight(50)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(cancel_btn)
        card_layout.addLayout(btn_layout)

        center_layout.addWidget(card)

        # Footer
        footer = QLabel("© Bernett's Inventoria System")
        footer.setFont(QFont("Arial", 10))
        footer.setStyleSheet("color: #868E96; margin-top: 15px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(footer)

        center_layout.addStretch()

        layout.addWidget(center_widget)
        self.setLayout(layout)
        self.username_input.setFocus()

    def update_toggle_icon(self):
        """Update the toggle button icon"""
        # Create SVG icon for eye or eye-slash
        if self.password_visible:
            # Eye-slash icon (password visible)
            svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 512" fill="#6C757D">
                <path d="M38.8 5.1C28.4-3.1 13.3-1.2 5.1 9.2S-1.2 34.7 9.2 42.9l592 464c10.4 8.2 25.5 6.3 33.7-4.1s6.3-25.5-4.1-33.7L525.6 386.7c39.6-40.6 66.4-86.1 79.9-118.4c3.3-7.9 3.3-16.7 0-24.6c-14.9-35.7-46.2-87.7-93-131.1C465.5 68.8 400.8 32 320 32c-68.2 0-125 26.3-169.3 60.8L38.8 5.1zm151 118.3C226 97.7 269.5 80 320 80c65.2 0 118.8 29.6 159.9 67.7C518.4 183.5 545 226 558.6 256c-12.6 28-36.6 66.8-70.9 100.9l-53.8-42.2c9.1-17.6 14.2-37.5 14.2-58.7c0-70.7-57.3-128-128-128c-32.2 0-61.7 11.9-84.2 31.5l-46.1-36.1zM394.9 284.2l-81.5-63.9c4.2-8.5 6.6-18.2 6.6-28.3c0-5.5-.7-10.9-2-16c.7 0 1.3 0 2 0c44.2 0 80 35.8 80 80c0 9.9-1.8 19.4-5.1 28.2zm9.4 130.3C378.8 425.4 350.7 432 320 432c-65.2 0-118.8-29.6-159.9-67.7C121.6 328.5 95 286 81.4 256c8.3-18.4 21.5-41.5 39.4-64.8L83.1 161.5C60.3 191.2 44 220.8 34.5 243.7c-3.3 7.9-3.3 16.7 0 24.6c14.9 35.7 46.2 87.7 93 131.1C174.5 443.2 239.2 480 320 480c47.8 0 89.9-12.9 126.2-32.5l-41.9-33zM192 256c0 70.7 57.3 128 128 128c13.3 0 26.1-2 38.2-5.8L302 334c-23.5-5.4-43.1-21.2-53.7-42.3l-56.1-44.2c-.2 2.8-.3 5.6-.3 8.5z"/>
            </svg>'''
        else:
            # Eye icon (password hidden)
            svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512" fill="#6C757D">
                <path d="M288 80c-65.2 0-118.8 29.6-159.9 67.7C89.6 183.5 63 226 49.4 256c13.6 30 40.2 72.5 78.6 108.3C169.2 402.4 222.8 432 288 432s118.8-29.6 159.9-67.7C486.4 328.5 513 286 526.6 256c-13.6-30-40.2-72.5-78.6-108.3C406.8 109.6 353.2 80 288 80zM95.4 112.6C142.5 68.8 207.2 32 288 32s145.5 36.8 192.6 80.6c46.8 43.5 78.1 95.4 93 131.1c3.3 7.9 3.3 16.7 0 24.6c-14.9 35.7-46.2 87.7-93 131.1C433.5 443.2 368.8 480 288 480s-145.5-36.8-192.6-80.6C48.6 356 17.3 304 2.5 268.3c-3.3-7.9-3.3-16.7 0-24.6C17.3 208 48.6 156 95.4 112.6zM288 336c44.2 0 80-35.8 80-80s-35.8-80-80-80c-.7 0-1.3 0-2 0c1.3 5.1 2 10.5 2 16c0 35.3-28.7 64-64 64c-5.5 0-10.9-.7-16-2c0 .7 0 1.3 0 2c0 44.2 35.8 80 80 80zm0-208a128 128 0 1 1 0 256 128 128 0 1 1 0-256z"/>
            </svg>'''

        try:
            # Create pixmap from SVG
            svg_bytes = svg.encode('utf-8')
            from PyQt6.QtCore import QByteArray
            pixmap = QPixmap(20, 20)
            pixmap.fill(Qt.GlobalColor.transparent)

            from PyQt6.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer = QSvgRenderer(QByteArray(svg_bytes))
            renderer.render(painter)
            painter.end()

            icon = QIcon(pixmap)
            self.toggle_btn.setIcon(icon)
            self.toggle_btn.setIconSize(pixmap.size())
        except Exception as e:
            # Fallback to text if SVG fails
            self.toggle_btn.setText("👁" if not self.password_visible else "🙈")

    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.password_visible:
            # Hide password
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_visible = False
        else:
            # Show password
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.password_visible = True

        self.update_toggle_icon()

    def handle_login(self):
        """Handle login"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username:
            self.show_message("Username Required", "Please enter your username.", QMessageBox.Icon.Warning)
            self.username_input.setFocus()
            return

        if not password:
            self.show_message("Password Required", "Please enter your password.", QMessageBox.Icon.Warning)
            self.password_input.setFocus()
            return

        if self.authenticate(username, password):
            self.authenticated = True
            self.username = username

            # Show welcome message with role info
            role = self.user_data.get('role', 'staff').upper()
            full_name = self.user_data.get('full_name', username)

            welcome_msg = f"Welcome, {full_name}!\n\nRole: {role}"

            if role == "ADMIN":
                welcome_msg += "\n\nYou have full system access including:\n• Supplier Management\n• Stock Approvals\n• User Management"
            else:
                welcome_msg += "\n\nYou have staff-level access including:\n• Inventory Management\n• Stock Requests\n• Viewing Reports"

            self.show_message("Login Successful", welcome_msg, QMessageBox.Icon.Information)
            self.accept()
        else:
            error_msg = "Invalid username or password!\n\n"
            error_msg += "Default credentials:\n"
            error_msg += "• Username: admin\n"
            error_msg += "• Password: admin\n\n"


            self.show_message("Login Failed", error_msg, QMessageBox.Icon.Critical)
            self.password_input.clear()
            self.password_input.setFocus()

    def show_message(self, title, message, icon):
        """Show styled message box"""
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
                font-family: Arial;
            }
            QLabel {
                color: #2C3E50;
                font-size: 13px;
                min-width: 300px;
            }
            QPushButton {
                background-color: #495057;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 90px;
                border: none;
            }
            QPushButton:hover {
                background-color: #343A40;
            }
        """)
        msg.exec()

    def authenticate(self, username, password):
        """Authenticate user"""
        try:
            db = DatabaseHandler(**self.db_config)
            if db.connect():
                user = db.authenticate_user(username, password)
                db.disconnect()
                if user:
                    if 'role' not in user:
                        user['role'] = 'staff'
                    self.user_data = user
                    return True
            return False
        except:
            if username == "admin" and password == "admin":
                self.user_data = {'username': 'admin', 'full_name': 'Administrator', 'role': 'admin'}
                return True
            return False

    def get_username(self):
        return self.username

    def get_user_data(self):
        return self.user_data

    def is_authenticated(self):
        return self.authenticated