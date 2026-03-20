"""
Damage Report - Controller
Handles damage report business logic.
Place in: controller/damage_report_controller.py
"""

from PyQt6.QtWidgets import QMessageBox
from model.damage_report_model import DamageReportModel


class DamageReportController:
    """
    Controller for damage report operations.
    Coordinates between DamageReportModel and the view.

    Usage in main.py:
        damage_ctrl = DamageReportController(inventory_model, view, db_config, username)
    """

    def __init__(self, inventory_model, view, db_config, username):
        self.inventory_model = inventory_model
        self.view = view
        self.db_config = db_config
        self.username = username
        self.damage_model = DamageReportModel(db_config)

        # Create table on init
        self.damage_model.create_table()

        # Connect signal
        self.view.damage_report_signal.connect(self.handle_submit_report)

        # Load initial data
        self.refresh_item_list()
        self.refresh_reports()

    def handle_submit_report(self, item_id, item_name, quantity, reason):
        """Validate and save a damage report submitted by staff"""
        if not item_id:
            self.view.show_message("Warning", "Please select an item.", QMessageBox.Icon.Warning)
            return

        if not reason.strip():
            self.view.show_message("Warning", "Please enter a reason.", QMessageBox.Icon.Warning)
            return

        if quantity <= 0:
            self.view.show_message("Warning", "Quantity must be greater than zero.", QMessageBox.Icon.Warning)
            return

        report_id = self.damage_model.add_report(
            item_id, item_name, quantity, reason.strip(), self.username
        )

        if report_id:
            # Log to activity log
            try:
                self.inventory_model.db.log_action(
                    self.username,
                    "Damage Report",
                    f"Item: {item_name} | Qty: {quantity} | Reason: {reason.strip()}"
                )
            except Exception as e:
                print(f"Activity log error: {e}")

            self.view.show_message(
                "Report Submitted",
                f"Damage report submitted successfully!\n\nItem: {item_name}\nQuantity: {quantity}\nReason: {reason}",
                QMessageBox.Icon.Information
            )
            self.view.clear_damage_form()
            self.refresh_reports()
        else:
            self.view.show_message("Error", "Failed to submit damage report.", QMessageBox.Icon.Critical)

    def refresh_item_list(self):
        """Load inventory items into the damage report item dropdown"""
        try:
            items = self.inventory_model.get_filtered_items()
            self.view.load_damage_item_combo(items)
        except Exception as e:
            print(f"Error refreshing damage item list: {e}")

    def refresh_reports(self):
        """Load damage reports into the damage report table"""
        try:
            reports = self.damage_model.get_all_reports()
            self.view.populate_damage_table(reports)
        except Exception as e:
            print(f"Error refreshing damage reports: {e}")