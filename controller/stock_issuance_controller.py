"""
Stock Issuance - Controller
Handles stock issuance business logic.
Place in: controller/stock_issuance_controller.py
"""

from PyQt6.QtWidgets import QMessageBox
from model.stock_issuance_model import StockIssuanceModel


class StockIssuanceController:
    """
    Controller for stock issuance operations.
    Coordinates between StockIssuanceModel and the view.

    Usage in main.py:
        issuance_ctrl = StockIssuanceController(inventory_model, view, db_config, username)
    """

    def __init__(self, inventory_model, view, db_config, username):
        self.inventory_model = inventory_model
        self.view = view
        self.db_config = db_config
        self.username = username
        self.issuance_model = StockIssuanceModel(db_config)

        # Create table on init
        self.issuance_model.create_table()

        # Connect signal
        self.view.stock_issuance_signal.connect(self.handle_issue_stock)

        # Load initial data
        self.refresh_item_list()
        self.refresh_issuances()

    def handle_issue_stock(self, item_id, item_name, quantity, notes):
        """Validate and process a stock issuance"""

        if not item_id:
            self.view.show_message("Warning", "Please select an item.", QMessageBox.Icon.Warning)
            return

        if quantity <= 0:
            self.view.show_message("Warning", "Quantity must be greater than zero.", QMessageBox.Icon.Warning)
            return

        # Check if enough stock is available
        current_stock = self.issuance_model.get_current_stock(item_id)
        if quantity > current_stock:
            self.view.show_message(
                "Insufficient Stock",
                f"Cannot issue {quantity} units of {item_name}.\n\nCurrent stock: {current_stock}",
                QMessageBox.Icon.Warning
            )
            return

        # Deduct stock first
        deducted = self.issuance_model.deduct_stock(item_id, quantity)
        if not deducted:
            self.view.show_message("Error", "Failed to deduct stock. Please try again.", QMessageBox.Icon.Critical)
            return

        # Record the issuance
        issuance_id = self.issuance_model.add_issuance(
            item_id, item_name, quantity, self.username, notes
        )

        if issuance_id:
            # Log to activity log
            try:
                self.inventory_model.db.log_action(
                    self.username,
                    "Stock Issuance",
                    f"Item: {item_name} | Qty: {quantity} | Notes: {notes}"
                )
            except Exception as e:
                print(f"Activity log error: {e}")

            # Refresh inventory view to reflect deducted stock
            self.inventory_model.notify_observers()

            self.view.show_message(
                "Stock Issued",
                f"Stock issued successfully!\n\nItem: {item_name}\nQuantity: {quantity}",
                QMessageBox.Icon.Information
            )
            self.view.clear_issuance_form()
            self.refresh_issuances()
            self.refresh_item_list()
        else:
            self.view.show_message("Error", "Failed to record issuance.", QMessageBox.Icon.Critical)

    def refresh_item_list(self):
        """Load inventory items into the issuance item dropdown"""
        try:
            items = self.inventory_model.get_filtered_items()
            self.view.load_issuance_item_combo(items)
        except Exception as e:
            print(f"Error refreshing issuance item list: {e}")

    def refresh_issuances(self):
        """Load issuance records into the issuance table"""
        try:
            issuances = self.issuance_model.get_all_issuances()
            self.view.populate_issuance_table(issuances)
        except Exception as e:
            print(f"Error refreshing issuances: {e}")