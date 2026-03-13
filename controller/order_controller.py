"""
Inventoria - Order Controller
Handles all order-related logic: loading orders, updating status,
deleting orders, approving orders, loading inventory items, and finding suppliers.

This controller extracts the hidden controller logic from:
  - view/supplier_dialogs.py → OrdersDialog  (load_orders, update_order_status,
                                               delete_order, approve_order)
  - view/supplier_dialogs.py → OrderDialog   (load_inventory_items,
                                               _find_supplier_by_name, _on_add_item_clicked)

HOW TO PLACE THIS FILE:
  Put it in your /controller/ folder as: controller/order_controller.py

HOW TO USE IN main.py:
  from controller.order_controller import OrderController
  order_controller = OrderController(db_config)

  Then pass it into dialogs:
  dlg = OrdersDialog(view, db_config, user_role, order_controller)
  dlg = OrderDialog(view, None, "Auto-detect Supplier", db_config, order_controller)
"""

import re
from model.database import DatabaseHandler


class OrderController:
    """
    Dedicated controller for all order-related actions.
    Keeps order management and supplier-finding logic OUT of views.
    """

    def __init__(self, db_config: dict):
        self.db_config = db_config

    # -----------------------------------------------------------------------
    # LOAD ORDERS (extracted from OrdersDialog.load_orders())
    # -----------------------------------------------------------------------

    def get_orders(self, status_filter="All"):
        """
        Get all orders with optional status filter.

        Args:
            status_filter (str): "All" or a specific status like "pending", "delivered", etc.

        Returns:
            tuple: (success: bool, orders: list | None, error: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, None, "Failed to connect to database."

        try:
            if status_filter != "All":
                query = """
                    SELECT o.*, s.name as supplier_name,
                           COUNT(oi.id) as items_count,
                           SUM(oi.total_price) as total_amount
                    FROM orders o
                    LEFT JOIN suppliers s ON o.supplier_id = s.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    WHERE o.status = %s
                    GROUP BY o.id
                    ORDER BY o.order_date DESC, o.id DESC
                """
                db.cursor.execute(query, (status_filter,))
            else:
                query = """
                    SELECT o.*, s.name as supplier_name,
                           COUNT(oi.id) as items_count,
                           SUM(oi.total_price) as total_amount
                    FROM orders o
                    LEFT JOIN suppliers s ON o.supplier_id = s.id
                    LEFT JOIN order_items oi ON o.id = oi.order_id
                    GROUP BY o.id
                    ORDER BY o.order_date DESC, o.id DESC
                """
                db.cursor.execute(query)

            orders = db.cursor.fetchall()
            print(f"✅ Loaded {len(orders)} orders from database")
            return True, orders, ""

        except Exception as e:
            print(f"❌ Error loading orders: {e}")
            return False, None, f"Failed to load orders: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # UPDATE ORDER STATUS (extracted from OrdersDialog.update_order_status())
    # -----------------------------------------------------------------------

    def update_order_status(self, order_id: int, new_status: str):
        """
        Update the status of an order.

        Args:
            order_id (int): The ID of the order to update.
            new_status (str): The new status value.

        Returns:
            tuple: (success: bool, message: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                (new_status, order_id)
            )
            db.conn.commit()
            print(f"✅ Updated order {order_id} status to {new_status}")
            return True, f"Order status updated to '{new_status}'."

        except Exception as e:
            print(f"❌ Error updating order status: {e}")
            return False, f"Failed to update order status: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # DELETE ORDER (extracted from OrdersDialog.delete_order())
    # -----------------------------------------------------------------------

    def delete_order(self, order_id: int, order_number: str):
        """
        Delete an order and its items from the database.

        Args:
            order_id (int): The ID of the order to delete.
            order_number (str): The order number (used for logging).

        Returns:
            tuple: (success: bool, message: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            # Delete order items first (foreign key constraint)
            db.cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            # Then delete the order
            db.cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            db.conn.commit()

            print(f"✅ Deleted order {order_number} (ID: {order_id})")
            return True, f"Order {order_number} deleted successfully."

        except Exception as e:
            db.conn.rollback()
            print(f"❌ Error deleting order: {e}")
            return False, f"Failed to delete order: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # APPROVE ORDER (extracted from OrdersDialog.approve_order())
    # -----------------------------------------------------------------------

    def approve_order(self, order_id: int, order_number: str):
        """
        Approve an order by setting its status to 'ordered'.

        Args:
            order_id (int): The ID of the order to approve.
            order_number (str): The order number (used for messages).

        Returns:
            tuple: (success: bool, message: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute(
                "UPDATE orders SET status = 'ordered' WHERE id = %s",
                (order_id,)
            )
            db.conn.commit()
            print(f"✅ Approved order {order_number}")
            return True, f"Order {order_number} approved. Status changed to 'ordered'."

        except Exception as e:
            print(f"❌ Error approving order: {e}")
            return False, f"Failed to approve order: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # GET ORDER DETAILS (extracted from OrdersDialog.view_order_details())
    # -----------------------------------------------------------------------

    def get_order_details(self, order_id: int, supplier_id: int):
        """
        Get full details for an order including items and supplier info.

        Args:
            order_id (int): The ID of the order.
            supplier_id (int): The supplier ID linked to the order.

        Returns:
            tuple: (success: bool, items: list, supplier: dict | None, error: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, [], None, "Failed to connect to database."

        try:
            db.cursor.execute("""
                SELECT oi.*, i.name as item_name, i.category, i.quantity as current_stock
                FROM order_items oi
                LEFT JOIN items i ON oi.item_id = i.id
                WHERE oi.order_id = %s
            """, (order_id,))
            items = db.cursor.fetchall()

            db.cursor.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
            supplier = db.cursor.fetchone()

            return True, items, supplier, ""

        except Exception as e:
            print(f"❌ Error loading order details: {e}")
            return False, [], None, f"Failed to load order details: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # LOAD INVENTORY ITEMS (extracted from OrderDialog.load_inventory_items())
    # -----------------------------------------------------------------------

    def get_inventory_items(self):
        """
        Get all inventory items for use in the order dialog dropdown.

        Returns:
            tuple: (success: bool, items: list, error: str)
        """
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, [], "Failed to connect to database."

        try:
            db.cursor.execute("""
                SELECT id, name, category, quantity, unit_price, supplier
                FROM items
                ORDER BY name
            """)
            items = db.cursor.fetchall()
            print(f"✅ Loaded {len(items)} inventory items for order dialog")
            return True, items, ""

        except Exception as e:
            print(f"❌ Error loading inventory items: {e}")
            return False, [], f"Failed to load items: {str(e)}"
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # FIND OR CREATE SUPPLIER (extracted from OrderDialog._find_supplier_by_name())
    # -----------------------------------------------------------------------

    def find_or_create_supplier(self, supplier_name: str):
        """
        Find a supplier by name using multiple matching strategies.
        If not found, creates a new supplier automatically.

        Args:
            supplier_name (str): The supplier name to search for.

        Returns:
            tuple: (supplier_id: int | None, supplier_name: str | None)
        """
        if not supplier_name or not supplier_name.strip():
            return None, None

        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return None, None

        try:
            normalized_input = self._normalize_supplier_name(supplier_name)
            print(f"🔍 Looking for supplier: '{supplier_name}' (normalized: '{normalized_input}')")

            # Strategy 1: Exact match (case-insensitive)
            db.cursor.execute(
                "SELECT id, name FROM suppliers WHERE LOWER(name) = LOWER(%s)",
                (supplier_name,)
            )
            result = db.cursor.fetchone()
            if result:
                print(f"✅ Found exact match: {result['name']} (ID: {result['id']})")
                return result['id'], result['name']

            # Strategy 2: Normalized match
            db.cursor.execute("SELECT id, name FROM suppliers")
            all_suppliers = db.cursor.fetchall()

            for supplier in all_suppliers:
                if self._normalize_supplier_name(supplier['name']) == normalized_input:
                    print(f"✅ Found normalized match: {supplier['name']} (ID: {supplier['id']})")
                    return supplier['id'], supplier['name']

            # Strategy 3: Partial/contains match
            for supplier in all_suppliers:
                normalized_db = self._normalize_supplier_name(supplier['name'])
                if normalized_input in normalized_db or normalized_db in normalized_input:
                    print(f"✅ Found partial match: {supplier['name']}")
                    return supplier['id'], supplier['name']

            # Strategy 4: Create new supplier
            print(f"❌ No supplier found for '{supplier_name}', creating new one...")
            try:
                db.cursor.execute("""
                    INSERT INTO suppliers (name, status, contact_person, phone, email, notes)
                    VALUES (%s, 'active', 'Auto-created', '', '', 'Auto-created from order dialog')
                """, (supplier_name,))
                db.conn.commit()
                supplier_id = db.cursor.lastrowid
                print(f"✅ Created new supplier: {supplier_name} (ID: {supplier_id})")
                return supplier_id, supplier_name

            except Exception as create_error:
                print(f"❌ Failed to create supplier: {create_error}")
                if "Duplicate entry" in str(create_error):
                    db.cursor.execute(
                        "SELECT id, name FROM suppliers WHERE name = %s",
                        (supplier_name,)
                    )
                    existing = db.cursor.fetchone()
                    if existing:
                        return existing['id'], existing['name']
                return None, None

        except Exception as e:
            print(f"❌ Error finding supplier: {e}")
            return None, None
        finally:
            db.disconnect()

    # -----------------------------------------------------------------------
    # HELPER
    # -----------------------------------------------------------------------

    def _normalize_supplier_name(self, name: str) -> str:
        """Normalize supplier name for fuzzy matching."""
        if not name:
            return ""
        normalized = name.lower()
        normalized = ' '.join(normalized.split())
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()