"""
Inventoria - KPI Controller
Handles all KPI / statistics logic, keeping it out of the view.
Used by InventoryController to update the KPI dashboard.
"""

from model.database import DatabaseHandler


class KPIController:
    """
    Fetches KPI statistics from the database and pushes them to the
    KPI dashboard widget on the view.

    Usage in InventoryController:
        self.kpi_controller = KPIController(model, view, db_config)

    Call update() any time stats need refreshing (e.g. after add/edit/delete).
    """

    def __init__(self, model, view, db_config: dict):
        self.model = model
        self.view = view
        self.db_config = db_config

    def update(self):
        """Fetch latest stats and push to the view's KPI dashboard."""
        try:
            stats = self.model.get_statistics()
            self.view.display_statistics(stats)
        except Exception as e:
            print(f"KPIController.update error: {e}")

    def get_category_breakdown(self):
        """
        Query accurate per-category totals directly from DB.
        Returns list of {'category', 'total_value', 'count'} sorted by value desc.
        Used by ValueAnalyticsDialog.
        """
        try:
            db = DatabaseHandler(**self.db_config)
            if not db.connect():
                return []
            db.cursor.execute("""
                SELECT
                    category,
                    COUNT(*)                   AS count,
                    SUM(quantity * unit_price) AS total_value
                FROM items
                GROUP BY category
                ORDER BY total_value DESC
            """)
            rows = db.cursor.fetchall()
            db.disconnect()
            return [
                {
                    'category':    r['category'],
                    'total_value': float(r['total_value'] or 0),
                    'count':       int(r['count'] or 0),
                }
                for r in rows
            ]
        except Exception as e:
            print(f"KPIController.get_category_breakdown error: {e}")
            return []