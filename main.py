import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from view.login import LoginWindow
from model.model import InventoryModel
from model.database import DatabaseHandler
from view.view import InventoryView
from controller.controller import InventoryController
import traceback


def main():
    """Main application entry point - FIXED for refactored models"""
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
    print(" Starting Inventoria Inventory Management System")
    print("=" * 50)

    # Initialize database
    try:
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
            print(" Default admin user created")

        db.cursor.execute("SELECT COUNT(*) as count FROM users WHERE username = 'staff'")
        if db.cursor.fetchone()['count'] == 0:
            db.cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES ('staff', 'staff', 'Staff Member', 'staff')")
            print(" Default staff user created")

        db.conn.commit()
        db.disconnect()
        print(" Database initialization completed")

    except Exception as e:
        print(f" Database initialization warning: {e}")
        traceback.print_exc()

    # ========================================================================
    # MAIN LOGIN LOOP - This allows re-login without restarting the process
    # ========================================================================

    while True:
        print("-" * 50)
        print(" Starting login process...")

        # Login Window
        login_window = LoginWindow(db_config)
        login_result = login_window.exec()

        if not login_result or not login_window.is_authenticated():
            print(" Login cancelled or failed - exiting application")
            break

        logged_in_user = login_window.get_username()
        user_data = login_window.get_user_data()
        user_role = user_data.get('role', 'staff')

        print(f" User authenticated: {logged_in_user} ({user_role})")

        # Create model, view, controller
        try:
            print(" Initializing inventory model...")
            # FIXED: InventoryModel no longer accepts db_config
            model = InventoryModel()

            # Create database handler and attach to model
            db_handler = DatabaseHandler(**db_config)
            if not db_handler.connect():
                raise Exception("Failed to connect to database")

            # Set the database handler on the model
            model.db = db_handler

            print(" Creating view...")
            from controller.order_controller import OrderController
            order_controller = OrderController(db_config)
            view = InventoryView(user_role, logged_in_user, order_controller)
            view.setWindowTitle(f"Inventoria - {logged_in_user} ({user_role.upper()})")

            print(" Initializing controller...")
            controller_instance = InventoryController(model, view, user_role, logged_in_user, db_config)

            # Load sample data using db_handler directly
            stats = db_handler.get_statistics()
            if stats['total_items'] == 0:
                print(" Loading sample data...")
                sample_data = [
                    ["Bed Sheets (Queen)", "Linens", 150, 100, 1375.00, "Linen Supply Co"],
                    ["Towels (Bath)", "Linens", 300, 200, 687.50, "Linen Supply Co"],
                    ["Shampoo Bottles", "Toiletries", 80, 150, 206.25, "Hospitality Goods Inc"],
                    ["Soap Bars", "Toiletries", 500, 300, 68.75, "Hospitality Goods Inc"],
                    ["Toilet Paper Rolls", "Toiletries", 1000, 800, 41.25, "Paper Products LLC"],
                    ["Cleaning Spray", "Cleaning", 45, 50, 467.50, "CleanPro Supplies"],
                    ["Vacuum Bags", "Cleaning", 30, 40, 825.00, "CleanPro Supplies"],
                    ["Coffee Pods", "Kitchen", 200, 150, 27.50, "Hotel Food Service"],
                    ["Dinner Plates", "Kitchen", 250, 200, 440.00, "Restaurant Supply Co"],
                    ["TV Remote Batteries", "Electronics", 100, 80, 137.50, "Electronics Depot"]
                ]
                for data in sample_data:
                    db_handler.add_item(*data)
                print(" Sample data loaded successfully!")

            # Wire Damage Report controller for staff
            if user_role == "staff":
                from controller.damage_report_controller import DamageReportController
                damage_ctrl = DamageReportController(model, view, db_config, logged_in_user)

            # Wire Stock Issuance controller for staff
            if user_role == "staff":
                from controller.stock_issuance_controller import StockIssuanceController
                issuance_ctrl = StockIssuanceController(model, view, db_config, logged_in_user)

            print(" MVC setup completed successfully")

        except Exception as e:
            error_msg = f"Failed to initialize application:\n\n{str(e)}\n\nDetailed error:\n{traceback.format_exc()}"
            print(f" INITIALIZATION ERROR:\n{error_msg}")
            QMessageBox.critical(None, "Initialization Error", error_msg)
            break

        # --- Create User Button Handler (admin only) ---
        if user_role == "admin":
            def open_create_user():
                try:
                    from view.create_user_dialog import CreateUserDialog
                    from controller.user_controller import UserController

                    user_ctrl = UserController(db_config)
                    create_user_dlg = CreateUserDialog(view, user_controller=user_ctrl)
                    create_user_dlg.exec()

                except Exception as e:
                    QMessageBox.warning(view, "Error", f"Could not open dialog: {str(e)}")
                    print(f" Dialog error: {e}")
                    traceback.print_exc()

            view.create_user_btn.clicked.connect(open_create_user)

            def open_view_users():
                try:
                    from view.create_user_dialog import CreateUserDialog
                    from controller.user_controller import UserController
                    user_ctrl = UserController(db_config)
                    dlg = CreateUserDialog(view, user_controller=user_ctrl)
                    from PyQt6.QtWidgets import QTabWidget
                    tab_widget = dlg.findChild(QTabWidget)
                    if tab_widget:
                        tab_widget.setCurrentIndex(1)
                    dlg.exec()
                except Exception as e:
                    QMessageBox.warning(view, "Error", f"Could not open dialog: {str(e)}")

            view.view_users_btn.clicked.connect(open_view_users)

        # --- Flag to track if we should re-login ---
        should_relogin = [False]

        # --- FIXED LOGOUT FUNCTION ---
        def perform_logout():
            print(f" Logout requested by: {logged_in_user}")

            reply = QMessageBox.question(
                view,
                "Confirm Logout",
                f"Are you sure you want to logout, {logged_in_user}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                print(f" Logging out user: {logged_in_user}")

                try:
                    print(" Cleaning up resources...")
                    controller_instance.cleanup()
                except Exception as e:
                    print(f" Cleanup warning: {e}")

                try:
                    print(" Closing main window...")
                    view.close()
                except Exception as e:
                    print(f" Window close warning: {e}")

                should_relogin[0] = True
                print(" Logout complete - will show login screen")

        print(" Connecting logout button...")
        view.logout_btn.clicked.connect(perform_logout)
        print(" Logout functionality connected")

        print(" Showing main window...")
        view.show()
        print(" Application window displayed!")
        print("=" * 50)

        app.exec()

        print("-" * 50)
        if should_relogin[0]:
            print(" User logged out - returning to login screen...")
            continue
        else:
            print(" Application window closed - exiting...")
            break

    print(" Inventoria shut down successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()