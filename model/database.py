"""
Database Handler for Inventoria
"""

import mysql.connector
from mysql.connector import Error


class DatabaseHandler:
    def __init__(self, host='localhost', user='root', password='', database='inventoria_db', port=3308):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except Error as e:
            print(f"Database connection error: {e}")
            return False

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    # ------------------- Table Creation -------------------
    def create_tables(self):
        """Create tables if they don't exist"""
        try:
            # Users table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                role VARCHAR(50)
            )
            """)

            # Items table
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                quantity INT DEFAULT 0,
                min_stock INT DEFAULT 0,
                unit_price DECIMAL(10,2) DEFAULT 0.00,
                supplier VARCHAR(255)
            )
            """)

            # ========== NEW TABLES FOR SUPPLIERS & APPROVALS ==========

            # 1. SUPPLIERS TABLE
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE,
                contact_person VARCHAR(100),
                phone VARCHAR(20),
                email VARCHAR(100),
                address TEXT,
                status ENUM('active', 'inactive') DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 2. ITEM_SUPPLIER LINK TABLE (Many-to-Many)
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_suppliers (
                item_id INT,
                supplier_id INT,
                is_primary BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (item_id, supplier_id),
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
            )
            """)

            # 3. ORDERS TABLE
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE,
                supplier_id INT,
                order_date DATE DEFAULT (CURRENT_DATE),
                expected_delivery DATE,
                status ENUM('draft', 'pending', 'ordered', 'delivered', 'cancelled') DEFAULT 'draft',
                total_amount DECIMAL(10,2) DEFAULT 0.00,
                notes TEXT,
                created_by VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
            """)

            # 4. ORDER_ITEMS TABLE
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT,
                item_id INT,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2),
                total_price DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
                status ENUM('pending', 'approved', 'received', 'cancelled') DEFAULT 'pending',
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """)

            # 5. STOCK_REQUESTS TABLE (Approval Workflow)
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_id INT,
                request_type ENUM('manual', 'low_stock', 'order') DEFAULT 'manual',
                requested_quantity INT NOT NULL,
                current_quantity INT,
                reason TEXT,
                requested_by VARCHAR(50),
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_by VARCHAR(50) NULL,
                approval_date TIMESTAMP NULL,
                status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
            """)
            # 6. ACTIVITY LOG TABLE
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(50) NOT NULL,
                action VARCHAR(100) NOT NULL,
                details TEXT,
                INDEX idx_timestamp (timestamp)
            )
            """)
            # ========== END OF NEW TABLES ==========

            self.conn.commit()
        except Error as e:
            print(f"Create tables error: {e}")

    # ------------------- Activity Log -------------------
    def log_action(self, username, action, details=""):
        """Insert a record into activity_log"""
        try:
            self.cursor.execute(
                "INSERT INTO activity_log (username, action, details) VALUES (%s, %s, %s)",
                (username, action, details)
            )
            self.conn.commit()
        except Error as e:
            print(f"Activity log error: {e}")

    def get_activity_log(self, limit=200):
        """Fetch recent activity log entries, newest first"""
        try:
            self.cursor.execute(
                "SELECT id, timestamp, username, action, details FROM activity_log ORDER BY timestamp DESC LIMIT %s",
                (limit,)
            )
            return self.cursor.fetchall()
        except Error as e:
            print(f"Get activity log error: {e}")
            return []

    # ------------------- Authentication -------------------
    def authenticate_user(self, username, password):
        """Authenticate user against database"""
        query = "SELECT username, full_name, role, password FROM users WHERE username=%s AND password=%s"
        self.cursor.execute(query, (username, password))
        user = self.cursor.fetchone()
        return user

    # ------------------- Inventory CRUD -------------------
    def is_empty(self):
        self.cursor.execute("SELECT COUNT(*) as count FROM items")
        result = self.cursor.fetchone()
        return result['count'] == 0

    def add_item(self, name, category, quantity, min_stock, unit_price, supplier):
        try:
            query = """
                INSERT INTO items (name, category, quantity, min_stock, unit_price, supplier)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, category, quantity, min_stock, unit_price, supplier))
            self.conn.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Add item error: {e}")
            return None

    def update_item(self, item_id, name, category, quantity, min_stock, unit_price, supplier):
        try:
            query = """
                UPDATE items
                SET name=%s, category=%s, quantity=%s, min_stock=%s, unit_price=%s, supplier=%s
                WHERE id=%s
            """
            self.cursor.execute(query, (name, category, quantity, min_stock, unit_price, supplier, item_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Update item error: {e}")
            return False

    def delete_item(self, item_id):
        try:
            query = "DELETE FROM items WHERE id=%s"
            self.cursor.execute(query, (item_id,))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Delete item error: {e}")
            return False

    def adjust_stock(self, item_id, adjustment):
        try:
            query = "UPDATE items SET quantity = quantity + %s WHERE id=%s"
            self.cursor.execute(query, (adjustment, item_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Adjust stock error: {e}")
            return False

    # ------------------- NEW SUPPLIER METHODS -------------------
    def add_supplier(self, name, contact_person, phone, email, address, notes=""):
        try:
            query = """
                INSERT INTO suppliers (name, contact_person, phone, email, address, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (name, contact_person, phone, email, address, notes))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Add supplier error: {e}")
            return False

    def update_supplier(self, supplier_id, name, contact_person, phone, email, address, status, notes):
        try:
            query = """
                UPDATE suppliers 
                SET name=%s, contact_person=%s, phone=%s, email=%s, 
                    address=%s, status=%s, notes=%s
                WHERE id=%s
            """
            self.cursor.execute(query, (name, contact_person, phone, email, address, status, notes, supplier_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Update supplier error: {e}")
            return False

    def delete_supplier(self, supplier_id):
        """Delete a supplier - FIXED VERSION"""
        try:
            # First, check if supplier exists in orders
            self.cursor.execute("SELECT COUNT(*) as order_count FROM orders WHERE supplier_id = %s", (supplier_id,))
            order_result = self.cursor.fetchone()

            if order_result['order_count'] > 0:
                # Supplier has orders, mark as inactive instead of hard delete
                query = "UPDATE suppliers SET status='inactive' WHERE id=%s"
                self.cursor.execute(query, (supplier_id,))
                self.conn.commit()
                return True, "Supplier removed from list (had existing orders, marked inactive)"
            else:
                # Delete from item_suppliers first (foreign key constraint)
                self.cursor.execute("DELETE FROM item_suppliers WHERE supplier_id = %s", (supplier_id,))

                # Then delete supplier
                query = "DELETE FROM suppliers WHERE id=%s"
                self.cursor.execute(query, (supplier_id,))
                self.conn.commit()
                return True, "Supplier deleted successfully"
        except Error as e:
            print(f"Delete supplier error: {e}")
            return False, str(e)

    def get_all_suppliers(self):
        """Get all suppliers with item counts - FIXED"""
        try:
            query = """
                SELECT s.*, 
                       COUNT(isup.item_id) as items_supplied_count,
                       GROUP_CONCAT(DISTINCT i.name SEPARATOR ', ') as items_list
                FROM suppliers s
                LEFT JOIN item_suppliers isup ON s.id = isup.supplier_id
                LEFT JOIN items i ON isup.item_id = i.id
                WHERE s.status != 'inactive'
                GROUP BY s.id
                ORDER BY s.name
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Get all suppliers error: {e}")
            return []

    def get_supplier_by_id(self, supplier_id):
        query = "SELECT * FROM suppliers WHERE id = %s"
        self.cursor.execute(query, (supplier_id,))
        return self.cursor.fetchone()

    def get_supplier_items(self, supplier_id):
        """Get items supplied by a specific supplier"""
        try:
            query = """
                SELECT i.name, i.category, i.quantity, isup.is_primary
                FROM items i
                JOIN item_suppliers isup ON i.id = isup.item_id
                WHERE isup.supplier_id = %s
                ORDER BY isup.is_primary DESC, i.name
            """
            self.cursor.execute(query, (supplier_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"Get supplier items error: {e}")
            return []

    # ------------------- NEW ORDER METHODS -------------------
    def create_order(self, supplier_id, order_number, created_by, notes="", expected_delivery=None):
        try:
            query = """
                INSERT INTO orders (supplier_id, order_number, created_by, notes, expected_delivery)
                VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (supplier_id, order_number, created_by, notes, expected_delivery))
            self.conn.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Create order error: {e}")
            return None

    def add_order_item(self, order_id, item_id, quantity, unit_price):
        try:
            query = """
                INSERT INTO order_items (order_id, item_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (order_id, item_id, quantity, unit_price))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Add order item error: {e}")
            return False

    def get_orders(self, status=None):
        query = "SELECT * FROM orders"
        if status:
            query += " WHERE status = %s"
            self.cursor.execute(query, (status,))
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    # ------------------- NEW STOCK REQUEST METHODS -------------------
    def create_stock_request(self, item_id, requested_quantity, requested_by, reason="", request_type="manual"):
        try:
            # Get current quantity
            self.cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
            item = self.cursor.fetchone()
            current_quantity = item['quantity'] if item else 0

            query = """
                INSERT INTO stock_requests 
                (item_id, request_type, requested_quantity, current_quantity, reason, requested_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (item_id, request_type, requested_quantity, current_quantity, reason, requested_by))
            self.conn.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"Create stock request error: {e}")
            return None

    def get_pending_stock_requests(self):
        query = """
            SELECT sr.*, i.name as item_name, i.category as item_category
            FROM stock_requests sr
            JOIN items i ON sr.item_id = i.id
            WHERE sr.status = 'pending'
            ORDER BY sr.request_date DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_all_stock_requests(self):
        """Get ALL stock requests (pending, approved, rejected) for Activity Log"""
        query = """
            SELECT sr.*, i.name as item_name, i.category as item_category
            FROM stock_requests sr
            JOIN items i ON sr.item_id = i.id
            ORDER BY sr.request_date DESC
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def approve_stock_request(self, request_id, approved_by, notes=""):
        try:
            # First get the request details
            query = "SELECT item_id, requested_quantity FROM stock_requests WHERE id = %s"
            self.cursor.execute(query, (request_id,))
            request = self.cursor.fetchone()

            if not request:
                return False

            # Update stock
            update_query = "UPDATE items SET quantity = quantity + %s WHERE id = %s"
            self.cursor.execute(update_query, (request['requested_quantity'], request['item_id']))

            # Update request status
            status_query = """
                UPDATE stock_requests 
                SET status='approved', approved_by=%s, approval_date=NOW(), notes=%s
                WHERE id=%s
            """
            self.cursor.execute(status_query, (approved_by, notes, request_id))

            self.conn.commit()
            return True
        except Error as e:
            print(f"Approve stock request error: {e}")
            return False

    def reject_stock_request(self, request_id, approved_by, notes=""):
        try:
            query = """
                UPDATE stock_requests 
                SET status='rejected', approved_by=%s, approval_date=NOW(), notes=%s
                WHERE id=%s
            """
            self.cursor.execute(query, (approved_by, notes, request_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Reject stock request error: {e}")
            return False

    # ------------------- Bulk Operations -------------------
    def bulk_insert_items(self, items_data):
        """Insert multiple items at once"""
        try:
            query = """
                INSERT INTO items (name, category, quantity, min_stock, unit_price, supplier)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.executemany(query, items_data)
            self.conn.commit()
            return True
        except Error as e:
            print(f"Bulk insert error: {e}")
            return False

    def get_item_by_name(self, name):
        """Get item by exact name match"""
        query = "SELECT * FROM items WHERE name = %s"
        self.cursor.execute(query, (name,))
        return self.cursor.fetchone()

    def item_exists(self, name):
        """Check if item exists by name"""
        query = "SELECT COUNT(*) as count FROM items WHERE name = %s"
        self.cursor.execute(query, (name,))
        result = self.cursor.fetchone()
        return result['count'] > 0

    def supplier_exists(self, supplier_id):
        """Check if supplier exists"""
        query = "SELECT COUNT(*) as count FROM suppliers WHERE id = %s"
        self.cursor.execute(query, (supplier_id,))
        result = self.cursor.fetchone()
        return result['count'] > 0

    def get_all_categories(self):
        """Get all unique categories"""
        query = "SELECT DISTINCT category FROM items ORDER BY category"
        self.cursor.execute(query)
        return [row['category'] for row in self.cursor.fetchall()]

    # ------------------- Queries -------------------
    def get_all_items(self):
        query = "SELECT * FROM items"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_filtered_items(self, search_text="", category="All"):
        sql = "SELECT * FROM items WHERE name LIKE %s"
        params = [f"%{search_text}%"]
        if category != "All":
            sql += " AND category=%s"
            params.append(category)
        self.cursor.execute(sql, tuple(params))
        return self.cursor.fetchall()

    def get_low_stock_items(self):
        query = "SELECT *, (min_stock - quantity) as shortage FROM items WHERE quantity < min_stock"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_statistics(self):
        stats = {}
        self.cursor.execute("SELECT COUNT(*) as total_items FROM items")
        stats['total_items'] = self.cursor.fetchone()['total_items']

        self.cursor.execute("SELECT SUM(quantity*unit_price) as total_value FROM items")
        result = self.cursor.fetchone()['total_value']
        stats['total_value'] = float(result) if result else 0.0

        self.cursor.execute("SELECT COUNT(*) as low_stock_count FROM items WHERE quantity < min_stock")
        stats['low_stock_count'] = self.cursor.fetchone()['low_stock_count']

        self.cursor.execute("SELECT category, COUNT(*) as count FROM items GROUP BY category")
        categories = {row['category']: row['count'] for row in self.cursor.fetchall()}
        stats['categories'] = categories

        return stats