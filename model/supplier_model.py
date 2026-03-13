"""
Supplier Management System - Model
Handles supplier, order, and approval data operations
"""

from .database import DatabaseHandler


class Supplier:
    """Represents a supplier"""

    def __init__(self, supplier_id, name, contact_person, phone, email, address, status, notes, items_supplied_count=0,
                 items_list=""):
        self.id = supplier_id
        self.name = name
        self.contact_person = contact_person if contact_person is not None else ""
        self.phone = phone if phone is not None else ""
        self.email = email if email is not None else ""
        self.address = address if address is not None else ""
        self.status = status if status is not None else "active"
        self.notes = notes if notes is not None else ""
        self.items_supplied_count = items_supplied_count if items_supplied_count is not None else 0
        self.items_list = items_list if items_list is not None else ""

    @classmethod
    def from_db_row(cls, row):
        return cls(
            supplier_id=row['id'],
            name=row['name'],
            contact_person=row.get('contact_person', ''),
            phone=row.get('phone', ''),
            email=row.get('email', ''),
            address=row.get('address', ''),
            status=row.get('status', 'active'),
            notes=row.get('notes', ''),
            items_supplied_count=row.get('items_supplied_count', 0),
            items_list=row.get('items_list', '')
        )


class StockRequest:
    """Represents a stock approval request"""

    def __init__(self, request_id, item_id, item_name, item_category, request_type,
                 requested_quantity, current_quantity, reason, requested_by,
                 request_date, approved_by, approval_date, status, notes):
        self.id = request_id
        self.item_id = item_id
        self.item_name = item_name if item_name is not None else ""
        self.item_category = item_category if item_category is not None else ""
        self.request_type = request_type
        self.requested_quantity = requested_quantity
        self.current_quantity = current_quantity
        self.reason = reason if reason is not None else ""
        self.requested_by = requested_by
        self.request_date = request_date
        self.approved_by = approved_by if approved_by is not None else ""
        self.approval_date = approval_date
        self.status = status
        self.notes = notes if notes is not None else ""

    @classmethod
    def from_db_row(cls, row):
        return cls(
            request_id=row['id'],
            item_id=row['item_id'],
            item_name=row.get('item_name', ''),
            item_category=row.get('item_category', ''),
            request_type=row['request_type'],
            requested_quantity=row['requested_quantity'],
            current_quantity=row['current_quantity'],
            reason=row.get('reason', ''),
            requested_by=row['requested_by'],
            request_date=row['request_date'].strftime('%Y-%m-%d %H:%M') if row.get('request_date') else '',
            approved_by=row.get('approved_by', ''),
            approval_date=row['approval_date'].strftime('%Y-%m-%d %H:%M') if row.get('approval_date') else '',
            status=row['status'],
            notes=row.get('notes', '')
        )


class SupplierModel:
    """Main model class for supplier management"""

    def __init__(self, db_config=None):
        print(f"🔄 Initializing SupplierModel with config: {db_config}")

        if db_config is None:
            db_config = {
                'host': 'localhost',
                'database': 'inventoria_db',
                'user': 'root',
                'password': '',
                'port': 3308
            }

        self.db = DatabaseHandler(**db_config)
        if not self.db.connect():
            print("❌ Failed to connect to database in SupplierModel")
            self.db = None
            # Don't raise exception, just log and continue
        else:
            print("✅ SupplierModel database connected successfully")

    # ------------------- Supplier CRUD -------------------

    def add_supplier(self, name, contact_person, phone, email, address, notes=""):
        """Add a new supplier"""
        if self.db is None:
            print("❌ Cannot add supplier: Database not connected")
            return False

        return self.db.add_supplier(name, contact_person, phone, email, address, notes)

    def update_supplier(self, supplier_id, name, contact_person, phone, email, address, status, notes):
        """Update an existing supplier"""
        if self.db is None:
            print("❌ Cannot update supplier: Database not connected")
            return False

        return self.db.update_supplier(supplier_id, name, contact_person, phone, email, address, status, notes)

    def delete_supplier(self, supplier_id):
        """Delete a supplier - FIXED VERSION"""
        if self.db is None:
            print("❌ Cannot delete supplier: Database not connected")
            return False, "Database not connected"

        return self.db.delete_supplier(supplier_id)

    def get_all_suppliers(self):
        """Get all suppliers with item counts - SAFE VERSION"""
        if self.db is None:
            print("⚠️ Database not connected, returning empty suppliers list")
            return []

        try:
            db_suppliers = self.db.get_all_suppliers()

            if db_suppliers is None:
                print("⚠️ db.get_all_suppliers() returned None")
                return []

            suppliers = []
            for row in db_suppliers:
                # Ensure all fields have default values if None
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

                suppliers.append(Supplier.from_db_row(row))

            print(f"✅ Retrieved {len(suppliers)} suppliers from database")
            return suppliers

        except Exception as e:
            print(f"❌ Error in get_all_suppliers: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_supplier_by_id(self, supplier_id):
        """Get supplier by ID"""
        if self.db is None:
            print("❌ Cannot get supplier: Database not connected")
            return None

        db_supplier = self.db.get_supplier_by_id(supplier_id)
        if db_supplier:
            return Supplier.from_db_row(db_supplier)
        return None

    # ------------------- Stock Requests -------------------

    def create_stock_request(self, item_id, requested_quantity, requested_by, reason="", request_type="manual"):
        """Create a new stock request - FIXED VERSION"""
        if self.db is None:
            print("❌ Cannot create stock request: Database not connected")
            return None

        try:
            # Get current quantity
            self.db.cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
            item = self.db.cursor.fetchone()
            current_quantity = item['quantity'] if item else 0

            query = """
                INSERT INTO stock_requests 
                (item_id, request_type, requested_quantity, current_quantity, reason, requested_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """
            self.db.cursor.execute(query, (item_id, request_type, requested_quantity, current_quantity, reason, requested_by))
            self.db.conn.commit()
            request_id = self.db.cursor.lastrowid
            print(f"✅ Created stock request ID: {request_id} for item {item_id}")
            return request_id
        except Exception as e:
            print(f"❌ Create stock request error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_pending_approvals(self):
        """Get ALL stock requests (pending, approved, rejected) for Activity Log"""
        if self.db is None:
            print("⚠️ Database not connected, returning empty approvals list")
            return []

        try:
            # Use the new method that gets ALL requests
            db_approvals = self.db.get_all_stock_requests()

            if db_approvals is None:
                print("⚠️ db.get_all_stock_requests() returned None")
                return []

            approvals = []
            for row in db_approvals:
                # Ensure all fields have default values if None
                if row.get('reason') is None:
                    row['reason'] = ""
                if row.get('item_name') is None:
                    row['item_name'] = "Unknown Item"
                if row.get('item_category') is None:
                    row['item_category'] = "Unknown"
                if row.get('notes') is None:
                    row['notes'] = ""

                approvals.append(StockRequest.from_db_row(row))

            print(f"✅ Retrieved {len(approvals)} total requests from database")
            return approvals

        except Exception as e:
            print(f"❌ Error in get_pending_approvals: {e}")
            import traceback
            traceback.print_exc()
            return []

    def approve_stock_request(self, request_id, approved_by, notes=""):
        """Approve a stock request - FIXED VERSION"""
        if self.db is None:
            print("❌ Cannot approve stock request: Database not connected")
            return False

        try:
            # First get the request details
            self.db.cursor.execute("SELECT item_id, requested_quantity FROM stock_requests WHERE id = %s AND status = 'pending'", (request_id,))
            request = self.db.cursor.fetchone()

            if not request:
                print(f"❌ Request {request_id} not found or already processed")
                return False

            # Update stock in items table
            update_query = "UPDATE items SET quantity = quantity + %s WHERE id = %s"
            self.db.cursor.execute(update_query, (request['requested_quantity'], request['item_id']))

            # Update request status
            status_query = """
                UPDATE stock_requests 
                SET status='approved', approved_by=%s, approval_date=NOW(), notes=%s
                WHERE id=%s
            """
            self.db.cursor.execute(status_query, (approved_by, notes, request_id))

            self.db.conn.commit()
            print(f"✅ Approved stock request {request_id}, added {request['requested_quantity']} to item {request['item_id']}")
            return True
        except Exception as e:
            print(f"❌ Approve stock request error: {e}")
            self.db.conn.rollback()
            import traceback
            traceback.print_exc()
            return False

    def reject_stock_request(self, request_id, approved_by, notes=""):
        """Reject a stock request - FIXED VERSION"""
        if self.db is None:
            print("❌ Cannot reject stock request: Database not connected")
            return False

        try:
            query = """
                UPDATE stock_requests 
                SET status='rejected', approved_by=%s, approval_date=NOW(), notes=%s
                WHERE id=%s AND status = 'pending'
            """
            self.db.cursor.execute(query, (approved_by, notes, request_id))
            self.db.conn.commit()

            if self.db.cursor.rowcount > 0:
                print(f"✅ Rejected stock request {request_id}")
                return True
            else:
                print(f"❌ Request {request_id} not found or already processed")
                return False
        except Exception as e:
            print(f"❌ Reject stock request error: {e}")
            self.db.conn.rollback()
            return False

    # ------------------- Orders -------------------

    def create_order(self, supplier_id, order_number, created_by, notes="", expected_delivery=None):
        """Create a new order"""
        if self.db is None:
            print("❌ Cannot create order: Database not connected")
            return None

        return self.db.create_order(supplier_id, order_number, created_by, notes, expected_delivery)

    def add_order_item(self, order_id, item_id, quantity, unit_price):
        """Add item to an order"""
        if self.db is None:
            print("❌ Cannot add order item: Database not connected")
            return False

        return self.db.add_order_item(order_id, item_id, quantity, unit_price)

    def get_orders(self, status=None):
        """Get orders with optional status filter"""
        if self.db is None:
            print("❌ Cannot get orders: Database not connected")
            return []

        return self.db.get_orders(status)

    def close(self):
        """Close database connection"""
        if self.db:
            self.db.disconnect()
            print("✅ SupplierModel database connection closed")