"""
Inventory Management System - Report Generator
Generates PDF reports for inventory data
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QMessageBox, QDateEdit, QCheckBox)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime, date
import mysql.connector
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
import os


class ReportGenerator:
    """Handles generation of various inventory reports"""

    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        # Set fixed reports directory
        self.reports_dir = "/Users/jbasquiat/Downloads/reports"

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                port=self.db_config.get('port', 3308)
            )
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def generate_inventory_report(self, report_type="full", category="All", include_low_stock=False,
                                 start_date=None, end_date=None):
        """Generate inventory report as PDF with optional date filtering"""
        if not self.connect():
            return False, "Failed to connect to database"

        try:
            # Build SQL query based on parameters
            where_parts = []
            params = []

            # 1. Handle category filter
            if category != "All":
                where_parts.append("category = %s")
                params.append(category)

            # 2. Handle low stock filter
            if report_type == "low_stock":
                where_parts.append("quantity < min_stock")
            elif include_low_stock and report_type == "full":
                where_parts.append("quantity < min_stock")

            # 3. Handle date filter (if specified)
            date_filter_text = ""
            if start_date and end_date:
                # Note: This filters based on when items were added/modified
                # You may need to add a created_at or updated_at column to items table
                # For now, we'll just note the date range in the report
                date_filter_text = f" (Date Range: {start_date} to {end_date})"

            # Build the final query
            query = "SELECT * FROM items"
            if where_parts:
                query += " WHERE " + " AND ".join(where_parts)

            print(f"DEBUG: Executing query: {query} with params: {params}")
            self.cursor.execute(query, tuple(params))
            items = self.cursor.fetchall()

            print(f"DEBUG: Found {len(items)} items")
            for item in items:
                print(f"  - {item['name']} ({item['category']}): {item['quantity']}/{item['min_stock']}")

            # If no items found with current filters, provide helpful message
            if len(items) == 0:
                if report_type == "low_stock" or include_low_stock:
                    # Check if the category exists at all
                    category_check = "SELECT COUNT(*) as count FROM items"
                    category_params = []
                    if category != "All":
                        category_check += " WHERE category = %s"
                        category_params.append(category)

                    self.cursor.execute(category_check, tuple(category_params))
                    category_result = self.cursor.fetchone()

                    if category_result['count'] == 0 and category != "All":
                        self.disconnect()
                        return False, f"No items found in category '{category}'"
                    else:
                        self.disconnect()
                        return False, f"No low stock items found. Try unchecking 'Include Low Stock Highlight'."
                else:
                    self.disconnect()
                    return False, "No items found matching the criteria."

            # Get statistics for the filtered items
            stats_query = "SELECT COUNT(*) as total_items, SUM(quantity) as total_quantity, SUM(quantity * unit_price) as total_value FROM items"
            if where_parts:
                stats_query += " WHERE " + " AND ".join(where_parts)

            self.cursor.execute(stats_query, tuple(params))
            stats = self.cursor.fetchone()

            # Count low stock items in the filtered results
            low_stock_count = sum(1 for item in items if item['quantity'] < item['min_stock'])
            stats['low_stock_count'] = low_stock_count

            # Create PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_report_{timestamp}.pdf"

            # Ensure reports directory exists at fixed location
            if not os.path.exists(self.reports_dir):
                os.makedirs(self.reports_dir)

            filepath = os.path.join(self.reports_dir, filename)

            # Use landscape orientation for better table fit
            doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=10,
                alignment=1,
                textColor=colors.black
            )

            header_style = ParagraphStyle(
                'Header',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#333333')
            )

            # Title
            elements.append(Paragraph("INVENTORY MANAGEMENT SYSTEM REPORT", title_style))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", header_style))
            elements.append(Spacer(1, 15))

            # Report Type Info
            type_info = f"<b>Report Type:</b> {report_type.upper()}"
            if report_type == "full" and category != "All":
                type_info += f" | <b>Category:</b> {category}"
            if include_low_stock and report_type == "full":
                type_info += " | <b>Low Stock Only:</b> Yes"
            if date_filter_text:
                type_info += f" | {date_filter_text}"

            elements.append(Paragraph(type_info, styles['Normal']))
            elements.append(Spacer(1, 10))

            # Statistics - USING "PHP" INSTEAD OF SYMBOL
            stats_text = f"""
            <b>Statistics:</b><br/>
            • Total Items: {stats['total_items'] or 0}<br/>
            • Total Quantity: {stats['total_quantity'] or 0}<br/>
            • Total Value: PHP {stats['total_value'] or 0:,.2f}<br/>
            • Low Stock Items: {stats['low_stock_count'] or 0}<br/>
            """
            elements.append(Paragraph(stats_text, styles['Normal']))
            elements.append(Spacer(1, 15))

            # Items Table - with optimized column widths
            table_data = [['ID', 'Item Name', 'Category', 'Qty', 'Min', 'Price', 'Value', 'Supplier', 'Status']]

            for item in items:
                total_value = item['quantity'] * float(item['unit_price'])
                status = "LOW" if item['quantity'] < item['min_stock'] else "OK"

                row = [
                    str(item['id']),
                    item['name'][:25] + "..." if len(item['name']) > 25 else item['name'],
                    item['category'][:12] if len(item['category']) > 12 else item['category'],
                    str(item['quantity']),
                    str(item['min_stock']),
                    f"PHP {float(item['unit_price']):.2f}",  # CHANGED TO "PHP"
                    f"PHP {total_value:.2f}",  # CHANGED TO "PHP"
                    (item['supplier'] or "")[:18] + "..." if len(item['supplier'] or "") > 18 else (item['supplier'] or ""),
                    status
                ]
                table_data.append(row)

            # Calculate column widths for landscape A4
            col_widths = [
                1.2*cm,   # ID
                6.0*cm,   # Item Name
                2.8*cm,   # Category
                1.5*cm,   # Quantity
                1.5*cm,   # Min Stock
                2.2*cm,   # Unit Price
                2.5*cm,   # Total Value
                5.0*cm,   # Supplier
                1.5*cm,   # Status
            ]

            # Create table
            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # GREY/BLACK COLOR PALETTE
            header_bg = colors.HexColor('#2C3E50')      # Dark grey-blue
            header_text = colors.white
            row_bg_even = colors.HexColor('#F8F9FA')    # Very light grey
            row_bg_odd = colors.white
            grid_color = colors.HexColor('#BDC3C7')     # Medium grey
            low_stock_bg = colors.HexColor('#FFEAA7')   # Light yellow for low stock
            low_stock_text = colors.HexColor('#D35400') # Dark orange text

            # Style the table with grey/black theme
            table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), header_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 6),

                # Data rows - alternating colors
                ('BACKGROUND', (0, 1), (-1, -1), row_bg_even),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_bg_even, row_bg_odd]),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),

                # Alignment
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # ID left-aligned
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),      # Name left-aligned
                ('ALIGN', (7, 1), (7, -1), 'LEFT'),      # Supplier left-aligned
                ('ALIGN', (5, 1), (6, -1), 'RIGHT'),     # Prices right-aligned

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            # Highlight low stock rows
            for i, item in enumerate(items, start=1):
                if item['quantity'] < item['min_stock']:
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), low_stock_bg),
                        ('TEXTCOLOR', (0, i), (-1, i), low_stock_text),
                        ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
                    ]))

            elements.append(table)

            # Add footer with item count
            footer_text = f"Total items: {len(items)} | Generated by Inventoria System"
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(footer_text, header_style))

            # Build PDF
            doc.build(elements)

            self.disconnect()
            return True, filepath

        except Exception as e:
            if self.conn:
                self.disconnect()
            return False, f"Error generating report: {str(e)}"

    def generate_category_summary(self):
        """Generate category summary report"""
        if not self.connect():
            return False, "Failed to connect to database"

        try:
            self.cursor.execute("""
                SELECT 
                    category,
                    COUNT(*) as item_count,
                    SUM(quantity) as total_quantity,
                    SUM(quantity * unit_price) as total_value,
                    COUNT(CASE WHEN quantity < min_stock THEN 1 END) as low_stock_count
                FROM items
                GROUP BY category
                ORDER BY category
            """)
            categories = self.cursor.fetchall()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"category_summary_{timestamp}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            # Use portrait for simpler table
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []

            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CategoryTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                alignment=1,
                textColor=colors.black
            )

            elements.append(Paragraph("CATEGORY SUMMARY REPORT", title_style))
            elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))

            if categories:
                table_data = [['Category', 'Items', 'Total Qty', 'Total Value', 'Low Stock']]

                for cat in categories:
                    row = [
                        cat['category'],
                        str(cat['item_count']),
                        str(cat['total_quantity']),
                        f"PHP {cat['total_value'] or 0:,.2f}",  # CHANGED TO "PHP"
                        str(cat['low_stock_count'])
                    ]
                    table_data.append(row)

                # GREY/BLACK COLOR PALETTE
                header_bg = colors.HexColor('#2C3E50')
                header_text = colors.white
                row_bg_even = colors.HexColor('#F8F9FA')
                row_bg_odd = colors.white
                grid_color = colors.HexColor('#BDC3C7')

                # Optimized column widths for portrait
                col_widths = [4.5*cm, 2.5*cm, 3.0*cm, 4.0*cm, 2.5*cm]

                table = Table(table_data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    # Header
                    ('BACKGROUND', (0, 0), (-1, 0), header_bg),
                    ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),

                    # Data rows
                    ('BACKGROUND', (0, 1), (-1, -1), row_bg_even),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_bg_even, row_bg_odd]),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),

                    # Alignment
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Category left-aligned
                    ('ALIGN', (3, 1), (3, -1), 'RIGHT'),     # Value right-aligned

                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(table)
            else:
                elements.append(Paragraph("No categories found.", styles['Normal']))

            # Add summary
            total_items = sum(cat['item_count'] for cat in categories)
            total_value = sum(cat['total_value'] or 0 for cat in categories)
            total_low_stock = sum(cat['low_stock_count'] for cat in categories)

            elements.append(Spacer(1, 20))
            summary_text = f"""
            <b>Summary:</b><br/>
            • Total Categories: {len(categories)}<br/>
            • Total Items: {total_items}<br/>
            • Total Value: PHP {total_value:,.2f}<br/>  # CHANGED TO "PHP"
            • Total Low Stock Items: {total_low_stock}<br/>
            """
            elements.append(Paragraph(summary_text, styles['Normal']))

            doc.build(elements)
            self.disconnect()
            return True, filepath

        except Exception as e:
            if self.conn:
                self.disconnect()
            return False, f"Error generating category report: {str(e)}"


class ReportDialog(QDialog):
    """Dialog for generating reports"""

    def __init__(self, parent=None, db_config=None):
        super().__init__(parent)
        self.db_config = db_config or {
            'host': 'localhost',
            'database': 'inventoria_db',
            'user': 'root',
            'password': ''
        }

        self.setWindowTitle("Generate Report")
        self.setFixedSize(450, 450)  # Increased height for date filters
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("📊 Generate Inventory Report")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # Report directory info
        reports_dir = "/Users/jbasquiat/Downloads/reports"
        dir_label = QLabel(f"Reports will be saved to:\n{reports_dir}")
        dir_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px; background-color: #f0f0f0; border-radius: 5px;")
        dir_label.setWordWrap(True)
        layout.addWidget(dir_label)

        # Report Type
        layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["Full Inventory", "Category Summary", "Low Stock Only"])
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        layout.addWidget(self.report_type_combo)

        # Category (if applicable)
        layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Linens", "Toiletries", "Cleaning",
                                     "Kitchen", "Furniture", "Electronics", "Other"])
        layout.addWidget(self.category_combo)

        # Date Range Filter (NEW)
        layout.addWidget(QLabel("📅 Date Range (Optional):"))

        # Enable date filter checkbox
        self.enable_date_filter = QCheckBox("Enable Date Filter")
        self.enable_date_filter.setChecked(False)
        self.enable_date_filter.stateChanged.connect(self.toggle_date_filter)
        layout.addWidget(self.enable_date_filter)

        # Date range container
        date_layout = QHBoxLayout()

        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))  # Default: 1 month ago
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setEnabled(False)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())  # Default: today
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setEnabled(False)
        date_layout.addWidget(self.end_date)

        layout.addLayout(date_layout)

        # Low Stock option
        self.include_low_stock_check = QCheckBox("✓ Include Low Stock Highlight")
        self.include_low_stock_check.setChecked(False)
        layout.addWidget(self.include_low_stock_check)

        # Buttons
        button_layout = QHBoxLayout()

        generate_btn = QPushButton("📄 Generate PDF Report")
        generate_btn.clicked.connect(self.generate_report)
        button_layout.addWidget(generate_btn)

        # Open Reports Folder button
        open_folder_btn = QPushButton("📂 Open Reports Folder")
        open_folder_btn.clicked.connect(self.open_reports_folder)
        button_layout.addWidget(open_folder_btn)

        layout.addLayout(button_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

    def toggle_date_filter(self, state):
        """Enable/disable date picker based on checkbox"""
        enabled = (state == 2)  # Qt.Checked = 2
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def on_report_type_changed(self, text):
        """Handle report type change"""
        if text == "Low Stock Only":
            self.include_low_stock_check.setEnabled(False)
            self.include_low_stock_check.setText("✓ Low Stock Only (already filtered)")
            self.include_low_stock_check.setChecked(True)
            self.category_combo.setEnabled(False)
        elif text == "Category Summary":
            self.include_low_stock_check.setEnabled(False)
            self.include_low_stock_check.setText("N/A for Category Summary")
            self.include_low_stock_check.setChecked(False)
            self.category_combo.setEnabled(False)
        else:  # Full Inventory
            self.include_low_stock_check.setEnabled(True)
            self.include_low_stock_check.setText("✓ Include Low Stock Highlight")
            self.include_low_stock_check.setChecked(False)
            self.category_combo.setEnabled(True)

    def generate_report(self):
        report_type_text = self.report_type_combo.currentText()
        category = self.category_combo.currentText()
        include_low_stock = self.include_low_stock_check.isChecked()

        # Get date range if enabled
        start_date = None
        end_date = None
        if self.enable_date_filter.isChecked():
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")

        generator = ReportGenerator(self.db_config)

        if report_type_text == "Category Summary":
            success, result = generator.generate_category_summary()
        elif report_type_text == "Low Stock Only":
            success, result = generator.generate_inventory_report(
                report_type="low_stock",
                category="All",
                include_low_stock=False,
                start_date=start_date,
                end_date=end_date
            )
        else:  # Full Inventory
            success, result = generator.generate_inventory_report(
                report_type="full",
                category=category,
                include_low_stock=include_low_stock,
                start_date=start_date,
                end_date=end_date
            )

        if success:
            self.status_label.setText(f"✅ Report generated: {os.path.basename(result)}")

            filter_info = f"• Report Type: {report_type_text}\n• Category: {category}\n• Low Stock Only: {'Yes' if report_type_text == 'Low Stock Only' else ('Yes' if include_low_stock else 'No')}"
            if start_date and end_date:
                filter_info += f"\n• Date Range: {start_date} to {end_date}"

            QMessageBox.information(
                self,
                "Success",
                f"Report generated successfully!\n\nSaved to:\n{result}\n\nFilter applied:\n{filter_info}"
            )
        else:
            self.status_label.setText("❌ Failed to generate report")
            QMessageBox.critical(self, "Error", result)

    def open_reports_folder(self):
        """Open the reports folder in Finder (Mac)"""
        import subprocess
        import os

        reports_dir = "/Users/jbasquiat/Downloads/reports"

        # Create directory if it doesn't exist
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            self.status_label.setText("📁 Created reports directory")

        # Open folder in Finder (Mac)
        try:
            subprocess.run(["open", reports_dir])
            self.status_label.setText("📂 Opening reports folder...")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder:\n{str(e)}")