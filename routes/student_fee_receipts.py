from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    make_response,
    send_file
)

from models.fee_payment import FeePayment
from models.student import Student
from services.fee_documents import FeeDocuments


student_fee_receipts_bp = Blueprint(
    "student_fee_receipts",
    __name__,
    url_prefix="/student/fees"
)


# ============================================================
# STUDENT ACCESS
# ============================================================

def student_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(
                url_for("auth.login_user")
            )

        if session.get("role") != "student":
            return jsonify({
                "success": False,
                "message": "Student access required."
            }), 403

        student = Student.get_by_user_id(
            session.get("user_id")
        )

        if not student:
            return jsonify({
                "success": False,
                "message": "Student profile not found."
            }), 404

        if student.get("registration_status") != "approved":
            return redirect(
                url_for("auth.pending")
            )

        return function(
            student,
            *args,
            **kwargs
        )

    return decorated_function


# ============================================================
# VERIFY PAYMENT BELONGS TO CURRENT STUDENT
# ============================================================

def get_student_payment(student, payment_id):

    payment = FeePayment.get_payment_by_id(
        payment_id
    )

    if not payment:
        return None

    # --------------------------------------------------------
    # IMPORTANT SECURITY CHECK
    # --------------------------------------------------------

    if int(payment["student_id"]) != int(student["id"]):
        return None

    return payment


# ============================================================
# VIEW RECEIPT
# ============================================================

@student_fee_receipts_bp.route(
    "/payments/<int:payment_id>/receipt/view",
    methods=["GET"]
)
@student_required
def view_receipt(student, payment_id):

    payment = get_student_payment(
        student,
        payment_id
    )

    if not payment:

        return render_template(
            "errors/404.html"
        ), 404

    return render_template(
        "student/payment_receipt.html",
        payment=payment,
        student=student
    )


# ============================================================
# DOWNLOAD RECEIPT
# ============================================================

@student_fee_receipts_bp.route(
    "/payments/<int:payment_id>/receipt",
    methods=["GET"]
)
@student_required
def download_receipt(student, payment_id):

    payment = get_student_payment(
        student,
        payment_id
    )

    if not payment:

        return render_template(
            "errors/404.html"
        ), 404

    try:
        pdf_file = FeeDocuments.create_receipt_pdf(payment)
        filename = (
            "HostelNexus_Receipt_"
            + str(payment["receipt_number"])
            + ".pdf"
        )

        return send_file(
            pdf_file,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as error:
        print("STUDENT RECEIPT GENERATION ERROR:", error)
        return jsonify({
            "success": False,
            "message": "Unable to generate receipt."
        }), 500