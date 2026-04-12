"""
Inventoria - Order Controller
Handles all order-related logic.
NO QMessageBox imports.
"""

import re
from model.database import DatabaseHandler


class OrderController:

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def get_orders(self, status_filter="All"):
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
            return True, orders, ""
        except Exception as e:
            return False, None, f"Failed to load orders: {str(e)}"
        finally:
            db.disconnect()

    def update_order_status(self, order_id: int, new_status: str):
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s",
                (new_status, order_id)
            )
            db.conn.commit()
            return True, f"Order status updated to '{new_status}'."
        except Exception as e:
            return False, f"Failed to update order status: {str(e)}"
        finally:
            db.disconnect()

    def delete_order(self, order_id: int, order_number: str):
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
            db.cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            db.conn.commit()
            return True, f"Order {order_number} deleted successfully."
        except Exception as e:
            db.conn.rollback()
            return False, f"Failed to delete order: {str(e)}"
        finally:
            db.disconnect()

    def approve_order(self, order_id: int, order_number: str):
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False, "Failed to connect to database."

        try:
            db.cursor.execute(
                "UPDATE orders SET status = 'ordered' WHERE id = %s",
                (order_id,)
            )
            db.conn.commit()
            return True, f"Order {order_number} approved. Status changed to 'ordered'."
        except Exception as e:
            return False, f"Failed to approve order: {str(e)}"
        finally:
            db.disconnect()

    def get_order_details(self, order_id: int, supplier_id: int):
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
            return False, [], None, f"Failed to load order details: {str(e)}"
        finally:
            db.disconnect()

    def get_inventory_items(self):
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
            return True, items, ""
        except Exception as e:
            return False, [], f"Failed to load items: {str(e)}"
        finally:
            db.disconnect()

    def find_or_create_supplier(self, supplier_name: str):
        if not supplier_name or not supplier_name.strip():
            return None, None

        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return None, None

        try:
            normalized_input = self._normalize_supplier_name(supplier_name)

            db.cursor.execute(
                "SELECT id, name FROM suppliers WHERE LOWER(name) = LOWER(%s)",
                (supplier_name,)
            )
            result = db.cursor.fetchone()
            if result:
                return result['id'], result['name']

            db.cursor.execute("SELECT id, name FROM suppliers")
            all_suppliers = db.cursor.fetchall()

            for supplier in all_suppliers:
                if self._normalize_supplier_name(supplier['name']) == normalized_input:
                    return supplier['id'], supplier['name']

            for supplier in all_suppliers:
                normalized_db = self._normalize_supplier_name(supplier['name'])
                if normalized_input in normalized_db or normalized_db in normalized_input:
                    return supplier['id'], supplier['name']

            try:
                db.cursor.execute("""
                    INSERT INTO suppliers (name, status, contact_person, phone, email, notes)
                    VALUES (%s, 'active', 'Auto-created', '', '', 'Auto-created from order dialog')
                """, (supplier_name,))
                db.conn.commit()
                supplier_id = db.cursor.lastrowid
                return supplier_id, supplier_name

            except Exception:
                db.cursor.execute(
                    "SELECT id, name FROM suppliers WHERE name = %s",
                    (supplier_name,)
                )
                existing = db.cursor.fetchone()
                if existing:
                    return existing['id'], existing['name']
                return None, None

        except Exception as e:
            return None, None
        finally:
            db.disconnect()

    def _normalize_supplier_name(self, name: str) -> str:
        if not name:
            return ""
        normalized = name.lower()
        normalized = ' '.join(normalized.split())
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()