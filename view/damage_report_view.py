"""
Damage Report - View
UI tab and helper methods for the Damage Report feature.
Place in: view/damage_report_view.py

HOW TO USE IN view.py:
    from view.damage_report_view import DamageReportView
    mixin = DamageReportView()

    Then in setup_ui() add the tab for staff:
        if self.user_role == "staff":
            self.tabs.addTab(mixin.create_damage_report_tab(self), "Damage Report")

    Add the signal to InventoryView:
        damage_report_signal = pyqtSignal(int, str, int, str)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


def create_damage_report_tab(view_instance):
    """
    Build and return the Damage Report tab widget.
    Call this from InventoryView.setup_ui() for staff only.

    Args:
        view_instance: the InventoryView instance (self)

    Returns:
        QWidget: the complete tab widget
    """
    tab = QWidget()
    layout = QVBoxLayout(tab)

    # ── Header ──────────────────────────────────────────────
    title = QLabel("Damage Report")
    title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
    title.setStyleSheet("padding: 10px; color: #E74C3C;")
    layout.addWidget(title)

    desc = QLabel("Report damaged, lost, or unusable stock items. Reports are logged to the admin Activity Log.")
    desc.setStyleSheet("color: #666; padding: 0 10px 10px 10px;")
    desc.setWordWrap(True)
    layout.addWidget(desc)

    # ── Form ────────────────────────────────────────────────
    form_widget = QWidget()
    form_widget.setStyleSheet("""
        QWidget {
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 10px;
        }
    """)
    form_layout = QVBoxLayout(form_widget)

    # Item selection
    item_row = QHBoxLayout()
    item_label = QLabel("Item:")
    item_label.setFixedWidth(110)
    view_instance.damage_item_combo = QComboBox()
    view_instance.damage_item_combo.addItem("Select Item", None)
    item_row.addWidget(item_label)
    item_row.addWidget(view_instance.damage_item_combo)
    form_layout.addLayout(item_row)

    # Quantity
    qty_row = QHBoxLayout()
    qty_label = QLabel("Quantity:")
    qty_label.setFixedWidth(110)
    view_instance.damage_qty_spin = QSpinBox()
    view_instance.damage_qty_spin.setRange(1, 10000)
    view_instance.damage_qty_spin.setValue(1)
    qty_row.addWidget(qty_label)
    qty_row.addWidget(view_instance.damage_qty_spin)
    qty_row.addStretch()
    form_layout.addLayout(qty_row)

    # Reason
    reason_row = QHBoxLayout()
    reason_label = QLabel("Reason:")
    reason_label.setFixedWidth(110)
    reason_label.setAlignment(Qt.AlignmentFlag.AlignTop)
    view_instance.damage_reason_input = QTextEdit()
    view_instance.damage_reason_input.setMaximumHeight(80)
    view_instance.damage_reason_input.setPlaceholderText(
        "Describe the damage or loss (e.g. torn, broken, expired, lost...)"
    )
    reason_row.addWidget(reason_label)
    reason_row.addWidget(view_instance.damage_reason_input)
    form_layout.addLayout(reason_row)

    layout.addWidget(form_widget)

    # ── Submit button ────────────────────────────────────────
    submit_btn = QPushButton("Submit Damage Report")
    submit_btn.setObjectName("request_btn")
    submit_btn.setFixedHeight(36)
    submit_btn.clicked.connect(lambda: _on_submit(view_instance))
    layout.addWidget(submit_btn)

    # ── Reports table ────────────────────────────────────────
    table_label = QLabel("Submitted Damage Reports")
    table_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
    table_label.setStyleSheet("padding: 10px 0 5px 0;")
    layout.addWidget(table_label)

    view_instance.damage_table = QTableWidget()
    view_instance.damage_table.setColumnCount(5)
    view_instance.damage_table.setHorizontalHeaderLabels([
        "Date", "Item", "Quantity", "Reason", "Reported By"
    ])
    view_instance.damage_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    view_instance.damage_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    view_instance.damage_table.setWordWrap(True)
    view_instance.damage_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    view_instance.damage_table.setAlternatingRowColors(True)
    view_instance.damage_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    layout.addWidget(view_instance.damage_table)

    return tab


def _on_submit(view_instance):
    """Handle submit button click — validates then emits signal"""
    item_id = view_instance.damage_item_combo.currentData()
    item_name = view_instance.damage_item_combo.currentText()
    quantity = view_instance.damage_qty_spin.value()
    reason = view_instance.damage_reason_input.toPlainText().strip()

    if not item_id:
        QMessageBox.warning(view_instance, "Warning", "Please select an item.")
        return
    if not reason:
        QMessageBox.warning(view_instance, "Warning", "Please enter a reason for the damage.")
        return

    # Strip stock info from display name
    if ' (Stock:' in item_name:
        item_name = item_name.split(' (Stock:')[0]

    view_instance.damage_report_signal.emit(item_id, item_name, quantity, reason)


def load_damage_item_combo(view_instance, items):
    """Populate item combo box with current inventory items"""
    if not hasattr(view_instance, 'damage_item_combo'):
        return
    view_instance.damage_item_combo.clear()
    view_instance.damage_item_combo.addItem("Select Item", None)
    for item in items:
        view_instance.damage_item_combo.addItem(
            f"{item.name} (Stock: {item.quantity})", item.id
        )


def populate_damage_table(view_instance, reports):
    """Populate damage reports table with data"""
    if not hasattr(view_instance, 'damage_table'):
        return
    view_instance.damage_table.setRowCount(0)
    if not reports:
        return
    for report in reports:
        row = view_instance.damage_table.rowCount()
        view_instance.damage_table.insertRow(row)

        view_instance.damage_table.setItem(row, 0, QTableWidgetItem(str(report.reported_date)))
        view_instance.damage_table.setItem(row, 1, QTableWidgetItem(report.item_name))
        view_instance.damage_table.setItem(row, 2, QTableWidgetItem(str(report.quantity)))

        reason = report.reason
        reason_item = QTableWidgetItem(reason)
        reason_item.setToolTip(reason)
        view_instance.damage_table.setItem(row, 3, reason_item)
        view_instance.damage_table.setItem(row, 4, QTableWidgetItem(report.reported_by))


def clear_damage_form(view_instance):
    """Reset the damage report form after submission"""
    if hasattr(view_instance, 'damage_item_combo'):
        view_instance.damage_item_combo.setCurrentIndex(0)
    if hasattr(view_instance, 'damage_qty_spin'):
        view_instance.damage_qty_spin.setValue(1)
    if hasattr(view_instance, 'damage_reason_input'):
        view_instance.damage_reason_input.clear()