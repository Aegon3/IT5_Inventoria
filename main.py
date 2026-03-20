import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from view.login import LoginWindow
from model.model import InventoryModel
from view.view import InventoryView
from controller.controller import InventoryController
import traceback


def main():
    """Main application entry point - FIXED with proper logout/login loop"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Arial", 10))

    db_config = {
        'host': 'localhost',
        'database': 'inventoria_db',
        'user': 'root',
        'password': '',
        'port': 3308
    }

    print("=" * 50)
    print("🚀 Starting Inventoria Inventory Management System")
    print("=" * 50)

    # Initialize database
    try:
        from model.database import DatabaseHandler
        db = DatabaseHandler(**db_config)

        if not db.connect():
            QMessageBox.critical(None, "Database Connection Error",
                                 "Failed to connect to database!\n\nCheck MySQL service and credentials.")
            return

        db.create_tables()

        # Check/create default users
        db.cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = 'admin'")
        if db.cursor.fetchone()['count'] == 0:
            db.cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin', 'System Administrator', 'admin')")
            print("✅ Default admin user created")

        db.cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = 'staff'")
        if db.cursor.fetchone()['count'] == 0:
            db.cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES ('staff', 'staff', 'Staff Member', 'staff')")
            print("✅ Default staff user created")

        db.conn.commit()
        db.disconnect()
        print("✅ Database initialization completed")

    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        traceback.print_exc()

    # ========================================================================
    # MAIN LOGIN LOOP - This allows re-login without restarting the process
    # ========================================================================

    while True:  # Keep looping until user exits
        print("-" * 50)
        print("🔐 Starting login process...")

        # Login Window
        login_window = LoginWindow(db_config)
        login_result = login_window.exec()

        if not login_result or not login_window.is_authenticated():
            print("❌ Login cancelled or failed - exiting application")
            break  # Exit the loop and close app

        logged_in_user = login_window.get_username()
        user_data = login_window.get_user_data()
        user_role = user_data.get('role', 'staff')

        print(f"✅ User authenticated: {logged_in_user} ({user_role})")

        # Create model, view, controller
        try:
            print("📦 Initializing inventory model...")
            model = InventoryModel(db_config)

            print("🖼️ Creating view...")
            from controller.order_controller import OrderController
            order_controller = OrderController(db_config)
            view = InventoryView(user_role, logged_in_user, db_config, order_controller)
            view.setWindowTitle(f"Inventoria - {logged_in_user} ({user_role.upper()})")

            print("🎮 Initializing controller...")
            controller_instance = InventoryController(model, view, user_role, logged_in_user)

            print("📊 Loading sample data...")
            model.load_sample_data()

            # Wire Damage Report controller for staff
            if user_role == "staff":
                from controller.damage_report_controller import DamageReportController
                damage_ctrl = DamageReportController(model, view, db_config, logged_in_user)

            # Wire Stock Issuance controller for staff
            if user_role == "staff":
                from controller.stock_issuance_controller import StockIssuanceController
                issuance_ctrl = StockIssuanceController(model, view, db_config, logged_in_user)

            print("✅ MVC setup completed successfully")

        except Exception as e:
            error_msg = f"Failed to initialize application:\n\n{str(e)}\n\nDetailed error:\n{traceback.format_exc()}"
            print(f"❌ INITIALIZATION ERROR:\n{error_msg}")
            QMessageBox.critical(None, "Initialization Error", error_msg)
            break  # Exit on initialization error

        # --- Create User Button Handler (admin only) ---
        if user_role == "admin":
            def open_create_user():
                """Open Create User dialog for admin"""
                try:
                    from view.create_user_dialog import CreateUserDialog
                    from controller.user_controller import UserController

                    user_ctrl = UserController(db_config)
                    create_user_dlg = CreateUserDialog(view, user_controller=user_ctrl)
                    create_user_dlg.exec()

                except Exception as e:
                    QMessageBox.warning(view, "Error", f"Could not open dialog: {str(e)}")
                    print(f"❌ Dialog error: {e}")
                    traceback.print_exc()

            view.create_user_btn.clicked.connect(open_create_user)

            def open_view_users():
                try:
                    from view.create_user_dialog import CreateUserDialog
                    from controller.user_controller import UserController
                    user_ctrl = UserController(db_config)
                    dlg = CreateUserDialog(view, user_controller=user_ctrl)
                    # Switch directly to View All Users tab (index 1)
                    from PyQt6.QtWidgets import QTabWidget
                    tab_widget = dlg.findChild(QTabWidget)
                    if tab_widget:
                        tab_widget.setCurrentIndex(1)
                    dlg.exec()
                except Exception as e:
                    QMessageBox.warning(view, "Error", f"Could not open dialog: {str(e)}")

            view.view_users_btn.clicked.connect(open_view_users)

        # --- Flag to track if we should re-login ---
        should_relogin = [False]  # Using list to allow modification in nested function

        # --- FIXED LOGOUT FUNCTION ---
        def perform_logout():
            """Logout and return to login screen - NO RESTART NEEDED"""
            print(f"🔓 Logout requested by: {logged_in_user}")

            # Show confirmation dialog
            reply = QMessageBox.question(
                view,
                "Confirm Logout",
                f"Are you sure you want to logout, {logged_in_user}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                print(f"👋 Logging out user: {logged_in_user}")

                # Cleanup resources
                try:
                    print("🧹 Cleaning up resources...")
                    controller_instance.cleanup()
                except Exception as e:
                    print(f"⚠️ Cleanup warning: {e}")

                # Close the view
                try:
                    print("🔴 Closing main window...")
                    view.close()
                except Exception as e:
                    print(f"⚠️ Window close warning: {e}")

                # Set flag to re-login
                should_relogin[0] = True
                print("✅ Logout complete - will show login screen")

        # Connect logout button
        print("🔗 Connecting logout button...")
        view.logout_btn.clicked.connect(perform_logout)
        print("✅ Logout functionality connected")

        # Show window and start event loop
        print("🎬 Showing main window...")
        view.show()
        print("✅ Application window displayed!")
        print("=" * 50)

        # Run the event loop for this session
        app.exec()

        # After the window closes, check if we should re-login
        print("-" * 50)
        if should_relogin[0]:
            print("🔄 User logged out - returning to login screen...")
            # Loop will continue and show login window again
            continue
        else:
            print("🛑 Application window closed - exiting...")
            break  # User closed the window, exit the loop

    print("👋 Inventoria shut down successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()