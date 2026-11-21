from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


class FeeDocuments:

    # =========================================================
    # EXCEL REPORT
    # =========================================================

    @staticmethod
    def create_excel_report(rows, batch=None):

        workbook = Workbook()

        worksheet = workbook.active
        worksheet.title = "Fee Report"

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        worksheet.merge_cells(
            "A1:G1"
        )

        worksheet["A1"] = (
            "HostelNexus - Fee & Payment Report"
        )

        worksheet["A1"].font = Font(
            bold=True,
            size=16
        )

        worksheet["A1"].alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        worksheet.row_dimensions[1].height = 28

        # -----------------------------------------------------
        # REPORT INFORMATION
        # -----------------------------------------------------

        worksheet.merge_cells(
            "A2:G2"
        )

        if batch:

            report_name = (
                "Batch: " + str(batch)
            )

        else:

            report_name = "All Batches"

        worksheet["A2"] = (
            report_name
            + " | Generated: "
            + datetime.now().strftime(
                "%d-%m-%Y %I:%M %p"
            )
        )

        worksheet["A2"].alignment = Alignment(
            horizontal="center"
        )

        # -----------------------------------------------------
        # HEADERS
        # -----------------------------------------------------

        headers = [
            "USN / Student ID",
            "Student Name",
            "Batch",
            "Total Fee",
            "Paid Amount",
            "Pending Amount",
            "Status"
        ]

        header_row = 4

        for column, header in enumerate(
            headers,
            start=1
        ):

            cell = worksheet.cell(
                row=header_row,
                column=column
            )

            cell.value = header

            cell.font = Font(
                bold=True
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

        # -----------------------------------------------------
        # DATA
        # -----------------------------------------------------

        current_row = 5

        total_fee = 0
        total_paid = 0
        total_pending = 0

        for row in rows:

            total = float(
                row.get("total_fee", 0) or 0
            )

            paid = float(
                row.get("paid_amount", 0) or 0
            )

            pending = float(
                row.get("pending_amount", 0) or 0
            )

            total_fee += total
            total_paid += paid
            total_pending += pending

            if total > 0 and pending <= 0:

                status = "Paid"

            elif paid > 0:

                status = "Partially Paid"

            else:

                status = "Pending"

            values = [
                row.get("usn", ""),
                row.get("student_name", ""),
                row.get("batch", ""),
                total,
                paid,
                pending,
                status
            ]

            for column, value in enumerate(
                values,
                start=1
            ):

                cell = worksheet.cell(
                    row=current_row,
                    column=column
                )

                cell.value = value

                cell.alignment = Alignment(
                    vertical="center"
                )

            # Currency formatting

            worksheet.cell(
                current_row,
                4
            ).number_format = (
                '₹#,##0.00'
            )

            worksheet.cell(
                current_row,
                5
            ).number_format = (
                '₹#,##0.00'
            )

            worksheet.cell(
                current_row,
                6
            ).number_format = (
                '₹#,##0.00'
            )

            current_row += 1

        # -----------------------------------------------------
        # TOTAL ROW
        # -----------------------------------------------------

        total_row = current_row + 1

        worksheet.cell(
            total_row,
            1
        ).value = "TOTAL"

        worksheet.cell(
            total_row,
            1
        ).font = Font(
            bold=True
        )

        worksheet.cell(
            total_row,
            4
        ).value = total_fee

        worksheet.cell(
            total_row,
            5
        ).value = total_paid

        worksheet.cell(
            total_row,
            6
        ).value = total_pending

        for column in [4, 5, 6]:

            worksheet.cell(
                total_row,
                column
            ).font = Font(
                bold=True
            )

            worksheet.cell(
                total_row,
                column
            ).number_format = (
                '₹#,##0.00'
            )

        # -----------------------------------------------------
        # BORDERS
        # -----------------------------------------------------

        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        for row_cells in worksheet.iter_rows(
            min_row=header_row,
            max_row=total_row,
            min_col=1,
            max_col=7
        ):

            for cell in row_cells:

                cell.border = thin_border

        # -----------------------------------------------------
        # COLUMN WIDTHS
        # -----------------------------------------------------

        widths = {
            1: 20,
            2: 28,
            3: 15,
            4: 17,
            5: 17,
            6: 18,
            7: 20
        }

        for column, width in widths.items():

            worksheet.column_dimensions[
                get_column_letter(column)
            ].width = width

        # -----------------------------------------------------
        # FREEZE HEADER
        # -----------------------------------------------------

        worksheet.freeze_panes = "A5"

        # -----------------------------------------------------
        # SAVE TO MEMORY
        # -----------------------------------------------------

        output = BytesIO()

        workbook.save(output)

        output.seek(0)

        return output


    # =========================================================
    # PDF RECEIPT
    # =========================================================

    @staticmethod
    def create_receipt_pdf(payment):

        output = BytesIO()

        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReceiptTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=5
        )

        subtitle_style = ParagraphStyle(
            "ReceiptSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=15
        )

        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6
        )

        normal_style = ParagraphStyle(
            "NormalReceipt",
            parent=styles["Normal"],
            fontSize=9,
            leading=13
        )

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        elements = []

        elements.append(
            Paragraph(
                "HOSTELNEXUS",
                title_style
            )
        )

        elements.append(
            Paragraph(
                "BIET Engineering College - Hostel Management",
                subtitle_style
            )
        )

        elements.append(
            Paragraph(
                "PAYMENT RECEIPT",
                section_style
            )
        )

        # -----------------------------------------------------
        # RECEIPT INFORMATION
        # -----------------------------------------------------

        receipt_number = (
            payment.get(
                "receipt_number"
            )
            or "—"
        )

        payment_date = (
            payment.get(
                "payment_date"
            )
            or "—"
        )

        receipt_data = [

            [
                Paragraph(
                    "<b>Receipt Number</b>",
                    normal_style
                ),
                Paragraph(
                    str(receipt_number),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Payment Date</b>",
                    normal_style
                ),
                Paragraph(
                    str(payment_date),
                    normal_style
                )
            ]

        ]

        receipt_table = Table(
            receipt_data,
            colWidths=[
                55 * mm,
                115 * mm
            ]
        )

        receipt_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        elements.append(
            receipt_table
        )

        # -----------------------------------------------------
        # STUDENT INFORMATION
        # -----------------------------------------------------

        elements.append(
            Paragraph(
                "Student Information",
                section_style
            )
        )

        student_name = (
            str(
                payment.get(
                    "first_name"
                )
                or ""
            )
            + " "
            +
            str(
                payment.get(
                    "last_name"
                )
                or ""
            )
        ).strip()

        student_data = [

            [
                Paragraph(
                    "<b>Student Name</b>",
                    normal_style
                ),
                Paragraph(
                    student_name or "—",
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>USN / Student ID</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "usn"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Batch</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "batch"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Course</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "course"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Department</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "department"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ]

        ]

        student_table = Table(
            student_data,
            colWidths=[
                55 * mm,
                115 * mm
            ]
        )

        student_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        elements.append(
            student_table
        )

        # -----------------------------------------------------
        # PAYMENT INFORMATION
        # -----------------------------------------------------

        elements.append(
            Paragraph(
                "Payment Information",
                section_style
            )
        )

        amount = float(
            payment.get(
                "amount"
            )
            or 0
        )

        payment_data = [

            [
                Paragraph(
                    "<b>Payment Method</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "payment_method"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Transaction ID</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "transaction_id"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Academic Year</b>",
                    normal_style
                ),
                Paragraph(
                    str(
                        payment.get(
                            "academic_year"
                        )
                        or "—"
                    ),
                    normal_style
                )
            ],

            [
                Paragraph(
                    "<b>Amount Paid</b>",
                    normal_style
                ),
                Paragraph(
                    "<b>₹{:,.2f}</b>".format(
                        amount
                    ),
                    normal_style
                )
            ]

        ]

        payment_table = Table(
            payment_data,
            colWidths=[
                55 * mm,
                115 * mm
            ]
        )

        payment_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.lightgrey
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ])
        )

        elements.append(
            payment_table
        )

        # -----------------------------------------------------
        # REMARKS
        # -----------------------------------------------------

        remarks = (
            payment.get(
                "remarks"
            )
            or ""
        )

        if remarks:

            elements.append(
                Paragraph(
                    "Remarks",
                    section_style
                )
            )

            elements.append(
                Paragraph(
                    str(remarks),
                    normal_style
                )
            )

        # -----------------------------------------------------
        # FOOTER
        # -----------------------------------------------------

        elements.append(
            Spacer(
                1,
                20
            )
        )

        elements.append(
            Paragraph(
                "This is a computer-generated payment receipt.",
                subtitle_style
            )
        )

        document.build(
            elements
        )

        output.seek(0)

        return output