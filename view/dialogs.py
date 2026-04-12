"""
Inventory Management System - Dialogs
"""

from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QSpinBox, QDoubleSpinBox, QPushButton,
                             QHBoxLayout, QLabel)


class InventoryDialog(QDialog):
    """Dialog for adding or editing inventory items"""

    def __init__(self, parent=None, item_data=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setWindowTitle("Add Item" if not item_data else "Edit Item")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Linens", "Toiletries", "Cleaning", "Kitchen",
                                      "Furniture", "Electronics", "Other"])
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 10000)
        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 10000)
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0, 100000)
        self.unit_price_spin.setPrefix("₱ ")
        self.unit_price_spin.setDecimals(2)

        # CHANGED: Supplier is now a combo box instead of line edit
        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("Select Supplier")  # Default option

        # Load existing suppliers from database
        self.load_suppliers()

        # FIXED: Handle both dict and list item_data formats
        if self.item_data:
            if isinstance(self.item_data, dict):
                # Handle dict format
                self.name_input.setText(self.item_data.get('name', ''))
                self.category_combo.setCurrentText(self.item_data.get('category', 'Linens'))
                price_str = str(self.item_data.get('unit_price', '0'))
                price_clean = price_str.replace('₱', '').replace('PHP', '').replace('$', '').strip()
                try:
                    price_value = float(price_clean)
                except ValueError:
                    import re
                    numbers = re.findall(r'\d+\.?\d*', price_clean)
                    price_value = float(numbers[0]) if numbers else 0.0
                self.unit_price_spin.setValue(price_value)

                qty_str = str(self.item_data.get('quantity', '0'))
                self.quantity_spin.setValue(int(qty_str) if qty_str.isdigit() else 0)
                min_str = str(self.item_data.get('min_stock', '0'))
                self.min_stock_spin.setValue(int(min_str) if min_str.isdigit() else 0)

                # Set supplier from dict
                supplier_text = self.item_data.get('supplier', '')
                index = self.supplier_combo.findText(supplier_text)
                if index >= 0:
                    self.supplier_combo.setCurrentIndex(index)
                else:
                    self.supplier_combo.setCurrentText(supplier_text)
            elif isinstance(self.item_data, list):
                # Handle old list format (backward compatibility)
                self.name_input.setText(self.item_data[0])
                self.category_combo.setCurrentText(self.item_data[1])
                self.quantity_spin.setValue(int(self.item_data[2]))
                self.min_stock_spin.setValue(int(self.item_data[3]))

                # Handle price - both string and number formats
                price_str = str(self.item_data[4])
                # Remove currency symbols and text, keep only numbers
                price_clean = price_str.replace('₱', '').replace('PHP', '').replace('$', '').strip()
                try:
                    price_value = float(price_clean)
                except ValueError:
                    # If still can't convert, try to extract numbers
                    import re
                    numbers = re.findall(r'\d+\.?\d*', price_clean)
                    price_value = float(numbers[0]) if numbers else 0.0
                self.unit_price_spin.setValue(price_value)

                # Set supplier if it exists
                if len(self.item_data) > 6:
                    supplier_text = self.item_data[6]
                    # Try to find this supplier in the combo box
                    index = self.supplier_combo.findText(supplier_text)
                    if index >= 0:
                        self.supplier_combo.setCurrentIndex(index)
                    else:
                        self.supplier_combo.setCurrentText(supplier_text)

        layout.addRow("Item Name:", self.name_input)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Quantity:", self.quantity_spin)
        layout.addRow("Min Stock Level:", self.min_stock_spin)
        layout.addRow("Unit Price:", self.unit_price_spin)
        layout.addRow("Supplier:", self.supplier_combo)  # CHANGED: Now combo box

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)
        self.setLayout(layout)

    def load_suppliers(self):
        """Load suppliers via SupplierController — no DB access in the View."""
        try:
            from controller.supplier_controller import SupplierController
            suppliers = SupplierController.get_active_suppliers()
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier['name'], supplier['id'])
        except Exception as e:
            print(f" Error loading suppliers: {e}")
            fallback_suppliers = [
                "Linen Supply Co", "Hospitality Goods Inc", "CleanPro Supplies",
                "Paper Products LLC", "Hotel Food Service", "Restaurant Supply Co",
                "Electronics Depot", "Other"
            ]
            for supplier in fallback_suppliers:
                self.supplier_combo.addItem(supplier)

    def get_data(self):
        return {
            'name': self.name_input.text(),
            'category': self.category_combo.currentText(),
            'quantity': self.quantity_spin.value(),
            'min_stock': self.min_stock_spin.value(),
            'unit_price': self.unit_price_spin.value(),
            'supplier': self.supplier_combo.currentText()  # CHANGED: Now gets from combo
        }


class StockAdjustmentDialog(QDialog):
    """Dialog for adjusting stock quantities"""

    def __init__(self, parent=None, item_name="", current_qty=0):
        super().__init__(parent)
        self.item_name = item_name
        self.current_qty = current_qty
        self.setWindowTitle("Adjust Stock")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        item_label = QLabel(f"<b>Item:</b> {self.item_name}")
        item_label.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addRow(item_label)

        current_label = QLabel(f"<b>Current Stock:</b> {self.current_qty}")
        current_label.setStyleSheet("font-size: 13px; padding: 5px; color: #0066cc;")
        layout.addRow(current_label)

        self.adjustment_spin = QSpinBox()
        self.adjustment_spin.setRange(-self.current_qty, 10000)
        self.adjustment_spin.setValue(0)
        self.adjustment_spin.setStyleSheet("font-size: 14px; padding: 8px;")

        self.preview_label = QLabel(f"<b>New Quantity:</b> {self.current_qty}")
        self.preview_label.setStyleSheet("font-size: 13px; padding: 5px; color: #009900;")
        self.adjustment_spin.valueChanged.connect(self.update_preview)

        layout.addRow("Adjustment Amount:", self.adjustment_spin)
        layout.addRow(self.preview_label)

        help_label = QLabel(" Use positive numbers to add stock, negative to remove")
        help_label.setStyleSheet("font-size: 11px; color: #666666; padding: 5px;")
        layout.addRow(help_label)

        btn_layout = QHBoxLayout()
        apply_btn = QPushButton(" Apply")
        cancel_btn = QPushButton(" Cancel")
        apply_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(cancel_btn)

        layout.addRow(btn_layout)
        self.setLayout(layout)

    def update_preview(self, value):
        new_qty = max(0, self.current_qty + value)
        self.preview_label.setText(f"<b>New Quantity:</b> {new_qty}")

    def get_adjustment(self):
        return self.adjustment_spin.value()