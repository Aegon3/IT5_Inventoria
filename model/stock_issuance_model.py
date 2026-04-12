"""
Stock Issuance - Model
Handles all stock issuance data operations.
Place in: model/stock_issuance_model.py
"""

from model.database import DatabaseHandler



class StockIssuance:
    """Represents a single stock issuance record"""

    def __init__(self, issuance_id, issued_date, item_id, item_name,
                 quantity, issued_by, notes):
        self.id = issuance_id
        self.issued_date = issued_date
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.issued_by = issued_by
        self.notes = notes

    @classmethod
    def from_db_row(cls, row):
        return cls(
            issuance_id=row['id'],
            issued_date=row['issued_date'].strftime('%Y-%m-%d %H:%M') if row.get('issued_date') else '',
            item_id=row['item_id'],
            item_name=row.get('item_name', ''),
            quantity=row['quantity'],
            issued_by=row.get('issued_by', ''),
            notes=row.get('notes', '')
        )


class StockIssuanceModel:
    """Model class for stock issuance operations"""

    def __init__(self, db_config=None):
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'database': 'inventoria_db',
                'user': 'root',
                'password': '',
                'port': 3308
            }
        self.db_config = db_config

    def create_table(self):
        """Create stock_issuances table if it does not exist"""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            print(" Cannot create stock_issuances table: DB not connected")
            return
        try:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_issuances (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    item_id INT NOT NULL,
                    item_name VARCHAR(255) NOT NULL,
                    quantity INT NOT NULL,
                    issued_by VARCHAR(50) NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            db.conn.commit()
            print(" stock_issuances table ready")
        except Exception as e:
            print(f" Create stock_issuances table error: {e}")
        finally:
            db.disconnect()

    def add_issuance(self, item_id, item_name, quantity, issued_by, notes=""):
        """Insert a new stock issuance record. Returns issuance_id or None."""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return None
        try:
            db.cursor.execute(
                "INSERT INTO stock_issuances (item_id, item_name, quantity, issued_by, notes) "
                "VALUES (%s, %s, %s, %s, %s)",
                (item_id, item_name, quantity, issued_by, notes)
            )
            db.conn.commit()
            return db.cursor.lastrowid
        except Exception as e:
            print(f" Add issuance error: {e}")
            return None
        finally:
            db.disconnect()

    def get_all_issuances(self, limit=200):
        """Fetch all issuances newest first. Returns list of StockIssuance."""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return []
        try:
            db.cursor.execute(
                "SELECT * FROM stock_issuances ORDER BY issued_date DESC LIMIT %s",
                (limit,)
            )
            rows = db.cursor.fetchall()
            return [StockIssuance.from_db_row(r) for r in rows]
        except Exception as e:
            print(f" Get issuances error: {e}")
            return []
        finally:
            db.disconnect()

    def get_current_stock(self, item_id):
        """Get current quantity of an item"""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return 0
        try:
            db.cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
            row = db.cursor.fetchone()
            return row['quantity'] if row else 0
        except Exception as e:
            print(f" Get current stock error: {e}")
            return 0
        finally:
            db.disconnect()

    def deduct_stock(self, item_id, quantity):
        """Deduct stock from items table after issuance"""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return False
        try:
            db.cursor.execute(
                "UPDATE items SET quantity = quantity - %s WHERE id = %s AND quantity >= %s",
                (quantity, item_id, quantity)
            )
            db.conn.commit()
            return db.cursor.rowcount > 0
        except Exception as e:
            print(f" Deduct stock error: {e}")
            return False
        finally:
            db.disconnect()