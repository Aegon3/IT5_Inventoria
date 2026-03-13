"""
Inventory Management System - Controller (Database Version)
"""

from PyQt6.QtWidgets import QMessageBox
from model.supplier_model import SupplierModel
from controller.kpi_controller import KPIController


class InventoryController:
    """Main controller for inventory operations with database"""

    def __init__(self, model, view, user_role="staff", username="User"):
        self.model = model
        self.view = view
        self.user_role = user_role
        self.username = username

        # FIX: Use hardcoded db_config (matches main.py)
        db_config = {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': '',
            'port': 3308
        }
        self.supplier_model = SupplierModel(db_config)
        self.kpi_controller = KPIController(model, view, db_config)
        if user_role == "admin":
            self.view.kpi_dashboard.set_kpi_controller(self.kpi_controller)

        self.model.add_observer(self)
        self._connect_signals()
        self.update()

    def _connect_signals(self):
        # Existing signals
        self.view.add_item_signal.connect(self.handle_add_item)
        self.view.edit_item_signal.connect(self.handle_edit_item)
        self.view.delete_item_signal.connect(self.handle_delete_item)
        self.view.adjust_stock_signal.connect(self.handle_adjust_stock)
        self.view.filter_changed_signal.connect(self.handle_filter_changed)
        self.view.refresh_low_stock_signal.connect(self.update_low_stock)

        # NEW: Supplier and approval signals
        self.view.request_stock_signal.connect(self.handle_request_stock)
        self.view.approve_request_signal.connect(self.handle_approve_request)
        self.view.refresh_approvals_signal.connect(self.handle_refresh_approvals)
        self.view.add_supplier_signal.connect(self.handle_add_supplier)
        self.view.edit_supplier_signal.connect(self.handle_edit_supplier)
        self.view.delete_supplier_signal.connect(self.handle_delete_supplier)
        self.view.place_order_signal.connect(self.handle_place_order)
        self.view.refresh_activity_log_signal.connect(self.handle_refresh_activity_log)
        self.view.view_suppliers_signal.connect(self.handle_view_supplier_details)

    def update(self):
        self.update_inventory_table()
        self.update_low_stock()
        self.update_statistics()
        self.update_suppliers()
        if self.user_role == "admin":
            self.handle_refresh_approvals()
        self.handle_refresh_activity_log()
        self.handle_refresh_activity_log()

    def update_inventory_table(self):
        search_text = self.view.get_search_text()
        category = self.view.get_category_filter()
        items = self.model.get_filtered_items(search_text, category)
        self.view.populate_inventory_table(items)

    def update_low_stock(self):
        items = self.model.get_low_stock_items()
        self.view.populate_low_stock_table(items)

    def update_statistics(self):
        self.kpi_controller.update()

    def update_suppliers(self):
        """Update suppliers table"""
        suppliers = self.supplier_model.get_all_suppliers()
        self.view.populate_suppliers_table(suppliers)

    # --- Existing Item Handlers ---
    def handle_add_item(self, item_data):
        try:
            if not item_data['name'].strip():
                self.view.show_message("Validation Error", "Item name cannot be empty!", QMessageBox.Icon.Warning)
                return False

            success = self.model.add_item(
                item_data['name'], item_data['category'], item_data['quantity'],
                item_data['min_stock'], item_data['unit_price'], item_data['supplier']
            )

            if success:
                self.log_activity("Added Item", f"Added item: {item_data['name']} | Category: {item_data['category']} | Qty: {item_data['quantity']}")
                self.view.show_message("Success", "Item added successfully!", QMessageBox.Icon.Information)
            else:
                self.view.show_message("Error", "Failed to add item to database!", QMessageBox.Icon.Critical)
            return success
        except Exception as e:
            self.view.show_message("Error", f"Failed to add item: {str(e)}", QMessageBox.Icon.Critical)
            return False

    def handle_edit_item(self, item_name, item_data):
        """Handle editing an item - FIXED VERSION"""
        try:
            # Find the item by original name
            item_id = self.model.find_item_by_name(item_name)

            if item_id >= 0:
                # Update with new data
                success = self.model.update_item(
                    item_id,
                    item_data['name'],
                    item_data['category'],
                    item_data['quantity'],
                    item_data['min_stock'],
                    item_data['unit_price'],
                    item_data['supplier']
                )

                if success:
                    self.log_activity("Edited Item", f"Edited item: {item_name} → {item_data['name']} | Qty: {item_data['quantity']}")
                    self.view.show_message("Success", "Item updated successfully!", QMessageBox.Icon.Information)
                    self.update()  # Refresh all views
                    return True
                else:
                    self.view.show_message("Error", "Failed to update item in database!", QMessageBox.Icon.Critical)
                    return False
            else:
                self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
                return False
        except Exception as e:
            self.view.show_message("Error", f"Failed to update item: {str(e)}", QMessageBox.Icon.Critical)
            return False

    def handle_delete_item(self, item_name):
        try:
            reply = self.view.confirm_action("Confirm Delete",
                f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone!")

            if reply:
                item_id = self.model.find_item_by_name(item_name)

                if item_id >= 0:
                    success = self.model.delete_item(item_id)
                    if success:
                        self.log_activity("Deleted Item", f"Deleted item: {item_name}")
                        self.view.show_message("Success", "Item deleted successfully!", QMessageBox.Icon.Information)
                    else:
                        self.view.show_message("Error", "Failed to delete item!", QMessageBox.Icon.Critical)
                    return success
                else:
                    self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
                    return False
            return False
        except Exception as e:
            self.view.show_message("Error", f"Failed to delete item: {str(e)}", QMessageBox.Icon.Critical)
            return False

    def handle_adjust_stock(self, item_name, adjustment):
        try:
            if adjustment == 0:
                self.view.show_message("Info", "No adjustment made (change is 0)", QMessageBox.Icon.Information)
                return False

            item_id = self.model.find_item_by_name(item_name)

            if item_id >= 0:
                success = self.model.adjust_stock(item_id, adjustment)
                if success:
                    action = "increased" if adjustment > 0 else "decreased"
                    self.log_activity("Adjusted Stock", f"Stock {action} for '{item_name}' by {abs(adjustment)} units")
                    self.view.show_message("Success", f"Stock {action} by {abs(adjustment)} units!",
                                          QMessageBox.Icon.Information)
                else:
                    self.view.show_message("Error", "Failed to adjust stock!", QMessageBox.Icon.Critical)
                return success
            else:
                self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)
                return False
        except Exception as e:
            self.view.show_message("Error", f"Failed to adjust stock: {str(e)}", QMessageBox.Icon.Critical)
            return False

    def handle_filter_changed(self):
        self.update_inventory_table()

    # --- NEW: Supplier and Approval Handlers ---
    def handle_request_stock(self, item_name, quantity, reason):
        """Handle stock request from staff - FIXED VERSION"""
        if self.user_role != "staff":
            self.view.show_message("Error", "Only staff can request stock!", QMessageBox.Icon.Warning)
            return

        # Find item by name
        item_id = self.model.find_item_by_name(item_name)
        if item_id >= 0:
            success = self.supplier_model.create_stock_request(
                item_id, quantity, self.username, reason
            )
            if success:
                self.view.show_message("Success", "Stock request submitted for approval!", QMessageBox.Icon.Information)
                # Refresh approvals if admin is viewing
                if self.user_role == "admin":
                    self.handle_refresh_approvals()
            else:
                self.view.show_message("Error", "Failed to submit request!", QMessageBox.Icon.Critical)
        else:
            self.view.show_message("Error", "Item not found!", QMessageBox.Icon.Warning)

    def handle_approve_request(self, request_id, approve, notes):
        """Handle approval/rejection of stock request (admin only) - FIXED VERSION"""
        if self.user_role != "admin":
            self.view.show_message("Error", "Only admins can approve requests!", QMessageBox.Icon.Warning)
            return

        if approve:
            success = self.supplier_model.approve_stock_request(request_id, self.username, notes)
            if success:
                self.log_activity("Approved Stock Request", f"Approved request ID {request_id}")
                self.view.show_message("Success", "Request approved!", QMessageBox.Icon.Information)
            else:
                self.view.show_message("Error", "Failed to approve request!", QMessageBox.Icon.Critical)
        else:
            success = self.supplier_model.reject_stock_request(request_id, self.username, notes)
            if success:
                self.log_activity("Rejected Stock Request", f"Rejected request ID {request_id}")
                self.view.show_message("Success", "Request rejected!", QMessageBox.Icon.Information)
            else:
                self.view.show_message("Error", "Failed to reject request!", QMessageBox.Icon.Critical)

        # Refresh all views
        self.update()
        # Refresh approvals table
        self.handle_refresh_approvals()

    def handle_refresh_approvals(self):
        """Refresh pending approvals - FIXED VERSION"""
        if self.user_role == "admin":
            try:
                approvals = self.supplier_model.get_pending_approvals()
                self.view.populate_approvals_table(approvals)
            except Exception as e:
                print(f"Error refreshing approvals: {e}")
                self.view.show_message("Error", f"Failed to refresh approvals: {str(e)}", QMessageBox.Icon.Warning)

    def handle_add_supplier(self, supplier_data):
        """Handle adding a new supplier"""
        if not supplier_data['name'].strip():
            self.view.show_message("Validation Error", "Supplier name cannot be empty!", QMessageBox.Icon.Warning)
            return False

        success = self.supplier_model.add_supplier(
            supplier_data['name'],
            supplier_data['contact_person'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['address'],
            supplier_data.get('notes', '')
        )
        if success:
            self.log_activity("Added Supplier", f"Added supplier: {supplier_data['name']}")
            self.view.show_message("Success", "Supplier added successfully!", QMessageBox.Icon.Information)
            self.update_suppliers()
        else:
            self.view.show_message("Error", "Failed to add supplier!", QMessageBox.Icon.Critical)
        return success

    def handle_edit_supplier(self, supplier_id, supplier_data):
        """Handle editing a supplier"""
        if not supplier_data['name'].strip():
            self.view.show_message("Validation Error", "Supplier name cannot be empty!", QMessageBox.Icon.Warning)
            return False

        success = self.supplier_model.update_supplier(
            supplier_id,
            supplier_data['name'],
            supplier_data['contact_person'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['address'],
            supplier_data['status'],
            supplier_data.get('notes', '')
        )
        if success:
            self.log_activity("Edited Supplier", f"Edited supplier ID {supplier_id}: {supplier_data['name']}")
            self.view.show_message("Success", "Supplier updated successfully!", QMessageBox.Icon.Information)
            self.update_suppliers()
        else:
            self.view.show_message("Error", "Failed to update supplier!", QMessageBox.Icon.Critical)
        return success

    def handle_delete_supplier(self, supplier_id):
        """Handle deleting a supplier - FIXED VERSION"""
        if self.user_role != "admin":
            self.view.show_message("Error", "Only admins can delete suppliers!", QMessageBox.Icon.Warning)
            return False

        # Get supplier name for confirmation
        supplier = self.supplier_model.get_supplier_by_id(supplier_id)
        if not supplier:
            self.view.show_message("Error", "Supplier not found!", QMessageBox.Icon.Critical)
            return False

        reply = self.view.confirm_action("Confirm Delete",
            f"Are you sure you want to delete supplier '{supplier.name}'?\n\nThis action cannot be undone!")

        if not reply:
            return False

        success, message = self.supplier_model.delete_supplier(supplier_id)

        if success:
            self.log_activity("Deleted Supplier", f"Deleted supplier: {supplier.name}")
            self.view.show_message("Success", f"Supplier deleted: {message}", QMessageBox.Icon.Information)
            self.update_suppliers()
            return True
        else:
            self.view.show_message("Error", f"Failed to delete supplier: {message}", QMessageBox.Icon.Critical)
            return False

    def handle_place_order(self, order_data):
        """Handle placing a new order - Staff creates approval requests, Admin creates directly"""
        try:
            # Debug: Print order data for troubleshooting
            print(f"DEBUG Order data received: {order_data}")

            if order_data is None:
                self.view.show_message("Error", "Order data is missing!", QMessageBox.Icon.Critical)
                return False

            # Check if we have items
            items = order_data.get('items', [])
            if not items:
                self.view.show_message("Error", "Please add at least one item to the order!", QMessageBox.Icon.Critical)
                return False

            # Check if we have a valid supplier_id
            supplier_id = order_data.get('supplier_id')
            supplier_name = order_data.get('supplier_name', 'Unknown Supplier')

            if supplier_id is None:
                # Show helpful message about how to fix
                item_list = "\n".join([f"• {item.get('name', 'Unknown')}" for item in items[:5]])
                if len(items) > 5:
                    item_list += f"\n• ... and {len(items) - 5} more items"

                self.view.show_message("Supplier Information Required",
                                      f"No supplier was found for this order.\n\n"
                                      f"Items in order ({len(items)}):\n"
                                      f"{item_list}\n\n"
                                      f"Possible solutions:\n"
                                      f"1. Edit each item and assign a supplier\n"
                                      f"2. Use the 'Edit Supplier' option to add suppliers to items\n"
                                      f"3. Create a new supplier first, then assign it to items",
                                      QMessageBox.Icon.Warning)
                return False

            order_number = order_data.get('order_number', f"ORD-{self.username}-{self.get_timestamp()}")
            notes = order_data.get('notes', '')
            expected_delivery = order_data.get('expected_delivery', None)
            expected_delivery = order_data.get('expected_delivery', None)

            # STAFF: Submit orders as stock requests for admin approval
            if self.user_role == "staff":
                print(f"📋 Staff order - creating stock requests for approval")

                success_count = 0
                order_summary = f"Order from {supplier_name}"
                if notes:
                    order_summary += f" - {notes}"

                # Create a stock request for each item
                for item in items:
                    request_id = self.supplier_model.create_stock_request(
                        item['id'],
                        item['quantity'],
                        self.username,
                        order_summary,
                        'order'  # Mark as order type
                    )

                    if request_id:
                        success_count += 1

                if success_count == len(items):
                    self.view.show_message("Order Submitted for Approval",
                                           f"📋 Your order has been submitted for admin approval!\n\n"
                                           f"Supplier: {supplier_name}\n"
                                           f"Items: {len(items)}\n"
                                           f"Order Number: {order_number}\n\n"
                                           f"✅ All {success_count} items sent to Activity Log\n"
                                           f"An admin will review and approve your order.",
                                           QMessageBox.Icon.Information)
                    # Refresh approvals if admin
                    if self.user_role == "admin":
                        self.handle_refresh_approvals()
                    return True
                else:
                    self.view.show_message("Partial Success",
                                           f"⚠️ Only {success_count} of {len(items)} items were submitted.\n"
                                           f"Please try again for failed items.",
                                           QMessageBox.Icon.Warning)
                    return False

            # ADMIN: Create order directly (no approval needed)
            else:
                print(f"✅ Admin order - creating directly and updating stock")

                order_id = self.supplier_model.create_order(
                    supplier_id,
                    order_number,
                    self.username,
                    notes,
                    expected_delivery
                )

                if order_id:
                    # Save order items
                    for item in items:
                        self.supplier_model.add_order_item(
                            order_id,
                            item['id'],
                            item['quantity'],
                            item['unit_price']
                        )

                    # Admin orders automatically update stock
                    for item in items:
                        self.model.adjust_stock(item['id'], item['quantity'])

                    self.view.show_message("Success",
                                           f"✅ Order #{order_id} created and stock updated!\n\n"
                                           f"Supplier: {supplier_name}\n"
                                           f"Items: {len(items)}\n"
                                           f"Order Number: {order_number}\n\n"
                                           f"Stock has been automatically updated.",
                                           QMessageBox.Icon.Information)
                    return True
                else:
                    self.view.show_message("Error", "Failed to create order!", QMessageBox.Icon.Critical)
                    return False
        except Exception as e:
            self.view.show_message("Error", f"Failed to place order: {str(e)}", QMessageBox.Icon.Critical)
            import traceback
            print(f"DEBUG Order placement error: {traceback.format_exc()}")
            return False

    def handle_view_supplier_details(self, supplier_id):
        """Handle viewing supplier details"""
        supplier = self.supplier_model.get_supplier_by_id(supplier_id)
        if supplier:
            details = f"""
            <h3>Supplier Details</h3>
            <p><b>Name:</b> {supplier.name}</p>
            <p><b>Contact Person:</b> {supplier.contact_person}</p>
            <p><b>Phone:</b> {supplier.phone}</p>
            <p><b>Email:</b> {supplier.email}</p>
            <p><b>Address:</b> {supplier.address}</p>
            <p><b>Status:</b> {supplier.status}</p>
            <p><b>Items Supplied:</b> {supplier.items_supplied_count}</p>
            <p><b>Notes:</b> {supplier.notes}</p>
            """
            self.view.show_message("Supplier Details", details, QMessageBox.Icon.Information)

    def get_timestamp(self):
        """Get current timestamp for order number"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def get_supplier_for_edit(self, supplier_id):
        """Get complete supplier data for editing"""
        return self.supplier_model.get_supplier_by_id(supplier_id)
    # --- Activity Log ---
    def log_activity(self, action, details=""):
        """Write an entry to the activity_log table."""
        try:
            self.model.db.log_action(self.username, action, details)
            self.handle_refresh_activity_log()
        except Exception as e:
            print(f"Logging error: {e}")

    def handle_refresh_activity_log(self):
        """Load activity log from DB and push to view."""
        try:
            logs = self.model.db.get_activity_log()
            self.view.populate_activity_log(logs)
        except Exception as e:
            print(f"Error refreshing activity log: {e}")

    # --- Cleanup ---
    def cleanup(self):
        try:
            self.model.close()
            self.supplier_model.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")