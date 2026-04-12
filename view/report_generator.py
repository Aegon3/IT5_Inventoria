"""
Inventoria - Report Dialog (View only)
Place in: view/report_generator.py
ReportGenerator logic has been moved to model/report_model.py
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QMessageBox, QDateEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDate
import os



class ReportDialog(QDialog):
    """View-only dialog for report generation. Collects inputs and emits signals."""

    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.db_config = db_config
        self.setWindowTitle("Generate Report")
        self.setFixedSize(450, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title_label = QLabel("Generate Inventory Report")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)

        reports_dir = "/Users/jbasquiat/Downloads/reports"
        dir_label = QLabel(f"Reports will be saved to:\n{reports_dir}")
        dir_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px; background-color: #f0f0f0; border-radius: 5px;")
        dir_label.setWordWrap(True)
        layout.addWidget(dir_label)

        layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Full Inventory",
            "Category Summary",
            "Low Stock Only",
            "Damage Report",
            "Stock Issuance Report"
        ])
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        layout.addWidget(self.report_type_combo)

        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Linens", "Toiletries", "Cleaning",
                                      "Kitchen", "Furniture", "Electronics", "Other"])
        layout.addWidget(self.category_combo)

        layout.addWidget(QLabel("Date Range (Optional):"))

        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(False)
        self.enable_date_filter.stateChanged.connect(self.toggle_date_filter)
        layout.addWidget(self.enable_date_filter)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setEnabled(False)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setEnabled(False)
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)

        self.include_low_stock_check = QCheckBox("Highlight Low Stock Items")
        self.include_low_stock_check.setChecked(True)
        layout.addWidget(self.include_low_stock_check)

        button_layout = QHBoxLayout()
        generate_btn = QPushButton("Generate PDF Report")
        generate_btn.clicked.connect(self._on_generate_clicked)
        button_layout.addWidget(generate_btn)

        open_folder_btn = QPushButton("Open Reports Folder")
        open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        button_layout.addWidget(open_folder_btn)
        layout.addLayout(button_layout)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

    def toggle_date_filter(self, state):
        """Enable/disable date pickers — pure UI toggle."""
        enabled = (state == 2)
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def on_report_type_changed(self, text):
        """Update UI state based on report type — pure display logic."""
        if text == "Low Stock Only":
            self.include_low_stock_check.setEnabled(False)
            self.include_low_stock_check.setText("Low Stock Only (already filtered)")
            self.include_low_stock_check.setChecked(True)
            self.category_combo.setEnabled(False)
        elif text in ("Category Summary", "Damage Report", "Stock Issuance Report"):
            self.include_low_stock_check.setEnabled(False)
            self.include_low_stock_check.setText(f"N/A for {text}")
            self.include_low_stock_check.setChecked(False)
            self.category_combo.setEnabled(False)
        else:
            self.include_low_stock_check.setEnabled(True)
            self.include_low_stock_check.setText("Highlight Low Stock Items")
            self.include_low_stock_check.setChecked(True)
            self.category_combo.setEnabled(True)
            self.category_combo.setCurrentIndex(0)

    def _on_generate_clicked(self):
        """Gather inputs and pass to controller via callback — no generation logic here."""
        params = {
            'report_type': self.report_type_combo.currentText(),
            'category': self.category_combo.currentText(),
            'include_low_stock': self.include_low_stock_check.isChecked(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd") if self.enable_date_filter.isChecked() else None,
            'end_date': self.end_date.date().toString("yyyy-MM-dd") if self.enable_date_filter.isChecked() else None,
        }
        if self._generate_callback:
            self._generate_callback(params)

    def _on_open_folder_clicked(self):
        """Tell controller to open the reports folder."""
        if self._open_folder_callback:
            self._open_folder_callback()

    def set_callbacks(self, generate_callback, open_folder_callback):
        """Controller injects its handler functions."""
        self._generate_callback = generate_callback
        self._open_folder_callback = open_folder_callback

    def show_result(self, success, message):
        """Controller calls this to update the status label after generation."""
        if success:
            self.status_label.setText(f"Report generated: {message}")
            QMessageBox.information(self, "Success", f"Report generated successfully!\n\nSaved to:\n{message}")
        else:
            self.status_label.setText("Failed to generate report")
            QMessageBox.critical(self, "Error", message)

    def show_folder_status(self, message):
        """Controller calls this to update folder open status."""
        self.status_label.setText(message)