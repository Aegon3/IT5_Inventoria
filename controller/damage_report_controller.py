"""
Damage Report - Controller
Handles ALL damage report database operations.
NO QMessageBox imports - All UI alerts delegated to view.
"""

from model.damage_report_model import DamageReport
from model.database import DatabaseHandler


class DamageReportController:
    """
    Controller for damage report operations.
    Handles ALL database operations - NO logic in models.
    """

    def __init__(self, inventory_model, view, db_config, username):
        self.inventory_model = inventory_model
        self.view = view
        self.db_config = db_config
        self.username = username

        self._create_table()
        self.view.damage_report_signal.connect(self.handle_submit_report)
        self.refresh_item_list()
        self.refresh_reports()

    def _get_connection(self):
        db = DatabaseHandler(**self.db_config)
        db.connect()
        return db

    def _create_table(self):
        db = self._get_connection()
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
        db.disconnect()

    def add_report(self, item_id, item_name, quantity, reason, reported_by):
        db = self._get_connection()
        db.cursor.execute(
            "INSERT INTO damage_reports (item_id, item_name, quantity, reason, reported_by) "
            "VALUES (%s, %s, %s, %s, %s)",
            (item_id, item_name, quantity, reason, reported_by)
        )
        db.conn.commit()
        report_id = db.cursor.lastrowid
        db.disconnect()
        return report_id

    def get_all_reports(self, limit=200):
        db = self._get_connection()
        db.cursor.execute(
            "SELECT * FROM damage_reports ORDER BY reported_date DESC LIMIT %s",
            (limit,)
        )
        rows = db.cursor.fetchall()
        db.disconnect()
        return [DamageReport.from_dict(r) for r in rows]

    def handle_submit_report(self, item_id, item_name, quantity, reason):
        if not item_id:
            self.view.show_message("Warning", "Please select an item.", "warning")
            return

        if not reason.strip():
            self.view.show_message("Warning", "Please enter a reason.", "warning")
            return

        if quantity <= 0:
            self.view.show_message("Warning", "Quantity must be greater than zero.", "warning")
            return

        report_id = self.add_report(item_id, item_name, quantity, reason.strip(), self.username)

        if report_id:
            self.inventory_model.db.log_action(
                self.username,
                "Damage Report",
                f"Item: {item_name} | Qty: {quantity} | Reason: {reason.strip()}"
            )

            self.view.show_message(
                "Report Submitted",
                f"Damage report submitted successfully!\n\nItem: {item_name}\nQuantity: {quantity}\nReason: {reason}",
                "information"
            )
            self.view.clear_damage_form()
            self.refresh_reports()
        else:
            self.view.show_message("Error", "Failed to submit damage report.", "critical")

    def refresh_item_list(self):
        items = self.inventory_model.get_filtered_items()
        self.view.load_damage_item_combo(items)

    def refresh_reports(self):
        reports = self.get_all_reports()
        self.view.populate_damage_table(reports)