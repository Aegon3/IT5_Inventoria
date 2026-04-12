"""
Damage Report - Model
Pure data container - NO database operations, NO if statements, NO logic.
"""


class DamageReport:
    def __init__(self, report_id, reported_date, item_id, item_name, quantity, reason, reported_by):
        self.id = report_id
        self.reported_date = reported_date
        self.item_id = item_id
        self.item_name = item_name
        self.quantity = quantity
        self.reason = reason
        self.reported_by = reported_by

    @classmethod
    def from_dict(cls, data):
        return cls(
            report_id=data.get('id'),
            reported_date=data.get('reported_date', ''),
            item_id=data.get('item_id'),
            item_name=data.get('item_name', ''),
            quantity=data.get('quantity'),
            reason=data.get('reason', ''),
            reported_by=data.get('reported_by', '')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'reported_date': self.reported_date,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'reason': self.reason,
            'reported_by': self.reported_by
        }


class DamageReportModel:
    pass