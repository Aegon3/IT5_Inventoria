"""
Stock Issuance - Controller
Handles ALL stock issuance database operations.
NO QMessageBox imports - All UI alerts delegated to view.
"""

from model.stock_issuance_model import StockIssuance
from model.database import DatabaseHandler


class StockIssuanceController:
    """
    Controller for stock issuance operations.
    Handles ALL database operations - NO logic in models.
    """

    def __init__(self, inventory_model, view, db_config, username):
        self.inventory_model = inventory_model
        self.view = view
        self.db_config = db_config
        self.username = username

        self._create_table()
        self.view.stock_issuance_signal.connect(self.handle_issue_stock)
        self.refresh_item_list()
        self.refresh_issuances()

    def _get_connection(self):
        db = DatabaseHandler(**self.db_config)
        db.connect()
        return db

    def _create_table(self):
        db = self._get_connection()
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
        db.disconnect()

    def add_issuance(self, item_id, item_name, quantity, issued_by, notes=""):
        db = self._get_connection()
        db.cursor.execute(
            "INSERT INTO stock_issuances (item_id, item_name, quantity, issued_by, notes) "
            "VALUES (%s, %s, %s, %s, %s)",
            (item_id, item_name, quantity, issued_by, notes)
        )
        db.conn.commit()
        issuance_id = db.cursor.lastrowid
        db.disconnect()
        return issuance_id

    def get_all_issuances(self, limit=200):
        db = self._get_connection()
        db.cursor.execute(
            "SELECT * FROM stock_issuances ORDER BY issued_date DESC LIMIT %s",
            (limit,)
        )
        rows = db.cursor.fetchall()
        db.disconnect()
        return [StockIssuance.from_dict(r) for r in rows]

    def get_current_stock(self, item_id):
        db = self._get_connection()
        db.cursor.execute("SELECT quantity FROM items WHERE id = %s", (item_id,))
        row = db.cursor.fetchone()
        db.disconnect()
        return row['quantity'] if row else 0

    def deduct_stock(self, item_id, quantity):
        db = self._get_connection()
        db.cursor.execute(
            "UPDATE items SET quantity = quantity - %s WHERE id = %s AND quantity >= %s",
            (quantity, item_id, quantity)
        )
        db.conn.commit()
        success = db.cursor.rowcount > 0
        db.disconnect()
        return success

    def handle_issue_stock(self, item_id, item_name, quantity, notes):
        if not item_id:
            self.view.show_message("Warning", "Please select an item.", "warning")
            return

        if quantity <= 0:
            self.view.show_message("Warning", "Quantity must be greater than zero.", "warning")
            return

        current_stock = self.get_current_stock(item_id)
        if quantity > current_stock:
            self.view.show_message(
                "Insufficient Stock",
                f"Cannot issue {quantity} units of {item_name}.\n\nCurrent stock: {current_stock}",
                "warning"
            )
            return

        deducted = self.deduct_stock(item_id, quantity)
        if not deducted:
            self.view.show_message("Error", "Failed to deduct stock. Please try again.", "critical")
            return

        issuance_id = self.add_issuance(item_id, item_name, quantity, self.username, notes)

        if issuance_id:
            self.inventory_model.db.log_action(
                self.username,
                "Stock Issuance",
                f"Item: {item_name} | Qty: {quantity} | Notes: {notes}"
            )

            self.inventory_model.notify_observers()

            self.view.show_message(
                "Stock Issued",
                f"Stock issued successfully!\n\nItem: {item_name}\nQuantity: {quantity}",
                "information"
            )
            self.view.clear_issuance_form()
            self.refresh_issuances()
            self.refresh_item_list()
        else:
            self.view.show_message("Error", "Failed to record issuance.", "critical")

    def refresh_item_list(self):
        items = self.inventory_model.get_filtered_items()
        self.view.load_issuance_item_combo(items)

    def refresh_issuances(self):
        issuances = self.get_all_issuances()
        self.view.populate_issuance_table(issuances)