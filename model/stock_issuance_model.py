"""
Stock Issuance - Model
Pure data container - NO database operations, NO if statements, NO logic.
"""


class StockIssuance:
    def __init__(self, issuance_id, issued_date, item_id, item_name, quantity, issued_by, notes):
        self.id = issuance_id
        self.issued_date = issued_date
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.issued_by = issued_by
        self.notes = notes

    @classmethod
    def from_dict(cls, data):
        return cls(
            issuance_id=data.get('id'),
            issued_date=data.get('issued_date', ''),
            item_id=data.get('item_id'),
            item_name=data.get('item_name', ''),
            quantity=data.get('quantity'),
            issued_by=data.get('issued_by', ''),
            notes=data.get('notes', '')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'issued_date': self.issued_date,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'issued_by': self.issued_by,
            'notes': self.notes
        }


class StockIssuanceModel:
    pass