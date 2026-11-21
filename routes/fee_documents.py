from functools import wraps
import secrets

from flask import (
    Blueprint,
    jsonify,
    redirect,
    request,
    send_file,
    session,
    url_for
)

from models.fee_payment import FeePayment
from services.fee_documents import FeeDocuments


fee_documents_bp = Blueprint(
    "fee_documents",
    __name__,
    url_prefix="/admin/fees"
)


# ============================================================
# ADMIN ACCESS
# ============================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(
                url_for("auth.login_user")
            )

        if session.get("role") != "admin":

            return jsonify({
                "success": False,
                "message": "Administrator access required."
            }), 403

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# CSRF
# ============================================================

def validate_csrf():

    token = request.form.get(
        "csrf_token",
        ""
    )

    if not token:

        token = request.headers.get(
            "X-CSRF-Token",
            ""
        )

    session_token = session.get(
        "csrf_token",
        ""
    )

    if not token or not session_token:
        return False

    return secrets.compare_digest(
        token,
        session_token
    )


# ============================================================
# DOWNLOAD PAYMENT RECEIPT
# ============================================================

@fee_documents_bp.route(
    "/payments/<int:payment_id>/receipt",
    methods=["GET"]
)
@admin_required
def download_receipt(payment_id):

    payment = FeePayment.get_payment_by_id(
        payment_id
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment not found."
        }), 404

    try:

        pdf_file = (
            FeeDocuments.create_receipt_pdf(
                payment
            )
        )

        receipt_number = (
            payment.get(
                "receipt_number"
            )
            or "receipt"
        )

        filename = (
            str(receipt_number)
            + ".pdf"
        )

        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as error:

        print(
            "RECEIPT GENERATION ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate receipt."
        }), 500


# ============================================================
# VIEW RECEIPT
# ============================================================

@fee_documents_bp.route(
    "/payments/<int:payment_id>/receipt/view",
    methods=["GET"]
)
@admin_required
def view_receipt(payment_id):

    payment = FeePayment.get_payment_by_id(
        payment_id
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment not found."
        }), 404

    try:

        pdf_file = (
            FeeDocuments.create_receipt_pdf(
                payment
            )
        )

        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=False
        )

    except Exception as error:

        print(
            "RECEIPT VIEW ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate receipt."
        }), 500


# ============================================================
# EXCEL BATCH REPORT
# ============================================================

@fee_documents_bp.route(
    "/reports/export",
    methods=["GET"]
)
@admin_required
def export_excel():

    batch = request.args.get(
        "batch",
        ""
    ).strip()

    try:

        rows = (
            FeePayment.get_batch_payment_report(
                batch or None
            )
        )

        excel_file = (
            FeeDocuments.create_excel_report(
                rows,
                batch=batch or None
            )
        )

        if batch:

            safe_batch = (
                batch
                .replace(" ", "_")
                .replace("/", "-")
                .replace("\\", "-")
            )

            filename = (
                "HostelNexus_Fee_Report_"
                + safe_batch
                + ".xlsx"
            )

        else:

            filename = (
                "HostelNexus_Fee_Report_All_Batches.xlsx"
            )

        return send_file(
            excel_file,
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            as_attachment=True,
            download_name=filename
        )

    except Exception as error:

        print(
            "EXCEL EXPORT ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to generate Excel report."
        }), 500