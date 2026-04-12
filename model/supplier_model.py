"""
Supplier Management System - Model
Pure data containers - NO database operations, NO if statements.
"""


class Supplier:
    def __init__(self, supplier_id, name, contact_person, phone, email, address, status, notes, items_supplied_count, items_list):
        self.id = supplier_id
        self.name = name
        self.contact_person = contact_person
        self.phone = phone
        self.email = email
        self.address = address
        self.status = status
        self.notes = notes
        self.items_supplied_count = items_supplied_count
        self.items_list = items_list

    @classmethod
    def from_dict(cls, data):
        return cls(
            supplier_id=data.get('id'),
            name=data.get('name', ''),
            contact_person=data.get('contact_person', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            address=data.get('address', ''),
            status=data.get('status', 'active'),
            notes=data.get('notes', ''),
            items_supplied_count=data.get('items_supplied_count', 0),
            items_list=data.get('items_list', '')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'status': self.status,
            'notes': self.notes,
            'items_supplied_count': self.items_supplied_count,
            'items_list': self.items_list
        }


class StockRequest:
    def __init__(self, request_id, item_id, item_name, item_category, request_type,
                 requested_quantity, current_quantity, reason, requested_by,
                 request_date, approved_by, approval_date, status, notes):
        self.id = request_id
        self.item_id = item_id
        self.item_name = item_name
        self.item_category = item_category
        self.request_type = request_type
        self.requested_quantity = requested_quantity
        self.current_quantity = current_quantity
        self.reason = reason
        self.requested_by = requested_by
        self.request_date = request_date
        self.approved_by = approved_by
        self.approval_date = approval_date
        self.status = status
        self.notes = notes

    @classmethod
    def from_dict(cls, data):
        return cls(
            request_id=data.get('id'),
            item_id=data.get('item_id'),
            item_name=data.get('item_name', ''),
            item_category=data.get('item_category', ''),
            request_type=data.get('request_type', 'manual'),
            requested_quantity=data.get('requested_quantity', 0),
            current_quantity=data.get('current_quantity', 0),
            reason=data.get('reason', ''),
            requested_by=data.get('requested_by', ''),
            request_date=data.get('request_date', ''),
            approved_by=data.get('approved_by', ''),
            approval_date=data.get('approval_date', ''),
            status=data.get('status', 'pending'),
            notes=data.get('notes', '')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'item_category': self.item_category,
            'request_type': self.request_type,
            'requested_quantity': self.requested_quantity,
            'current_quantity': self.current_quantity,
            'reason': self.reason,
            'requested_by': self.requested_by,
            'request_date': self.request_date,
            'approved_by': self.approved_by,
            'approval_date': self.approval_date,
            'status': self.status,
            'notes': self.notes
        }


class SupplierModel:
    pass