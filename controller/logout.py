"""
Inventory Management System - Controller with Logout / Login Loop
"""

from PyQt6.QtWidgets import QMessageBox
from view.login import LoginWindow
from model import InventoryModel
from view import InventoryView


class InventoryControllerWithLogout:
    """Controller that supports logout and login loop"""

    def __init__(self, model: InventoryModel, view: InventoryView, db_config: dict):
        self.model = model
        self.view = view
        self.db_config = db_config
        self.model.add_observer(self)
        self._connect_signals()
        self.update()

    def _connect_signals(self):
        self.view.add_item_signal.connect(self.handle_add_item)
        self.view.edit_item_signal.connect(self.handle_edit_item)
        self.view.delete_item_signal.connect(self.handle_delete_item)
        self.view.adjust_stock_signal.connect(self.handle_adjust_stock)
        self.view.filter_changed_signal.connect(self.handle_filter_changed)
        self.view.refresh_low_stock_signal.connect(self.update_low_stock)
        self.view.logout_signal.connect(self.handle_logout)

    def update(self):
        self.update_inventory_table()
        self.update_low_stock()
        self.update_statistics()

    def update_inventory_table(self):
        search_text = self.view.get_search_text()
        category = self.view.get_category_filter()
        items = self.model.get_filtered_items(search_text, category)
        self.view.populate_inventory_table(items)

    def update_low_stock(self):
        items = self.model.get_low_stock_items()
        self.view.populate_low_stock_table(items)

    def update_statistics(self):
        stats = self.model.get_statistics()
        self.view.display_statistics(stats)

    # --- Item Handlers ---
    def handle_add_item(self, item_data):
        if not item_data['name'].strip():
            self.view.show_message("Validation Error", "Item name cannot be empty!", QMessageBox.Icon.Warning)
            return False
        success = self.model.add_item(
            item_data['name'], item_data['category'], item_data['quantity'],
            item_data['min_stock'], item_data['unit_price'], item_data['supplier']
        )
        if success:
            self.view.show_message("Success", "Item added successfully!", QMessageBox.Icon.Information)
        else:
            self.view.show_message("Error", "Failed to add item to database!", QMessageBox.Icon.Critical)
        return success

    def handle_edit_item(self, item_name, item_data):
        if not item_data['name'].strip():
            self.view.show_message("Validation Error", "Item name cannot be empty!", QMessageBox.Icon.Warning)
            return False
        item_id = self.model.find_item_by_name(item_name)
        if item_id >= 0:
            success = self.model.update_item(
                item_id, item_data['name'], item_data['category'], item_data['quantity'],
                item_data['min_stock'], item_data['unit_price'], item_data['supplier']
            )
            if success:
                self.view.show_message("Success", "Item updated successfully!", QMessageBox.Icon.Information)
            else:
                self.view.show_message("Error", "Failed to update item!", QMessageBox.Icon.Critical)
            return success
        else:
            self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
            return False

    def handle_delete_item(self, item_name):
        reply = self.view.confirm_action("Confirm Delete",
                                         f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone!")
        if reply:
            item_id = self.model.find_item_by_name(item_name)
            if item_id >= 0:
                success = self.model.delete_item(item_id)
                if success:
                    self.view.show_message("Success", "Item deleted successfully!", QMessageBox.Icon.Information)
                else:
                    self.view.show_message("Error", "Failed to delete item!", QMessageBox.Icon.Critical)
                return success
            else:
                self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
                return False
        return False

    def handle_adjust_stock(self, item_name, adjustment):
        if adjustment == 0:
            self.view.show_message("Info", "No adjustment made (change is 0)", QMessageBox.Icon.Information)
            return False
        item_id = self.model.find_item_by_name(item_name)
        if item_id >= 0:
            success = self.model.adjust_stock(item_id, adjustment)
            if success:
                action = "increased" if adjustment > 0 else "decreased"
                self.view.show_message("Success", f"Stock {action} by {abs(adjustment)} units!", QMessageBox.Icon.Information)
            else:
                self.view.show_message("Error", "Failed to adjust stock!", QMessageBox.Icon.Critical)
            return success
        else:
            self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
            return False

    def handle_filter_changed(self):
        self.update_inventory_table()

    # --- Logout Handler ---
    def handle_logout(self):
        reply = self.view.confirm_action("Logout Confirmation", "Are you sure you want to logout?")
        if reply:
            self.cleanup()
            self.view.close()

            # Reopen login window
            login_window = LoginWindow(self.db_config)
            if login_window.exec():
                if login_window.is_authenticated():
                    user = login_window.get_username()
                    user_data = login_window.get_user_data()

                    # Reopen main app with new user
                    model = InventoryModel(self.db_config)
                    view = InventoryView()
                    view.setWindowTitle(f"Inventoria - {user} ({user_data['role']})")
                    controller = InventoryControllerWithLogout(model, view, self.db_config)
                    model.load_sample_data()
                    view.show()
            else:
                import sys
                sys.exit(0)

    # --- Cleanup ---
    def cleanup(self):
        try:
            self.model.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")