"""
Inventory Management System - Controller (Database Version)
NO QMessageBox imports - All UI alerts delegated to view.
Handles ALL database operations directly.
"""

from controller.supplier_controller import SupplierController
from controller.kpi_controller import KPIController
from model.database import DatabaseHandler
from model.model import InventoryItem


class InventoryController:
    """Main controller for inventory operations with database"""

    def __init__(self, model, view, user_role="staff", username="User", db_config=None):
        self.model = model
        self.view = view
        self.user_role = user_role
        self.username = username

        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': '',
            'port': 3308
        }

        # Create database handler
        self.db = DatabaseHandler(**self.db_config)
        self.db.connect()

        # Set db on model for activity log access
        self.model.db = self.db

        self.supplier_controller = SupplierController(self.db_config)
        self.kpi_controller = KPIController(model, view, self.db_config, self.db)
        if user_role == "admin":
            self.view.kpi_dashboard.set_kpi_controller(self.kpi_controller)

        self.model.add_observer(self)
        self._connect_signals()

        self._activity_log_all = []
        self._activity_page = 1
        self._activity_page_size = 15

        self.update()

    def _connect_signals(self):
        self.view.add_item_signal.connect(self.handle_add_item)
        self.view.edit_item_signal.connect(self.handle_edit_item)
        self.view.delete_item_signal.connect(self.handle_delete_item)
        self.view.adjust_stock_signal.connect(self.handle_adjust_stock)
        self.view.filter_changed_signal.connect(self.handle_filter_changed)
        self.view.refresh_low_stock_signal.connect(self.update_low_stock)

        self.view.request_stock_signal.connect(self.handle_request_stock)
        self.view.approve_request_signal.connect(self.handle_approve_request)
        self.view.refresh_approvals_signal.connect(self.handle_refresh_approvals)
        self.view.add_supplier_signal.connect(self.handle_add_supplier)
        self.view.edit_supplier_signal.connect(self.handle_edit_supplier)
        self.view.delete_supplier_signal.connect(self.handle_delete_supplier)
        self.view.place_order_signal.connect(self.handle_place_order)
        self.view.refresh_activity_log_signal.connect(self.handle_refresh_activity_log)
        self.view.view_suppliers_signal.connect(self.handle_view_supplier_details)
        self.view.generate_report_signal.connect(self.handle_generate_report)
        if self.user_role == "admin" and hasattr(self.view, 'activity_log_page_signal'):
            self.view.activity_log_page_signal.connect(self.handle_activity_log_page)
        if self.user_role == "staff" and hasattr(self.view, 'my_requests_signal'):
            self.view.my_requests_signal.connect(self.handle_load_my_requests)

    def update(self):
        self.update_inventory_table()
        self.update_low_stock()
        self.update_statistics()
        self.update_suppliers()
        if self.user_role == "admin":
            self.handle_refresh_approvals()
        self.handle_refresh_activity_log()
        if self.user_role == "staff":
            self.handle_load_my_requests()

    def update_inventory_table(self):
        search_text = self.view.get_search_text()
        category = self.view.get_category_filter()
        items = self.get_filtered_items(search_text, category)
        self.view.populate_inventory_table(items)

    def update_low_stock(self):
        if not hasattr(self.view, 'low_stock_table'):
            return
        items = self.get_low_stock_items()
        self.view.populate_low_stock_table(items)

    def update_statistics(self):
        self.kpi_controller.update()

    def update_suppliers(self):
        suppliers = self.supplier_controller.get_all_suppliers()
        self.view.populate_suppliers_table(suppliers)

    # ==================== INVENTORY DATABASE OPERATIONS ====================

    def get_filtered_items(self, search_text="", category="All"):
        sql = "SELECT * FROM items WHERE name LIKE %s"
        params = [f"%{search_text}%"]
        if category != "All":
            sql += " AND category=%s"
            params.append(category)
        self.db.cursor.execute(sql, tuple(params))
        rows = self.db.cursor.fetchall()
        return [InventoryItem.from_dict(row) for row in rows]

    def get_low_stock_items(self):
        self.db.cursor.execute("SELECT *, (min_stock - quantity) as shortage FROM items WHERE quantity < min_stock")
        rows = self.db.cursor.fetchall()
        return [InventoryItem.from_dict(row) for row in rows]

    def add_item(self, name, category, quantity, min_stock, unit_price, supplier):
        item_id = self.db.add_item(name, category, quantity, min_stock, unit_price, supplier)
        if item_id:
            self.model.notify_observers()
            return True
        return False

    def update_item(self, item_id, name, category, quantity, min_stock, unit_price, supplier):
        success = self.db.update_item(item_id, name, category, quantity, min_stock, unit_price, supplier)
        if success:
            self.model.notify_observers()
        return success

    def delete_item(self, item_id):
        success = self.db.delete_item(item_id)
        if success:
            self.model.notify_observers()
        return success

    def adjust_stock(self, item_id, adjustment):
        success = self.db.adjust_stock(item_id, adjustment)
        if success:
            self.model.notify_observers()
        return success

    def find_item_by_name(self, name):
        self.db.cursor.execute("SELECT id FROM items WHERE name = %s", (name,))
        row = self.db.cursor.fetchone()
        return row['id'] if row else -1

    def get_statistics(self):
        return self.db.get_statistics()

    def get_all_categories(self):
        return self.db.get_all_categories()

    def item_exists(self, name):
        return self.db.item_exists(name)

    def get_item_by_name(self, name):
        item = self.db.get_item_by_name(name)
        if item:
            return InventoryItem.from_dict(item)
        return None

    # ==================== HANDLERS ====================

    def handle_add_item(self, item_data):
        if not item_data['name'].strip():
            self.view.show_message("Validation Error", "Item name cannot be empty!", "warning")
            return False

        success = self.add_item(
            item_data['name'], item_data['category'], item_data['quantity'],
            item_data['min_stock'], item_data['unit_price'], item_data['supplier']
        )

        if success:
            self.log_activity("Added Item", f"Added item: {item_data['name']} | Category: {item_data['category']} | Qty: {item_data['quantity']}")
            self.view.show_message("Success", "Item added successfully!", "information")
        else:
            self.view.show_message("Error", "Failed to add item to database!", "critical")
        return success

    def handle_edit_item(self, item_name, item_data):
        item_id = self.find_item_by_name(item_name)

        if item_id >= 0:
            success = self.update_item(
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
                self.view.show_message("Success", "Item updated successfully!", "information")
                self.update()
                return True
            else:
                self.view.show_message("Error", "Failed to update item in database!", "critical")
                return False
        else:
            self.view.show_message("Error", "Item not found!", "warning")
            return False

    def handle_delete_item(self, item_name):
        reply = self.view.confirm_action("Confirm Delete",
            f"Are you sure you want to delete '{item_name}'?\n\nThis action cannot be undone!")

        if reply:
            item_id = self.find_item_by_name(item_name)

            if item_id >= 0:
                success = self.delete_item(item_id)
                if success:
                    self.log_activity("Deleted Item", f"Deleted item: {item_name}")
                    self.view.show_message("Success", "Item deleted successfully!", "information")
                else:
                    self.view.show_message("Error", "Failed to delete item!", "critical")
                return success
            else:
                self.view.show_message("Error", "Item not found!", "warning")
                return False
        return False

    def handle_adjust_stock(self, item_name, adjustment):
        if adjustment == 0:
            self.view.show_message("Info", "No adjustment made (change is 0)", "information")
            return False

        item_id = self.find_item_by_name(item_name)

        if item_id >= 0:
            success = self.adjust_stock(item_id, adjustment)
            if success:
                action = "increased" if adjustment > 0 else "decreased"
                self.log_activity("Adjusted Stock", f"Stock {action} for '{item_name}' by {abs(adjustment)} units")
                self.view.show_message("Success", f"Stock {action} by {abs(adjustment)} units!", "information")
            else:
                self.view.show_message("Error", "Failed to adjust stock!", "critical")
            return success
        else:
            self.view.show_message("Error", "Item not found!", "warning")
            return False

    def handle_load_my_requests(self):
        try:
            all_requests = self.supplier_controller.get_all_stock_requests()
            my_requests = [r for r in all_requests if r.requested_by == self.username]
            if hasattr(self.view, 'populate_my_requests_table'):
                self.view.populate_my_requests_table(my_requests)
        except Exception as e:
            print(f"Error loading my requests: {e}")

    def handle_filter_changed(self):
        self.update_inventory_table()

    def handle_request_stock(self, item_name, quantity, reason):
        if self.user_role != "staff":
            self.view.show_message("Error", "Only staff can request stock!", "warning")
            return

        item_id = self.find_item_by_name(item_name)
        if item_id >= 0:
            success = self.supplier_controller.create_stock_request(
                item_id, quantity, self.username, reason
            )
            if success:
                self.view.show_message("Success", "Stock request submitted for approval!", "information")
                if self.user_role == "admin":
                    self.handle_refresh_approvals()
                if self.user_role == "staff":
                    self.handle_load_my_requests()
            else:
                self.view.show_message("Error", "Failed to submit request!", "critical")
        else:
            self.view.show_message("Error", "Item not found!", "warning")

    def handle_approve_request(self, request_id, approve, notes):
        if self.user_role != "admin":
            self.view.show_message("Error", "Only admins can approve requests!", "warning")
            return

        if approve:
            success = self.supplier_controller.approve_stock_request(request_id, self.username, notes)
            if success:
                self.log_activity("Approved Stock Request", f"Approved request ID {request_id}")
                self.view.show_message("Success", "Request approved!", "information")
            else:
                self.view.show_message("Error", "Failed to approve request!", "critical")
        else:
            success = self.supplier_controller.reject_stock_request(request_id, self.username, notes)
            if success:
                self.log_activity("Rejected Stock Request", f"Rejected request ID {request_id}")
                self.view.show_message("Success", "Request rejected!", "information")
            else:
                self.view.show_message("Error", "Failed to reject request!", "critical")

        self.update()
        self.handle_refresh_approvals()

    def handle_refresh_approvals(self):
        if self.user_role == "admin":
            try:
                approvals = self.supplier_controller.get_all_stock_requests()
                self.view.populate_approvals_table(approvals)
            except Exception as e:
                print(f"Error refreshing approvals: {e}")
                self.view.show_message("Error", f"Failed to refresh approvals: {str(e)}", "warning")

    def handle_add_supplier(self, supplier_data):
        if not supplier_data['name'].strip():
            self.view.show_message("Validation Error", "Supplier name cannot be empty!", "warning")
            return False

        success = self.supplier_controller.add_supplier(
            supplier_data['name'],
            supplier_data['contact_person'],
            supplier_data['phone'],
            supplier_data['email'],
            supplier_data['address'],
            supplier_data.get('notes', '')
        )
        if success:
            self.log_activity("Added Supplier", f"Added supplier: {supplier_data['name']}")
            self.view.show_message("Success", "Supplier added successfully!", "information")
            self.update_suppliers()
        else:
            self.view.show_message("Error", "Failed to add supplier!", "critical")
        return success

    def handle_edit_supplier(self, supplier_id, supplier_data):
        if not supplier_data['name'].strip():
            self.view.show_message("Validation Error", "Supplier name cannot be empty!", "warning")
            return False

        success = self.supplier_controller.update_supplier(
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
            self.view.show_message("Success", "Supplier updated successfully!", "information")
            self.update_suppliers()
        else:
            self.view.show_message("Error", "Failed to update supplier!", "critical")
        return success

    def handle_delete_supplier(self, supplier_id):
        if self.user_role != "admin":
            self.view.show_message("Error", "Only admins can delete suppliers!", "warning")
            return False

        supplier = self.supplier_controller.get_supplier_by_id(supplier_id)
        if not supplier:
            self.view.show_message("Error", "Supplier not found!", "critical")
            return False

        reply = self.view.confirm_action("Confirm Delete",
            f"Are you sure you want to delete supplier '{supplier.name}'?\n\nThis action cannot be undone!")

        if not reply:
            return False

        success, message = self.supplier_controller.delete_supplier(supplier_id)

        if success:
            self.log_activity("Deleted Supplier", f"Deleted supplier: {supplier.name}")
            self.view.show_message("Success", f"Supplier deleted: {message}", "information")
            self.update_suppliers()
            return True
        else:
            self.view.show_message("Error", f"Failed to delete supplier: {message}", "critical")
            return False

    def handle_place_order(self, order_data):
        try:
            if order_data is None:
                self.view.show_message("Error", "Order data is missing!", "critical")
                return False

            items = order_data.get('items', [])
            if not items:
                self.view.show_message("Error", "Please add at least one item to the order!", "critical")
                return False

            supplier_id = order_data.get('supplier_id')
            supplier_name = order_data.get('supplier_name', 'Unknown Supplier')

            if supplier_id is None:
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
                                      "warning")
                return False

            order_number = order_data.get('order_number', f"ORD-{self.username}-{self.get_timestamp()}")
            notes = order_data.get('notes', '')
            expected_delivery = order_data.get('expected_delivery', None)

            if self.user_role == "staff":
                success_count = 0
                order_summary = f"Order from {supplier_name}"
                if notes:
                    order_summary += f" - {notes}"

                for item in items:
                    request_id = self.supplier_controller.create_stock_request(
                        item['id'],
                        item['quantity'],
                        self.username,
                        order_summary,
                        'order'
                    )

                    if request_id:
                        success_count += 1

                if success_count == len(items):
                    self.view.show_message("Order Submitted for Approval",
                                           f" Your order has been submitted for admin approval!\n\n"
                                           f"Supplier: {supplier_name}\n"
                                           f"Items: {len(items)}\n"
                                           f"Order Number: {order_number}\n\n"
                                           f" All {success_count} items sent to Activity Log\n"
                                           f"An admin will review and approve your order.",
                                           "information")
                    if self.user_role == "admin":
                        self.handle_refresh_approvals()
                    return True
                else:
                    self.view.show_message("Partial Success",
                                           f" Only {success_count} of {len(items)} items were submitted.\n"
                                           f"Please try again for failed items.",
                                           "warning")
                    return False

            else:
                order_id = self.supplier_controller.create_order(
                    supplier_id,
                    order_number,
                    self.username,
                    notes,
                    expected_delivery
                )

                if order_id:
                    for item in items:
                        self.supplier_controller.add_order_item(
                            order_id,
                            item['id'],
                            item['quantity'],
                            item['unit_price']
                        )

                    for item in items:
                        self.adjust_stock(item['id'], item['quantity'])

                    self.view.show_message("Success",
                                           f" Order #{order_id} created and stock updated!\n\n"
                                           f"Supplier: {supplier_name}\n"
                                           f"Items: {len(items)}\n"
                                           f"Order Number: {order_number}\n\n"
                                           f"Stock has been automatically updated.",
                                           "information")
                    return True
                else:
                    self.view.show_message("Error", "Failed to create order!", "critical")
                    return False
        except Exception as e:
            self.view.show_message("Error", f"Failed to place order: {str(e)}", "critical")
            print(f"DEBUG Order placement error: {e}")
            return False

    def handle_generate_report(self):
        try:
            from view.report_generator import ReportDialog
            dlg = ReportDialog(self.view, self.db_config)
            self._active_report_dialog = dlg
            dlg.set_callbacks(
                generate_callback=self._do_generate_report,
                open_folder_callback=self._do_open_reports_folder
            )
            dlg.exec()
        except ImportError as e:
            self.view.show_message("Error", f"Report module not available: {str(e)}", "critical")
        except Exception as e:
            self.view.show_message("Error", f"Failed to open report dialog: {str(e)}", "critical")

    def _do_generate_report(self, params):
        from view.report_builder import (
            build_inventory_pdf, build_category_pdf,
            build_damage_report_pdf, build_stock_issuance_pdf
        )
        import os

        report_type = params['report_type']
        category = params['category']
        include_low = params['include_low_stock']
        start_date = params['start_date']
        end_date = params['end_date']

        try:
            if report_type == "Category Summary":
                self.db.cursor.execute("""
                    SELECT
                        category,
                        COUNT(*) AS item_count,
                        SUM(quantity) AS total_quantity,
                        SUM(quantity * unit_price) AS total_value,
                        COUNT(CASE WHEN quantity < min_stock THEN 1 END) AS low_stock_count
                    FROM items
                    GROUP BY category
                    ORDER BY category
                """)
                rows = self.db.cursor.fetchall()
                if not rows:
                    self._active_report_dialog.show_result(False, "No categories found.")
                    return
                filepath = build_category_pdf(rows)

            elif report_type == "Low Stock Only":
                self.db.cursor.execute("SELECT * FROM items ORDER BY category, name")
                items = self.db.cursor.fetchall()
                items = [i for i in items if i['quantity'] < i['min_stock']]
                if not items:
                    self._active_report_dialog.show_result(False, "No low stock items found.")
                    return
                filepath = build_inventory_pdf(items, "low_stock", "All", False, start_date, end_date)

            elif report_type == "Damage Report":
                query = """
                    SELECT
                        reported_date,
                        item_name,
                        quantity,
                        reason,
                        reported_by
                    FROM damage_reports
                """
                params_list = []
                if start_date and end_date:
                    query += " WHERE reported_date BETWEEN %s AND %s"
                    params_list.extend([start_date, end_date])
                query += " ORDER BY reported_date DESC"
                self.db.cursor.execute(query, tuple(params_list))
                rows = self.db.cursor.fetchall()
                if not rows:
                    self._active_report_dialog.show_result(False, "No damage reports found.")
                    return
                filepath = build_damage_report_pdf(rows, start_date, end_date)

            elif report_type == "Stock Issuance Report":
                query = """
                    SELECT
                        si.issued_date,
                        si.item_name,
                        i.category,
                        si.quantity,
                        i.unit_price,
                        (si.quantity * i.unit_price) AS total_value,
                        si.issued_by,
                        si.notes
                    FROM stock_issuances si
                    LEFT JOIN items i ON si.item_id = i.id
                """
                params_list = []
                if start_date and end_date:
                    query += " WHERE si.issued_date BETWEEN %s AND %s"
                    params_list.extend([start_date, end_date])
                query += " ORDER BY si.issued_date DESC"
                self.db.cursor.execute(query, tuple(params_list))
                rows = self.db.cursor.fetchall()
                if not rows:
                    self._active_report_dialog.show_result(False, "No issuance records found.")
                    return
                filepath = build_stock_issuance_pdf(rows, start_date, end_date)

            else:
                where = []
                params_list = []
                if category != "All":
                    where.append("category = %s")
                    params_list.append(category)
                query = "SELECT * FROM items"
                if where:
                    query += " WHERE " + " AND ".join(where)
                query += " ORDER BY category, name"
                self.db.cursor.execute(query, tuple(params_list))
                items = self.db.cursor.fetchall()
                if not items:
                    self._active_report_dialog.show_result(False, "No items found matching the criteria.")
                    return
                filepath = build_inventory_pdf(items, "full", category, include_low, start_date, end_date)

            self._active_report_dialog.show_result(True, os.path.basename(filepath))

        except Exception as e:
            self._active_report_dialog.show_result(False, f"Failed to generate report: {str(e)}")

    def _do_open_reports_folder(self):
        import subprocess, os
        reports_dir = "/Users/jbasquiat/Downloads/reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            self._active_report_dialog.show_folder_status("Created reports directory")
        try:
            subprocess.run(["open", reports_dir])
            self._active_report_dialog.show_folder_status("Opening reports folder...")
        except Exception as e:
            self.view.show_message("Error", f"Could not open folder:\n{str(e)}", "warning")

    def handle_view_supplier_details(self, supplier_id):
        supplier = self.supplier_controller.get_supplier_by_id(supplier_id)
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
            self.view.show_message("Supplier Details", details, "information")

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def get_supplier_for_edit(self, supplier_id):
        return self.supplier_controller.get_supplier_by_id(supplier_id)

    def log_activity(self, action, details=""):
        try:
            self.db.log_action(self.username, action, details)
            self.handle_refresh_activity_log()
        except Exception as e:
            print(f"Logging error: {e}")

    def handle_refresh_activity_log(self):
        try:
            logs = self.db.get_activity_log()
            self._activity_log_all = logs if logs else []
            self._activity_page = 1
            self._render_activity_log_page()
        except Exception as e:
            print(f"Error refreshing activity log: {e}")

    def handle_activity_log_page(self, direction):
        total_pages = self._activity_total_pages()
        self._activity_page = max(1, min(self._activity_page + direction, total_pages))
        self._render_activity_log_page()

    def _activity_total_pages(self):
        total = len(self._activity_log_all)
        if total == 0:
            return 1
        import math
        return math.ceil(total / self._activity_page_size)

    def _render_activity_log_page(self):
        start = (self._activity_page - 1) * self._activity_page_size
        end = start + self._activity_page_size
        page_logs = self._activity_log_all[start:end]
        self.view.populate_activity_log(page_logs)
        total_pages = self._activity_total_pages()
        if hasattr(self.view, 'update_activity_log_pagination'):
            self.view.update_activity_log_pagination(self._activity_page, total_pages)

    def cleanup(self):
        try:
            if self.db:
                self.db.disconnect()
        except Exception as e:
            print(f"Error during cleanup: {e}")