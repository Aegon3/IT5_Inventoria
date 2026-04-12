"""
Inventoria - Report Builder
Handles ONLY PDF construction from raw data dicts.
No DB, no UI, no PyQt6.
Place in: model/report_builder.py
"""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import os


REPORTS_DIR = "/Users/jbasquiat/Downloads/reports"

HEADER_BG   = colors.HexColor('#2C3E50')
ROW_EVEN    = colors.HexColor('#F8F9FA')
ROW_ODD     = colors.white
GRID        = colors.HexColor('#BDC3C7')
LOW_STOCK_BG  = colors.HexColor('#FFEAA7')
LOW_STOCK_TXT = colors.HexColor('#D35400')


def _ensure_dir():
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)


def _base_styles():
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        'Title', parent=styles['Heading1'],
        fontSize=16, spaceAfter=10, alignment=1, textColor=colors.black
    )
    header = ParagraphStyle(
        'Header', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#333333')
    )
    return styles, title, header


def _base_table_style():
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_EVEN, ROW_ODD]),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])


def build_inventory_pdf(items, report_type, category, include_low_stock,
                        start_date, end_date):
    """Build inventory PDF from raw item rows. Returns filepath."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"inventory_report_{timestamp}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
    styles, title_style, header_style = _base_styles()
    elements = []

    elements.append(Paragraph("INVENTORY MANAGEMENT SYSTEM REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", header_style))
    elements.append(Spacer(1, 15))

    type_info = f"<b>Report Type:</b> {report_type.upper()}"
    if report_type == "full" and category != "All":
        type_info += f" | <b>Category:</b> {category}"
    if include_low_stock and report_type == "full":
        type_info += " | <b>Low Stock Only:</b> Yes"
    if start_date and end_date:
        type_info += f" | Date Range: {start_date} to {end_date}"
    elements.append(Paragraph(type_info, styles['Normal']))
    elements.append(Spacer(1, 10))

    total_qty   = sum(i['quantity'] for i in items)
    total_val   = sum(i['quantity'] * float(i['unit_price']) for i in items)
    low_count   = sum(1 for i in items if i['quantity'] < i['min_stock'])
    elements.append(Paragraph(
        f"<b>Statistics:</b><br/>"
        f"Total Items: {len(items)}<br/>"
        f"Total Quantity: {total_qty}<br/>"
        f"Total Value: PHP {total_val:,.2f}<br/>"
        f"Low Stock Items: {low_count}<br/>",
        styles['Normal']
    ))
    elements.append(Spacer(1, 15))

    table_data = [['ID', 'Item Name', 'Category', 'Qty', 'Min', 'Price', 'Value', 'Supplier', 'Status']]
    for item in items:
        item_total = item['quantity'] * float(item['unit_price'])
        status = "LOW" if item['quantity'] < item['min_stock'] else "OK"
        table_data.append([
            str(item['id']),
            item['name'][:25] + "..." if len(item['name']) > 25 else item['name'],
            item['category'][:12],
            str(item['quantity']),
            str(item['min_stock']),
            f"PHP {float(item['unit_price']):.2f}",
            f"PHP {item_total:.2f}",
            (item['supplier'] or "")[:18] + "..." if len(item['supplier'] or "") > 18 else (item['supplier'] or ""),
            status
        ])

    col_widths = [1.2*cm, 6.0*cm, 2.8*cm, 1.5*cm, 1.5*cm, 2.2*cm, 2.5*cm, 5.0*cm, 1.5*cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    table.setStyle(_base_table_style())
    table.setStyle(TableStyle([('ALIGN', (0, 1), (0, -1), 'LEFT'), ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                                ('ALIGN', (7, 1), (7, -1), 'LEFT'), ('ALIGN', (5, 1), (6, -1), 'RIGHT')]))
    for i, item in enumerate(items, start=1):
        if item['quantity'] < item['min_stock']:
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), LOW_STOCK_BG),
                ('TEXTCOLOR', (0, i), (-1, i), LOW_STOCK_TXT),
                ('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold'),
            ]))

    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Total items: {len(items)} | Generated by Inventoria System", header_style))
    doc.build(elements)
    return filepath


def build_category_pdf(rows):
    """Build category summary PDF from raw category rows. Returns filepath."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"category_summary_{timestamp}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles, title_style, _ = _base_styles()
    elements = []

    elements.append(Paragraph("CATEGORY SUMMARY REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    if rows:
        table_data = [['Category', 'Items', 'Total Qty', 'Total Value', 'Low Stock']]
        for r in rows:
            table_data.append([
                r['category'], str(r['item_count']), str(r['total_quantity']),
                f"PHP {r['total_value'] or 0:,.2f}", str(r['low_stock_count'])
            ])
        col_widths = [4.5*cm, 2.5*cm, 3.0*cm, 4.0*cm, 2.5*cm]
        table = Table(table_data, colWidths=col_widths)
        style = _base_table_style()
        style.add('ALIGN', (0, 1), (0, -1), 'LEFT')
        style.add('ALIGN', (3, 1), (3, -1), 'RIGHT')
        style.add('FONTSIZE', (0, 0), (-1, 0), 11)
        style.add('BOTTOMPADDING', (0, 0), (-1, 0), 10)
        style.add('TOPPADDING', (0, 0), (-1, 0), 8)
        style.add('FONTSIZE', (0, 1), (-1, -1), 10)
        table.setStyle(style)
        elements.append(table)
    else:
        elements.append(Paragraph("No categories found.", styles['Normal']))

    total_items     = sum(r['item_count'] for r in rows)
    total_value     = sum(r['total_value'] or 0 for r in rows)
    total_low_stock = sum(r['low_stock_count'] for r in rows)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        f"<b>Summary:</b><br/>"
        f"Total Categories: {len(rows)}<br/>"
        f"Total Items: {total_items}<br/>"
        f"Total Value: PHP {total_value:,.2f}<br/>"
        f"Total Low Stock Items: {total_low_stock}<br/>",
        styles['Normal']
    ))
    doc.build(elements)
    return filepath



def build_damage_report_pdf(rows, start_date=None, end_date=None):
    """Build damage report PDF from raw damage report rows. Returns filepath."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"damage_report_{timestamp}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
    styles, title_style, header_style = _base_styles()
    elements = []

    elements.append(Paragraph("DAMAGE REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", header_style))
    if start_date and end_date:
        elements.append(Paragraph(f"Date Range: {start_date} to {end_date}", header_style))
    elements.append(Spacer(1, 15))

    total_qty = sum(r['quantity'] for r in rows)
    elements.append(Paragraph(
        f"<b>Summary:</b><br/>"
        f"Total Damage Reports: {len(rows)}<br/>"
        f"Total Quantity Damaged/Lost: {total_qty}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 15))

    table_data = [['Date Reported', 'Item Name', 'Quantity', 'Reason', 'Reported By']]
    for r in rows:
        reported_date = r['reported_date'].strftime('%Y-%m-%d %H:%M') if r['reported_date'] else 'N/A'
        table_data.append([
            reported_date,
            (r['item_name'] or '')[:30],
            str(r['quantity']),
            (r['reason'] or '')[:40],
            r['reported_by'] or '',
        ])

    col_widths = [3.5*cm, 6.0*cm, 2.0*cm, 10.0*cm, 3.5*cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    style = _base_table_style()
    style.add('FONTSIZE', (0, 0), (-1, 0), 9)
    style.add('BOTTOMPADDING', (0, 0), (-1, 0), 7)
    style.add('FONTSIZE', (0, 1), (-1, -1), 8)
    style.add('ALIGN', (1, 1), (1, -1), 'LEFT')
    style.add('ALIGN', (3, 1), (3, -1), 'LEFT')
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Generated by Inventoria System", header_style))
    doc.build(elements)
    return filepath


def build_stock_issuance_pdf(rows, start_date=None, end_date=None):
    """Build stock issuance PDF from raw issuance rows. Returns filepath."""
    _ensure_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"stock_issuance_report_{timestamp}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
    styles, title_style, header_style = _base_styles()
    elements = []

    elements.append(Paragraph("STOCK ISSUANCE REPORT", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", header_style))
    if start_date and end_date:
        elements.append(Paragraph(f"Date Range: {start_date} to {end_date}", header_style))
    elements.append(Spacer(1, 15))

    total_qty = sum(r['quantity'] for r in rows)
    total_val = sum(float(r['total_value'] or 0) for r in rows)
    elements.append(Paragraph(
        f"<b>Summary:</b><br/>"
        f"Total Issuances: {len(rows)}<br/>"
        f"Total Quantity Issued: {total_qty}<br/>"
        f"Total Value Issued: PHP {total_val:,.2f}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 15))

    table_data = [['Date', 'Item Name', 'Category', 'Qty', 'Unit Price', 'Total Value', 'Issued By', 'Notes']]
    for r in rows:
        issued_date = r['issued_date'].strftime('%Y-%m-%d %H:%M') if r['issued_date'] else 'N/A'
        table_data.append([
            issued_date, (r['item_name'] or '')[:25], (r['category'] or 'N/A'),
            str(r['quantity']),
            f"PHP {float(r['unit_price'] or 0):.2f}",
            f"PHP {float(r['total_value'] or 0):.2f}",
            r['issued_by'] or '', (r['notes'] or '')[:20],
        ])

    col_widths = [3.5*cm, 5.0*cm, 2.8*cm, 1.5*cm, 2.5*cm, 3.0*cm, 2.8*cm, 4.0*cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    style = _base_table_style()
    style.add('FONTSIZE', (0, 0), (-1, 0), 9)
    style.add('BOTTOMPADDING', (0, 0), (-1, 0), 7)
    style.add('FONTSIZE', (0, 1), (-1, -1), 8)
    style.add('ALIGN', (1, 1), (2, -1), 'LEFT')
    style.add('ALIGN', (7, 1), (7, -1), 'LEFT')
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Generated by Inventoria System", header_style))
    doc.build(elements)
    return filepath