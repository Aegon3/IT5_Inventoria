"""
Inventoria - KPI Controller
Handles all KPI / statistics logic, keeping it out of the view.
NO QMessageBox imports.
"""


class KPIController:

    def __init__(self, model, view, db_config: dict, db):
        self.model = model
        self.view = view
        self.db_config = db_config
        self.db = db

    def update(self):
        try:
            stats = self.get_statistics()
            self.view.display_statistics(stats)
        except Exception as e:
            print(f"KPIController.update error: {e}")

    def get_statistics(self):
        stats = {}
        self.db.cursor.execute("SELECT COUNT(*) as total_items FROM items")
        stats['total_items'] = self.db.cursor.fetchone()['total_items']

        self.db.cursor.execute("SELECT SUM(quantity*unit_price) as total_value FROM items")
        result = self.db.cursor.fetchone()['total_value']
        stats['total_value'] = float(result) if result else 0.0

        self.db.cursor.execute("SELECT COUNT(*) as low_stock_count FROM items WHERE quantity < min_stock")
        stats['low_stock_count'] = self.db.cursor.fetchone()['low_stock_count']

        self.db.cursor.execute("SELECT category, COUNT(*) as count FROM items GROUP BY category")
        categories = {row['category']: row['count'] for row in self.db.cursor.fetchall()}
        stats['categories'] = categories

        total_items = stats['total_items']
        if total_items > 0:
            stats['avg_item_value'] = stats['total_value'] / total_items
        else:
            stats['avg_item_value'] = 0.0

        return stats

    def get_category_breakdown(self):
        try:
            self.db.cursor.execute("""
                SELECT
                    category,
                    COUNT(*)                   AS count,
                    SUM(quantity * unit_price) AS total_value
                FROM items
                GROUP BY category
                ORDER BY total_value DESC
            """)
            rows = self.db.cursor.fetchall()
            total_value = sum(float(r['total_value'] or 0) for r in rows)
            result = []
            for r in rows:
                val = float(r['total_value'] or 0)
                pct = (val / total_value * 100) if total_value > 0 else 0
                result.append({
                    'category': r['category'],
                    'total_value': val,
                    'count': int(r['count'] or 0),
                    'pct': pct
                })
            return result
        except Exception as e:
            print(f"KPIController.get_category_breakdown error: {e}")
            return []