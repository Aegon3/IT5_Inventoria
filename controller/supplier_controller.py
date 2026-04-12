"""
Supplier Management System - Controller
Handles ALL supplier, order, and approval database operations.
NO QMessageBox imports.
"""

from model.supplier_model import Supplier, StockRequest
from model.database import DatabaseHandler


class SupplierController:

    STATUS_COLORS = {
        'DRAFT':     '#95A5A6',
        'PENDING':   '#F39C12',
        'ORDERED':   '#3498DB',
        'DELIVERED': '#27AE60',
        'CANCELLED': '#E74C3C',
    }

    def __init__(self, db_config):
        self.db_config = db_config

    def _get_connection(self):
        db = DatabaseHandler(**self.db_config)
        db.connect()
        return db

    def add_supplier(self, name, contact_person, phone, email, address, notes=""):
        db = self._get_connection()
        db.cursor.execute("""
            INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, contact_person, phone, email, address, notes))
        db.conn.commit()
        db.disconnect()
        return True

    def update_supplier(self, supplier_id, name, contact_person, phone, email, address, status, notes):
        db = self._get_connection()
        db.cursor.execute("""
            UPDATE suppliers 
            SET name=%s, contact_person=%s, phone=%s, email=%s, 
                address=%s, status=%s, notes=%s
            WHERE id=%s
        """, (name, contact_person, phone, email, address, status, notes, supplier_id))
        db.conn.commit()
        db.disconnect()
        return True

    def delete_supplier(self, supplier_id):
        db = self._get_connection()
        db.cursor.execute("SELECT COUNT(*) as order_count FROM orders WHERE supplier_id = %s", (supplier_id,))
        order_result = db.cursor.fetchone()

        if order_result['order_count'] > 0:
            db.cursor.execute("UPDATE suppliers SET status='inactive' WHERE id=%s", (supplier_id,))
            db.conn.commit()
            message = "Supplier removed from list (had existing orders, marked inactive)"
        else:
            db.cursor.execute("DELETE FROM item_suppliers WHERE supplier_id = %s", (supplier_id,))
            db.cursor.execute("DELETE FROM suppliers WHERE id=%s", (supplier_id,))
            db.conn.commit()
            message = "Supplier deleted successfully"

        db.disconnect()
        return True, message

    def get_all_suppliers(self):
        db = self._get_connection()
        db.cursor.execute("""
            SELECT s.*, 
                   COUNT(isup.item_id) as items_supplied_count,
                   GROUP_CONCAT(DISTINCT i.name SEPARATOR ', ') as items_list
            FROM suppliers s
            LEFT JOIN item_suppliers isup ON s.id = isup.supplier_id
            LEFT JOIN items i ON isup.item_id = i.id
            WHERE s.status != 'inactive'
            GROUP BY s.id
            ORDER BY s.name
        """)
        rows = db.cursor.fetchall()
        db.disconnect()
        suppliers = []
        for row in rows:
            if row.get('address') is None:
                row['address'] = ""
            if row.get('contact_person') is None:
                row['contact_person'] = ""
            if row.get('phone') is None:
                row['phone'] = ""
            if row.get('email') is None:
                row['email'] = ""
            if row.get('status') is None:
                row['status'] = "active"
            if row.get('items_list') is None:
                row['items_list'] = ""
            suppliers.append(Supplier.from_dict(row))
        return suppliers

    def get_supplier_by_id(self, supplier_id):
        db = self._get_connection()
        db.cursor.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        row = db.cursor.fetchone()
        db.disconnect()
        if row:
            return Supplier.from_dict(row)
        return None

    def get_active_suppliers(self):
        db = self._get_connection()
        db.cursor.execute("SELECT id, name FROM suppliers WHERE status = 'active' ORDER BY name")
        rows = db.cursor.fetchall()
        db.disconnect()
        return [{'id': r['id'], 'name': r['name']} for r in rows]

    def get_supplier_items(self, supplier_id):
        db = self._get_connection()
        db.cursor.execute("""
            SELECT i.name, i.category, i.quantity, isup.is_primary
            FROM items i
            JOIN item_suppliers isup ON i.id = isup.item_id
            WHERE isup.supplier_id = %s
            ORDER BY isup.is_primary DESC, i.name
        """, (supplier_id,))
        rows = db.cursor.fetchall()
        db.disconnect()
        return rows

    def create_stock_request(self, item_id, requested_quantity, requested_by, reason="", request_type="manual"):
        db = self._get_connection()
        db.cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
        item = db.cursor.fetchone()
        current_quantity = item['quantity'] if item else 0

        db.cursor.execute("""
            INSERT INTO stock_requests 
            (item_id, request_type, requested_quantity, current_quantity, reason, requested_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        """, (item_id, request_type, requested_quantity, current_quantity, reason, requested_by))
        db.conn.commit()
        request_id = db.cursor.lastrowid
        db.disconnect()
        return request_id

    def get_all_stock_requests(self):
        db = self._get_connection()
        db.cursor.execute("""
            SELECT sr.*, i.name as item_name, i.category as item_category
            FROM stock_requests sr
            JOIN items i ON sr.item_id = i.id
            ORDER BY sr.request_date DESC
        """)
        rows = db.cursor.fetchall()
        db.disconnect()
        requests = []
        for row in rows:
            if row.get('reason') is None:
                row['reason'] = ""
            if row.get('item_name') is None:
                row['item_name'] = "Unknown Item"
            if row.get('item_category') is None:
                row['item_category'] = "Unknown"
            if row.get('notes') is None:
                row['notes'] = ""
            requests.append(StockRequest.from_dict(row))
        return requests

    def get_pending_approvals(self):
        db = self._get_connection()
        db.cursor.execute("""
            SELECT sr.*, i.name as item_name, i.category as item_category
            FROM stock_requests sr
            JOIN items i ON sr.item_id = i.id
            ORDER BY sr.request_date DESC
        """)
        rows = db.cursor.fetchall()
        db.disconnect()
        requests = []
        for row in rows:
            if row.get('reason') is None:
                row['reason'] = ""
            if row.get('item_name') is None:
                row['item_name'] = "Unknown Item"
            if row.get('item_category') is None:
                row['item_category'] = "Unknown"
            if row.get('notes') is None:
                row['notes'] = ""
            requests.append(StockRequest.from_dict(row))
        return requests

    def approve_stock_request(self, request_id, approved_by, notes=""):
        db = self._get_connection()
        db.cursor.execute("SELECT item_id, requested_quantity FROM stock_requests WHERE id = %s AND status = 'pending'", (request_id,))
        request = db.cursor.fetchone()

        if not request:
            db.disconnect()
            return False

        db.cursor.execute("UPDATE items SET quantity = quantity + %s WHERE id = %s",
                         (request['requested_quantity'], request['item_id']))
        db.cursor.execute("""
            UPDATE stock_requests 
            SET status='approved', approved_by=%s, approval_date=NOW(), notes=%s
            WHERE id=%s
        """, (approved_by, notes, request_id))
        db.conn.commit()
        db.disconnect()
        return True

    def reject_stock_request(self, request_id, approved_by, notes=""):
        db = self._get_connection()
        db.cursor.execute("""
            UPDATE stock_requests 
            SET status='rejected', approved_by=%s, approval_date=NOW(), notes=%s
            WHERE id=%s AND status = 'pending'
        """, (approved_by, notes, request_id))
        db.conn.commit()
        success = db.cursor.rowcount > 0
        db.disconnect()
        return success

    def create_order(self, supplier_id, order_number, created_by, notes="", expected_delivery=None):
        db = self._get_connection()
        db.cursor.execute("""
            INSERT INTO orders (supplier_id, order_number, created_by, notes, expected_delivery)
            VALUES (%s, %s, %s, %s, %s)
        """, (supplier_id, order_number, created_by, notes, expected_delivery))
        db.conn.commit()
        order_id = db.cursor.lastrowid
        db.disconnect()
        return order_id

    def add_order_item(self, order_id, item_id, quantity, unit_price):
        db = self._get_connection()
        db.cursor.execute("""
            INSERT INTO order_items (order_id, item_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item_id, quantity, unit_price))
        db.conn.commit()
        db.disconnect()
        return True

    def get_orders(self, status=None):
        db = self._get_connection()
        if status and status != "All":
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
            db.cursor.execute(query, (status,))
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
        db.disconnect()
        return orders

    def close(self):
        pass

    @staticmethod
    def get_status_color(status: str) -> str:
        return SupplierController.STATUS_COLORS.get(status.upper(), '#95A5A6')

    @staticmethod
    def get_active_suppliers_static():
        try:
            from model.database import DatabaseHandler
            db_config = {
                'host': 'localhost',
                'database': 'inventoria_db',
                'user': 'root',
                'password': '',
                'port': 3308
            }
            db = DatabaseHandler(**db_config)
            if not db.connect():
                return []
            db.cursor.execute("SELECT id, name FROM suppliers WHERE status = 'active' ORDER BY name")
            suppliers = db.cursor.fetchall()
            db.disconnect()
            return [{'id': s['id'], 'name': s['name']} for s in suppliers]
        except Exception as e:
            print(f"SupplierController.get_active_suppliers error: {e}")
            return []

    @staticmethod
    def build_order_details_html(order: dict, items: list, supplier: dict) -> str:
        order_date = order['order_date'].strftime('%Y-%m-%d') if order['order_date'] else 'N/A'
        expected_date = order['expected_delivery'].strftime('%Y-%m-%d') if order['expected_delivery'] else 'N/A'
        supplier_name = supplier['name'] if supplier else 'Unknown'
        supplier_contact = supplier['contact_person'] if supplier else 'N/A'
        supplier_phone = supplier['phone'] if supplier else 'N/A'
        supplier_email = supplier['email'] if supplier else 'N/A'

        html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; }}
            h3 {{ color: #2C3E50; margin-top: 0; }}
            h4 {{ color: #3498DB; margin-top: 15px; }}
            .section {{ margin-bottom: 15px; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #000; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; text-align: left; }}
            td {{ padding: 8px; border: 1px solid #ddd; }}
            .total-row {{ background-color: #e8f4fd; font-weight: bold; }}
            .status-ordered {{ color: #3498DB; }}
            .status-delivered {{ color: #27AE60; }}
            .status-cancelled {{ color: #E74C3C; }}
        </style>
        </head>
        <body>
        <div class="section">
            <h3>Order Details: {order['order_number']}</h3>
            <p><span class="label">Supplier:</span> <span class="value">{supplier_name}</span></p>
            <p><span class="label">Contact:</span> <span class="value">{supplier_contact}</span></p>
            <p><span class="label">Phone:</span> <span class="value">{supplier_phone}</span></p>
            <p><span class="label">Email:</span> <span class="value">{supplier_email}</span></p>
            <p><span class="label">Order Date:</span> <span class="value">{order_date}</span></p>
            <p><span class="label">Expected Delivery:</span> <span class="value">{expected_date}</span></p>
            <p><span class="label">Status:</span> <span class="value status-{order['status']}"><b>{order['status'].upper()}</b></span></p>
            <p><span class="label">Created By:</span> <span class="value">{order['created_by']}</span></p>
            <p><span class="label">Notes:</span> <span class="value">{order['notes'] or 'None'}</span></p>
        </div>
        <div class="section">
            <h4>Order Items ({len(items)} items):</h4>
        """

        if items:
            html += """
            <table>
                <tr>
                    <th>Item Name</th>
                    <th>Category</th>
                    <th>Current Stock</th>
                    <th>Order Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Price</th>
                </tr>
            """
            total_amount = 0
            for item in items:
                item_total = item['quantity'] * float(item['unit_price'])
                total_amount += item_total
                html += f"""
                <tr>
                    <td>{item.get('item_name', 'Unknown')}</td>
                    <td>{item.get('category', 'N/A')}</td>
                    <td style='text-align: center;'>{item.get('current_stock', 0)}</td>
                    <td style='text-align: center;'>{item['quantity']}</td>
                    <td style='text-align: right;'>&#8369;{float(item['unit_price']):.2f}</td>
                    <td style='text-align: right;'>&#8369;{item_total:.2f}</td>
                </tr>
                """
            html += f"""
                <tr class="total-row">
                    <td colspan="5" style="text-align: right;">Grand Total:</td>
                    <td style="text-align: right;">&#8369;{total_amount:.2f}</td>
                </tr>
            </table>
            """
        else:
            html += "<p>No items found in this order.</p>"

        if supplier and supplier.get('address'):
            html += f"""
            <div class="section">
                <h4>Supplier Address:</h4>
                <p>{supplier['address']}</p>
            </div>
            """

        html += "</body></html>"
        return html