"""
Damage Report - Model
Handles all damage report data operations.
Place in: model/damage_report_model.py
"""

from model.database import DatabaseHandler


class DamageReport:
    """Represents a single damage report record"""

    def __init__(self, report_id, reported_date, item_id, item_name, quantity, reason, reported_by):
        self.id = report_id
        self.reported_date = reported_date
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.reason = reason
        self.reported_by = reported_by

    @classmethod
    def from_db_row(cls, row):
        return cls(
            report_id=row['id'],
            reported_date=row['reported_date'].strftime('%Y-%m-%d %H:%M') if row.get('reported_date') else '',
            item_id=row['item_id'],
            item_name=row.get('item_name', ''),
            quantity=row['quantity'],
            reason=row.get('reason', ''),
            reported_by=row.get('reported_by', '')
        )


class DamageReportModel:
    """Model class for damage report operations"""

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
        """Create damage_reports table if it does not exist"""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            print(" Cannot create damage_reports table: DB not connected")
            return
        try:
            db.cursor.execute("""
                CREATE TABLE IF NOT EXISTS damage_reports (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    reported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    item_id INT NOT NULL,
                    item_name VARCHAR(255) NOT NULL,
                    quantity INT NOT NULL,
                    reason TEXT NOT NULL,
                    reported_by VARCHAR(50) NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            db.conn.commit()
            print(" damage_reports table ready")
        except Exception as e:
            print(f" Create damage_reports table error: {e}")
        finally:
            db.disconnect()

    def add_report(self, item_id, item_name, quantity, reason, reported_by):
        """Insert a new damage report. Returns report_id or None."""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return None
        try:
            db.cursor.execute(
                "INSERT INTO damage_reports (item_id, item_name, quantity, reason, reported_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (item_id, item_name, quantity, reason, reported_by)
            )
            db.conn.commit()
            return db.cursor.lastrowid
        except Exception as e:
            print(f" Add damage report error: {e}")
            return None
        finally:
            db.disconnect()

    def get_all_reports(self, limit=200):
        """Fetch all damage reports newest first. Returns list of DamageReport."""
        db = DatabaseHandler(**self.db_config)
        if not db.connect():
            return []
        try:
            db.cursor.execute(
                "SELECT * FROM damage_reports ORDER BY reported_date DESC LIMIT %s",
                (limit,)
            )
            rows = db.cursor.fetchall()
            return [DamageReport.from_db_row(r) for r in rows]
        except Exception as e:
            print(f" Get damage reports error: {e}")
            return []
        finally:
            db.disconnect()