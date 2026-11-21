from functools import wraps
import secrets
from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from models.fee_payment import FeePayment


admin_fees_bp = Blueprint(
    "admin_fees",
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

def ensure_csrf_token():

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]


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
# FEE & PAYMENT DASHBOARD
# ============================================================

@admin_fees_bp.route("/")
@admin_required
def fee_dashboard():

    csrf_token = ensure_csrf_token()

    fee_structures = (
        FeePayment.get_all_fee_structures()
    )

    students = (
        FeePayment.get_students()
    )

    payments = (
        FeePayment.get_all_payments()
    )

    batches = (
        FeePayment.get_batches()
    )

    batch_report = FeePayment.get_batch_payment_report()

    return render_template(
        "admin/fees.html",
        fee_structures=fee_structures,
        students=students,
        payments=payments,
        batches=batches,
        batch_report=batch_report,
        csrf_token=csrf_token
    )

# ============================================================
# FEE STRUCTURES
# ============================================================

@admin_fees_bp.route(
    "/structures",
    methods=["GET"]
)
@admin_required
def get_fee_structures():

    return jsonify({
        "success": True,
        "fee_structures":
            FeePayment.get_all_fee_structures()
    })


@admin_fees_bp.route(
    "/structures/<int:fee_structure_id>",
    methods=["GET"]
)
@admin_required
def get_fee_structure(
    fee_structure_id
):

    fee_structure = (
        FeePayment.get_fee_structure_by_id(
            fee_structure_id
        )
    )

    if not fee_structure:

        return jsonify({
            "success": False,
            "message": "Fee structure not found."
        }), 404

    return jsonify({
        "success": True,
        "fee_structure": fee_structure
    })


@admin_fees_bp.route(
    "/structures/add",
    methods=["POST"]
)
@admin_required
def add_fee_structure():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    batch = request.form.get(
        "batch",
        ""
    ).strip()

    academic_year = request.form.get(
        "academic_year",
        ""
    ).strip()

    hostel_fee = request.form.get(
        "hostel_fee",
        "0"
    ).strip()

    mess_fee = request.form.get(
        "mess_fee",
        "0"
    ).strip()

    security_deposit = request.form.get(
        "security_deposit",
        "0"
    ).strip()

    other_fee = request.form.get(
        "other_fee",
        "0"
    ).strip()

    due_date = request.form.get(
        "due_date",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "active"
    ).strip()

    if not batch:

        return jsonify({
            "success": False,
            "message": "Batch is required."
        }), 400

    if not academic_year:

        return jsonify({
            "success": False,
            "message": "Academic year is required."
        }), 400

    try:

        hostel_fee = float(
            hostel_fee or 0
        )

        mess_fee = float(
            mess_fee or 0
        )

        security_deposit = float(
            security_deposit or 0
        )

        other_fee = float(
            other_fee or 0
        )

        if (
            hostel_fee < 0
            or mess_fee < 0
            or security_deposit < 0
            or other_fee < 0
        ):

            raise ValueError

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Fee amounts must be valid positive numbers."
        }), 400

    try:

        fee_structure_id = (
            FeePayment.create_fee_structure(
                batch=batch,
                academic_year=academic_year,
                hostel_fee=hostel_fee,
                mess_fee=mess_fee,
                security_deposit=security_deposit,
                other_fee=other_fee,
                due_date=due_date or None,
                status=status
            )
        )

        return jsonify({
            "success": True,
            "message": "Fee structure created successfully.",
            "fee_structure_id":
                fee_structure_id
        })

    except Exception as error:

        print(
            "ADD FEE STRUCTURE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to create fee structure."
        }), 500


@admin_fees_bp.route(
    "/structures/<int:fee_structure_id>/update",
    methods=["POST"]
)
@admin_required
def update_fee_structure(
    fee_structure_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    existing = (
        FeePayment.get_fee_structure_by_id(
            fee_structure_id
        )
    )

    if not existing:

        return jsonify({
            "success": False,
            "message": "Fee structure not found."
        }), 404

    batch = request.form.get(
        "batch",
        ""
    ).strip()

    academic_year = request.form.get(
        "academic_year",
        ""
    ).strip()

    hostel_fee = request.form.get(
        "hostel_fee",
        "0"
    ).strip()

    mess_fee = request.form.get(
        "mess_fee",
        "0"
    ).strip()

    security_deposit = request.form.get(
        "security_deposit",
        "0"
    ).strip()

    other_fee = request.form.get(
        "other_fee",
        "0"
    ).strip()

    due_date = request.form.get(
        "due_date",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "active"
    ).strip()

    if not batch:

        return jsonify({
            "success": False,
            "message": "Batch is required."
        }), 400

    if not academic_year:

        return jsonify({
            "success": False,
            "message": "Academic year is required."
        }), 400

    try:

        hostel_fee = float(
            hostel_fee or 0
        )

        mess_fee = float(
            mess_fee or 0
        )

        security_deposit = float(
            security_deposit or 0
        )

        other_fee = float(
            other_fee or 0
        )

        if (
            hostel_fee < 0
            or mess_fee < 0
            or security_deposit < 0
            or other_fee < 0
        ):

            raise ValueError

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Fee amounts must be valid positive numbers."
        }), 400

    try:

        success = (
            FeePayment.update_fee_structure(
                fee_structure_id=
                    fee_structure_id,
                batch=batch,
                academic_year=academic_year,
                hostel_fee=hostel_fee,
                mess_fee=mess_fee,
                security_deposit=
                    security_deposit,
                other_fee=other_fee,
                due_date=due_date or None,
                status=status
            )
        )

        if not success:

            return jsonify({
                "success": False,
                "message": "Fee structure could not be updated."
            }), 400

        return jsonify({
            "success": True,
            "message": "Fee structure updated successfully."
        })

    except Exception as error:

        print(
            "UPDATE FEE STRUCTURE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update fee structure."
        }), 500


@admin_fees_bp.route(
    "/structures/<int:fee_structure_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_fee_structure(
    fee_structure_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    try:

        result = (
            FeePayment.delete_fee_structure(
                fee_structure_id
            )
        )

        if not result["success"]:

            return jsonify(result), 400

        return jsonify(result)

    except Exception as error:

        print(
            "DELETE FEE STRUCTURE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete fee structure."
        }), 500


# ============================================================
# STUDENTS
# ============================================================

@admin_fees_bp.route(
    "/students",
    methods=["GET"]
)
@admin_required
def get_students():

    return jsonify({
        "success": True,
        "students":
            FeePayment.get_students()
    })


@admin_fees_bp.route(
    "/students/<int:student_id>",
    methods=["GET"]
)
@admin_required
def get_student(
    student_id
):

    student = (
        FeePayment.get_student_by_id(
            student_id
        )
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found."
        }), 404

    summary = (
        FeePayment.get_student_payment_summary(
            student_id
        )
    )

    payments = (
        FeePayment.get_student_payments(
            student_id
        )
    )

    return jsonify({
        "success": True,
        "student": student,
        "summary": summary,
        "payments": payments
    })


# ============================================================
# PAYMENTS
# ============================================================

@admin_fees_bp.route(
    "/payments",
    methods=["GET"]
)
@admin_required
def get_payments():

    return jsonify({
        "success": True,
        "payments":
            FeePayment.get_all_payments()
    })


@admin_fees_bp.route("/payments/add", methods=["POST"])
@admin_required
def add_payment():

    # =========================================================
    # CSRF VALIDATION
    # =========================================================

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    # =========================================================
    # GET FORM DATA
    # =========================================================

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    fee_structure_id = request.form.get(
        "fee_structure_id",
        ""
    ).strip()

    amount = request.form.get(
        "amount",
        ""
    ).strip()

    payment_method = request.form.get(
        "payment_method",
        ""
    ).strip()

    transaction_id = request.form.get(
        "transaction_id",
        ""
    ).strip()

    payment_date = request.form.get(
        "payment_date",
        ""
    ).strip()

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()


    # =========================================================
    # REQUIRED VALIDATION
    # =========================================================

    if not student_id:

        return jsonify({
            "success": False,
            "message": "Please select a student."
        }), 400


    if not fee_structure_id:

        return jsonify({
            "success": False,
            "message": "Please select a fee structure."
        }), 400


    if not amount:

        return jsonify({
            "success": False,
            "message": "Please enter the payment amount."
        }), 400


    if not payment_method:

        return jsonify({
            "success": False,
            "message": "Please select a payment method."
        }), 400


    if not payment_date:

        return jsonify({
            "success": False,
            "message": "Please select a payment date."
        }), 400


    # =========================================================
    # VALIDATE NUMERIC VALUES
    # =========================================================

    try:

        student_id = int(
            student_id
        )

        fee_structure_id = int(
            fee_structure_id
        )

        amount = float(
            amount
        )

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid student, fee structure or amount."
        }), 400


    if amount <= 0:

        return jsonify({
            "success": False,
            "message": "Payment amount must be greater than zero."
        }), 400


    # =========================================================
    # DATETIME-LOCAL CONVERSION
    # =========================================================
    #
    # Browser sends:
    #
    # 2026-09-20T20:18
    #
    # MySQL expects:
    #
    # 2026-09-20 20:18:00
    #
    # =========================================================

    try:

        payment_datetime = datetime.fromisoformat(
            payment_date
        )

        payment_date = payment_datetime.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid payment date."
        }), 400


    # =========================================================
    # VERIFY STUDENT
    # =========================================================

    student = FeePayment.get_student_by_id(
        student_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Selected student was not found."
        }), 404


    # =========================================================
    # VERIFY FEE STRUCTURE
    # =========================================================

    fee_structure = (
        FeePayment.get_fee_structure_by_id(
            fee_structure_id
        )
    )

    if not fee_structure:

        return jsonify({
            "success": False,
            "message": "Selected fee structure was not found."
        }), 404


    if fee_structure.get("status") != "active":

        return jsonify({
            "success": False,
            "message": "Selected fee structure is inactive."
        }), 400


    # =========================================================
    # CREATE PAYMENT
    # =========================================================

    try:

        result = FeePayment.create_payment(

            student_id=student_id,

            fee_structure_id=fee_structure_id,

            amount=amount,

            payment_method=payment_method,

            transaction_id=(
                transaction_id
                if transaction_id
                else None
            ),

            payment_date=payment_date,

            remarks=(
                remarks
                if remarks
                else None
            )
        )


        if not result["success"]:

            return jsonify(result), 400


        return jsonify({

            "success": True,

            "message": (
                "Payment recorded successfully."
            ),

            "payment_id": result[
                "payment_id"
            ],

            "receipt_number": result[
                "receipt_number"
            ]

        })


    except Exception as error:

        print(
            "PAYMENT CREATION ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message": (
                "Unable to record payment. "
                "Please try again."
            )

        }), 500


@admin_fees_bp.route(
    "/payments/<int:payment_id>",
    methods=["GET"]
)
@admin_required
def payment_details(
    payment_id
):

    payment = (
        FeePayment.get_payment_by_id(
            payment_id
        )
    )

    if not payment:

        return jsonify({
            "success": False,
            "message": "Payment not found."
        }), 404

    return jsonify({
        "success": True,
        "payment": payment
    })


# ============================================================
# BATCH REPORT
# ============================================================

@admin_fees_bp.route(
    "/reports/batch",
    methods=["GET"]
)
@admin_required
def batch_report():

    batch = request.args.get(
        "batch",
        ""
    ).strip()

    report = (
        FeePayment.get_batch_payment_report(
            batch or None
        )
    )

    return jsonify({
        "success": True,
        "batch": batch,
        "report": report
    })


@admin_fees_bp.route(
    "/reports/batches",
    methods=["GET"]
)
@admin_required
def report_batches():

    return jsonify({
        "success": True,
        "batches":
            FeePayment.get_batches()
    })


# ============================================================
# STUDENT PAYMENT SUMMARY
# ============================================================

@admin_fees_bp.route(
    "/student/<int:student_id>/summary",
    methods=["GET"]
)
@admin_required
def student_payment_summary(
    student_id
):

    student = (
        FeePayment.get_student_by_id(
            student_id
        )
    )

    if not student:

        return jsonify({
            "success": False,
            "message": "Student not found."
        }), 404

    summary = (
        FeePayment.get_student_payment_summary(
            student_id
        )
    )

    return jsonify({
        "success": True,
        "student": student,
        "summary": summary
    })