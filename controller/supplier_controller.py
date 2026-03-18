"""
Supplier Management System - Controller
Contains logic extracted from supplier_views.py (formerly supplier_dialogs.py).
Handles validation, HTML building, and status color mapping.
"""


class SupplierController:
    """
    Static utility controller for supplier-related view logic.
    Used by supplier_views.py dialogs to keep logic out of the view layer.
    """

    # -----------------------------------------------------------------------
    # STATUS COLOR MAPPING
    # -----------------------------------------------------------------------

    STATUS_COLORS = {
        'DRAFT':     '#95A5A6',
        'PENDING':   '#F39C12',
        'ORDERED':   '#3498DB',
        'DELIVERED': '#27AE60',
        'CANCELLED': '#E74C3C',
    }

    @staticmethod
    def get_status_color(status: str) -> str:
        """
        Return the hex color for a given order status.

        Args:
            status (str): Order status string (case-insensitive).

        Returns:
            str: Hex color code.
        """
        return SupplierController.STATUS_COLORS.get(status.upper(), '#95A5A6')

    # -----------------------------------------------------------------------
    # APPROVAL VALIDATION
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_approval(supplier_text: str):
        """
        Validate that a supplier has been selected in StockApprovalDialog.

        Args:
            supplier_text (str): The current text of the supplier combo box.

        Returns:
            tuple: (valid: bool, message: str)
        """
        if not supplier_text or supplier_text == "Select Supplier":
            return False, "Please select a supplier!"
        return True, ""

    # -----------------------------------------------------------------------
    # ORDER DETAILS HTML BUILDER
    # -----------------------------------------------------------------------

    @staticmethod
    def build_order_details_html(order: dict, items: list, supplier: dict) -> str:
        """
        Build the full HTML string for displaying order details in OrdersDialog.

        Args:
            order (dict):    Order record from the database.
            items (list):    List of order item records.
            supplier (dict): Supplier record, or None if not found.

        Returns:
            str: Complete HTML string ready to pass to QTextEdit.setHtml().
        """
        order_date     = order['order_date'].strftime('%Y-%m-%d') if order['order_date'] else 'N/A'
        expected_date  = order['expected_delivery'].strftime('%Y-%m-%d') if order['expected_delivery'] else 'N/A'
        supplier_name  = supplier['name'] if supplier else 'Unknown'
        supplier_contact = supplier['contact_person'] if supplier else 'N/A'
        supplier_phone = supplier['phone'] if supplier else 'N/A'
        supplier_email = supplier['email'] if supplier else 'N/A'

        html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; }}
            h3 {{ color: #2C3E50; margin-top: 0; }}
            h4 {{ color: #3498DB; margin-top: 15px; }}
            .section {{ margin-bottom: 15px; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #000; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #f2f2f2; padding: 8px; border: 1px solid #ddd; text-align: left; }}
            td {{ padding: 8px; border: 1px solid #ddd; }}
            .total-row {{ background-color: #e8f4fd; font-weight: bold; }}
            .status-ordered {{ color: #3498DB; }}
            .status-delivered {{ color: #27AE60; }}
            .status-cancelled {{ color: #E74C3C; }}
        </style>
        </head>
        <body>
        <div class="section">
            <h3>Order Details: {order['order_number']}</h3>
            <p><span class="label">Supplier:</span> <span class="value">{supplier_name}</span></p>
            <p><span class="label">Contact:</span> <span class="value">{supplier_contact}</span></p>
            <p><span class="label">Phone:</span> <span class="value">{supplier_phone}</span></p>
            <p><span class="label">Email:</span> <span class="value">{supplier_email}</span></p>
            <p><span class="label">Order Date:</span> <span class="value">{order_date}</span></p>
            <p><span class="label">Expected Delivery:</span> <span class="value">{expected_date}</span></p>
            <p><span class="label">Status:</span> <span class="value status-{order['status']}"><b>{order['status'].upper()}</b></span></p>
            <p><span class="label">Created By:</span> <span class="value">{order['created_by']}</span></p>
            <p><span class="label">Notes:</span> <span class="value">{order['notes'] or 'None'}</span></p>
        </div>
        <div class="section">
            <h4>Order Items ({len(items)} items):</h4>
        """

        if items:
            html += """
            <table>
                <tr>
                    <th>Item Name</th>
                    <th>Category</th>
                    <th>Current Stock</th>
                    <th>Order Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Price</th>
                </tr>
            """
            total_amount = 0
            for item in items:
                item_total = item['quantity'] * float(item['unit_price'])
                total_amount += item_total
                html += f"""
                <tr>
                    <td>{item.get('item_name', 'Unknown')}</td>
                    <td>{item.get('category', 'N/A')}</td>
                    <td style='text-align: center;'>{item.get('current_stock', 0)}</td>
                    <td style='text-align: center;'>{item['quantity']}</td>
                    <td style='text-align: right;'>&#8369;{float(item['unit_price']):.2f}</td>
                    <td style='text-align: right;'>&#8369;{item_total:.2f}</td>
                </tr>
                """
            html += f"""
                <tr class="total-row">
                    <td colspan="5" style="text-align: right;">Grand Total:</td>
                    <td style="text-align: right;">&#8369;{total_amount:.2f}</td>
                </tr>
            </table>
            """
        else:
            html += "<p>No items found in this order.</p>"

        if supplier and supplier.get('address'):
            html += f"""
            <div class="section">
                <h4>Supplier Address:</h4>
                <p>{supplier['address']}</p>
            </div>
            """

        html += "</body></html>"
        return html