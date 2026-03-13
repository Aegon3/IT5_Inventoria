"""
Inventoria - Create User Dialog (Admin Only)
Allows admin users to create new user accounts and view all existing users
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QFormLayout, QLineEdit, QMessageBox, QHBoxLayout, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class CreateUserDialog(QDialog):
    """Dialog for admin to create new users and view all users"""

    def __init__(self, parent, db=None, user_controller=None):
        super().__init__(parent)
        self.db = db
        self.user_controller = user_controller  # Optional: UserController instance

        self.setWindowTitle("User Management")
        self.setMinimumSize(900, 600)  # Made larger to accommodate user list
        self.setModal(True)

        self.setup_ui()
        self.load_users()  # Load existing users

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("👥 USER MANAGEMENT")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("margin-bottom: 15px; color: #2C3E50;")
        layout.addWidget(title)

        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_new_user_tab(), "➕ Create New User")
        tabs.addTab(self._create_view_users_tab(), "👥 View All Users")
        layout.addWidget(tabs)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        close_btn.setFixedWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _create_new_user_tab(self):
        """Create the tab for adding new users"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Form
        form = QFormLayout()

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username (unique)")
        form.addRow("Username:", self.username_input)

        # Full Name
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Enter full name")
        form.addRow("Full Name:", self.fullname_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm Password:", self.confirm_password_input)

        # Role
        self.role_combo = QComboBox()
        self.role_combo.addItems(["staff", "admin"])
        self.role_combo.setCurrentText("staff")  # Default to staff
        form.addRow("Role:", self.role_combo)

        layout.addLayout(form)

        # Info label
        info_label = QLabel("💡 Tip: Staff can manage inventory, Admin can manage everything including users.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 10px; color: #666; margin-top: 10px;")
        layout.addWidget(info_label)

        layout.addStretch()

        # Create button
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        create_btn = QPushButton("✅ Create User")
        create_btn.clicked.connect(self.create_user)
        create_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        create_btn.setFixedWidth(150)
        btn_row.addWidget(create_btn)

        layout.addLayout(btn_row)

        return tab

    def _create_view_users_tab(self):
        """Create the tab for viewing all users"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Info label
        info_label = QLabel("📋 All registered users in the system:")
        info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Role", "Actions"
        ])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.users_table)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_users)
        refresh_btn.setFixedWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        return tab

    def load_users(self):
        """Load all users from database and display in table"""
        try:
            # Use UserController if available
            if self.user_controller:
                users = self.user_controller.get_all_users()
            else:
                cursor = self.db.cursor(dictionary=True)
                cursor.execute("SELECT id, username, full_name, role FROM users ORDER BY id")
                users = cursor.fetchall()
                cursor.close()

            self.users_table.setRowCount(0)

            for user in users:
                row = self.users_table.rowCount()
                self.users_table.insertRow(row)

                # ID
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))

                # Username
                self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))

                # Full Name
                self.users_table.setItem(row, 2, QTableWidgetItem(user['full_name']))

                # Role with color coding
                role_item = QTableWidgetItem(user['role'].upper())
                if user['role'] == 'admin':
                    role_item.setForeground(Qt.GlobalColor.red)
                else:
                    role_item.setForeground(Qt.GlobalColor.blue)
                self.users_table.setItem(row, 3, role_item)

                # Actions - Delete button (except for default admin/staff)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)

                # Only allow deletion of non-default users
                if user['username'] not in ['admin', 'staff']:
                    delete_btn = QPushButton("🗑️ Delete")
                    delete_btn.setFixedSize(80, 25)
                    delete_btn.setStyleSheet("background-color: #E74C3C; color: white;")
                    delete_btn.clicked.connect(lambda checked, uid=user['id'], uname=user['username']: self.delete_user(uid, uname))
                    actions_layout.addWidget(delete_btn)
                else:
                    protected_label = QLabel("🔒 Protected")
                    protected_label.setStyleSheet("color: #888; font-size: 10px;")
                    actions_layout.addWidget(protected_label)

                actions_layout.addStretch()
                self.users_table.setCellWidget(row, 4, actions_widget)

            print(f"✅ Loaded {len(users)} users")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users:\n{str(e)}")
            print(f"❌ Error loading users: {e}")

    def delete_user(self, user_id, username):
        """Delete a user from the database"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete user '{username}'?\n\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Use UserController if available
            if self.user_controller:
                success, message = self.user_controller.delete_user(user_id, username)
                if success:
                    QMessageBox.information(self, "Success", message)
                    self.load_users()
                else:
                    QMessageBox.critical(self, "Error", message)
            else:
                try:
                    cursor = self.db.cursor()
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                    self.db.commit()
                    cursor.close()
                    QMessageBox.information(self, "Success", f"User '{username}' has been deleted successfully!")
                    print(f"✅ User deleted: {username}")
                    self.load_users()
                except Exception as e:
                    QMessageBox.critical(self, "Database Error", f"Failed to delete user:\n{str(e)}")
                    print(f"❌ Error deleting user: {e}")

    def create_user(self):
        """Validate and create new user"""
        username = self.username_input.text().strip()
        fullname = self.fullname_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        role = self.role_combo.currentText()

        # Use UserController if available
        if self.user_controller:
            success, message = self.user_controller.create_user(
                username, fullname, password, confirm_password, role
            )
            if success:
                QMessageBox.information(self, "Success",
                    f"✅ User created successfully!\n\n"
                    f"Username: {username}\nFull Name: {fullname}\nRole: {role.upper()}\n\n"
                    f"The user can now log in with their credentials.")
                self.username_input.clear()
                self.fullname_input.clear()
                self.password_input.clear()
                self.confirm_password_input.clear()
                self.role_combo.setCurrentText("staff")
                self.load_users()
            else:
                # Check if it's a validation error vs taken username for proper dialog type
                if "already exists" in message:
                    QMessageBox.warning(self, "Username Taken", message)
                elif "cannot be empty" in message or "must be at least" in message or "do not match" in message:
                    QMessageBox.warning(self, "Validation Error", message)
                else:
                    QMessageBox.critical(self, "Database Error", message)
            return

        # Fallback: original direct DB logic
        if not username:
            QMessageBox.warning(self, "Validation Error", "Username cannot be empty!")
            return
        if not fullname:
            QMessageBox.warning(self, "Validation Error", "Full name cannot be empty!")
            return
        if not password:
            QMessageBox.warning(self, "Validation Error", "Password cannot be empty!")
            return
        if password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match!")
            return
        if len(password) < 4:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 4 characters long!")
            return
        if len(username) < 3:
            QMessageBox.warning(self, "Validation Error", "Username must be at least 3 characters long!")
            return

        cursor = None
        try:
            cursor = self.db.cursor(dictionary=True)
            query = "SELECT COUNT(*) as count FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            count = result.get('count') if isinstance(result, dict) else (result[0] if result else 0)

            if count > 0:
                QMessageBox.warning(self, "Username Taken",
                    f"Username '{username}' already exists!\nPlease choose a different username.")
                if cursor: cursor.close()
                return

            insert_query = "INSERT INTO users (username, password, full_name, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (username, password, fullname, role))
            self.db.commit()

            QMessageBox.information(self, "Success",
                f"✅ User created successfully!\n\n"
                f"Username: {username}\nFull Name: {fullname}\nRole: {role.upper()}\n\n"
                f"The user can now log in with their credentials.")
            print(f"✅ New user created: {username} ({role})")

            self.username_input.clear()
            self.fullname_input.clear()
            self.password_input.clear()
            self.confirm_password_input.clear()
            self.role_combo.setCurrentText("staff")
            self.load_users()
            if cursor: cursor.close()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to create user:\n{str(e)}")
            print(f"❌ Error creating user: {e}")
            import traceback
            traceback.print_exc()
            if cursor:
                try: cursor.close()
                except: pass