"""
Inventory Management System - Model
Pure data containers and observer pattern - NO database operations.
NO if statements, NO try/catch, NO db operations.
"""


class InventoryItem:
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
        return self.min_stock - self.quantity

    @classmethod
    def from_dict(cls, row):
        return cls(
            item_id=row.get('id'),
            name=row.get('name', ''),
            category=row.get('category', ''),
            quantity=row.get('quantity', 0),
            min_stock=row.get('min_stock', 0),
            unit_price=float(row.get('unit_price', 0)),
            supplier=row.get('supplier', '')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'quantity': self.quantity,
            'min_stock': self.min_stock,
            'unit_price': self.unit_price,
            'supplier': self.supplier
        }


class InventoryModel:
    CATEGORIES = ["Linens", "Toiletries", "Cleaning", "Kitchen", "Furniture", "Electronics", "Other"]

    def __init__(self):
        self._observers = []

    def add_observer(self, observer):
        self._observers.append(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update()