"""
Inventory Management System - Model (Database Version)
Handles all data operations using MySQL database
"""

from .database import DatabaseHandler


class InventoryItem:
    """Represents a single inventory item"""

    def __init__(self, item_id, name, category, quantity, min_stock, unit_price, supplier):
        self.id = item_id
        self.name = name
        self.category = category
        self.quantity = quantity
        self.min_stock = min_stock
        self.unit_price = unit_price
        self.supplier = supplier

    @property
    def total_value(self):
        return self.quantity * self.unit_price

    @property
    def is_low_stock(self):
        return self.quantity < self.min_stock

    @property
    def shortage(self):
        return max(0, self.min_stock - self.quantity)

    @classmethod
    def from_db_row(cls, row):
        return cls(
            item_id=row['id'],
            name=row['name'],
            category=row['category'],
            quantity=row['quantity'],
            min_stock=row['min_stock'],
            unit_price=float(row['unit_price']),
            supplier=row['supplier']
        )


class InventoryModel:
    """Main model class for inventory management with MySQL database"""

    CATEGORIES = ["Linens", "Toiletries", "Cleaning", "Kitchen",
                  "Furniture", "Electronics", "Other"]

    def __init__(self, db_config=None):
        self._observers = []

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
            raise Exception("Failed to connect to database")

        self.db.create_tables()  # Fixed: create tables if missing

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update()

    def add_item(self, name, category, quantity, min_stock, unit_price, supplier):
        item_id = self.db.add_item(name, category, quantity, min_stock, unit_price, supplier)
        if item_id:
            self.notify_observers()
            return True
        return False

    def update_item(self, item_id, name, category, quantity, min_stock, unit_price, supplier):
        success = self.db.update_item(item_id, name, category, quantity, min_stock, unit_price, supplier)
        if success:
            self.notify_observers()
        return success

    def delete_item(self, item_id):
        success = self.db.delete_item(item_id)
        if success:
            self.notify_observers()
        return success

    def find_item_by_name(self, name):
        item = self.db.get_filtered_items(name)
        if item:
            return item[0]['id']
        return -1

    def adjust_stock(self, item_id, adjustment):
        success = self.db.adjust_stock(item_id, adjustment)
        if success:
            self.notify_observers()
        return success

    def get_filtered_items(self, search_text="", category="All"):
        db_items = self.db.get_filtered_items(search_text, category)
        return [InventoryItem.from_db_row(row) for row in db_items]

    def get_low_stock_items(self):
        db_items = self.db.get_low_stock_items()
        return [InventoryItem.from_db_row(row) for row in db_items]

    def get_statistics(self):
        return self.db.get_statistics()

    # ------------------- Enhanced Methods -------------------
    def get_all_categories(self):
        """Get all unique categories from database"""
        return self.db.get_all_categories()

    def item_exists(self, name):
        """Check if item exists by name"""
        return self.db.item_exists(name)

    def get_item_by_name(self, name):
        """Get item by exact name"""
        item = self.db.get_item_by_name(name)
        if item:
            return InventoryItem.from_db_row(item)
        return None

    def bulk_add_items(self, items_list):
        """Add multiple items at once"""
        success = self.db.bulk_insert_items(items_list)
        if success:
            self.notify_observers()
        return success

    def load_sample_data(self):
        # Converted from USD to PHP (1 USD = 55 PHP approximately)
        sample_data = [
            ["Bed Sheets (Queen)", "Linens", 150, 100, 1375.00, "Linen Supply Co"],  # $25 → ₱1,375
            ["Towels (Bath)", "Linens", 300, 200, 687.50, "Linen Supply Co"],  # $12.50 → ₱687.50
            ["Shampoo Bottles", "Toiletries", 80, 150, 206.25, "Hospitality Goods Inc"],  # $3.75 → ₱206.25
            ["Soap Bars", "Toiletries", 500, 300, 68.75, "Hospitality Goods Inc"],  # $1.25 → ₱68.75
            ["Toilet Paper Rolls", "Toiletries", 1000, 800, 41.25, "Paper Products LLC"],  # $0.75 → ₱41.25
            ["Cleaning Spray", "Cleaning", 45, 50, 467.50, "CleanPro Supplies"],  # $8.50 → ₱467.50
            ["Vacuum Bags", "Cleaning", 30, 40, 825.00, "CleanPro Supplies"],  # $15.00 → ₱825.00
            ["Coffee Pods", "Kitchen", 200, 150, 27.50, "Hotel Food Service"],  # $0.50 → ₱27.50
            ["Dinner Plates", "Kitchen", 250, 200, 440.00, "Restaurant Supply Co"],  # $8.00 → ₱440.00
            ["TV Remote Batteries", "Electronics", 100, 80, 137.50, "Electronics Depot"]  # $2.50 → ₱137.50
        ]

        stats = self.db.get_statistics()
        if stats['total_items'] == 0:
            print(" Loading sample data...")
            for data in sample_data:
                self.add_item(*data)
            print(" Sample data loaded successfully!")
        else:
            print(f"ℹ Database already contains {stats['total_items']} items")

    def close(self):
        if self.db:
            self.db.disconnect()