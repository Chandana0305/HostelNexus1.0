from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    session,
    url_for
)

from models.fee_payment import FeePayment
from models.student import Student


student_fees_bp = Blueprint(
    "student_fees",
    __name__,
    url_prefix="/student/fees"
)


# ============================================================
# STUDENT ACCESS
# ============================================================

def student_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        # ----------------------------------------------------
        # LOGIN CHECK
        # ----------------------------------------------------

        if "user_id" not in session:

            return redirect(
                url_for("auth.login_user")
            )


        # ----------------------------------------------------
        # ROLE CHECK
        # ----------------------------------------------------

        if session.get("role") != "student":

            return jsonify({
                "success": False,
                "message": "Student access required."
            }), 403


        # ----------------------------------------------------
        # GET STUDENT FROM DATABASE
        # ----------------------------------------------------

        student = Student.get_by_user_id(
            session.get("user_id")
        )


        if not student:

            return jsonify({
                "success": False,
                "message": "Student profile not found."
            }), 404


        # ----------------------------------------------------
        # CHECK ACTUAL DATABASE REGISTRATION STATUS
        # ----------------------------------------------------

        if student.get("registration_status") != "approved":

            return redirect(
                url_for("auth.pending")
            )


        # ----------------------------------------------------
        # STORE STUDENT RECORD ID FOR CURRENT REQUEST
        # ----------------------------------------------------

        session["student_record_id"] = student["id"]

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# STUDENT FEE DASHBOARD
# ============================================================

@student_fees_bp.route("/")
@student_required
def fee_dashboard():

    # --------------------------------------------------------
    # GET CURRENT STUDENT
    # --------------------------------------------------------

    student = Student.get_by_user_id(
        session.get("user_id")
    )


    if not student:

        return render_template(
            "errors/404.html"
        ), 404


    student_record_id = student["id"]


    # --------------------------------------------------------
    # PAYMENT SUMMARY
    # --------------------------------------------------------

    summary = FeePayment.get_student_payment_summary(
        student_record_id
    )


    # --------------------------------------------------------
    # PAYMENT HISTORY
    # --------------------------------------------------------

    payments = FeePayment.get_student_payments(
        student_record_id
    )


    # --------------------------------------------------------
    # CURRENT ACTIVE FEE STRUCTURE
    # --------------------------------------------------------

    active_structures = (
        FeePayment.get_active_fee_structures()
    )


    fee_structure = None

    student_batch = student.get(
        "batch"
    )


    for fee in active_structures:

        fee_batch = str(
            fee.get("batch", "")
        ).strip().lower()

        current_batch = str(
            student_batch or ""
        ).strip().lower()


        if fee_batch == current_batch:

            fee_structure = fee

            break


    # --------------------------------------------------------
    # RENDER STUDENT FEE PAGE
    # --------------------------------------------------------

    return render_template(

        "student/fees.html",

        student=student,

        summary=summary,

        payments=payments,

        fee_structure=fee_structure
    )


# ============================================================
# PAYMENT HISTORY API
# ============================================================

@student_fees_bp.route(
    "/payments",
    methods=["GET"]
)
@student_required
def payment_history():

    student = Student.get_by_user_id(
        session.get("user_id")
    )


    if not student:

        return jsonify({

            "success": False,

            "message": (
                "Student profile not found."
            )

        }), 404


    payments = FeePayment.get_student_payments(
        student["id"]
    )


    return jsonify({

        "success": True,

        "payments": payments

    })


# ============================================================
# FEE SUMMARY API
# ============================================================

@student_fees_bp.route(
    "/summary",
    methods=["GET"]
)
@student_required
def fee_summary():

    student = Student.get_by_user_id(
        session.get("user_id")
    )


    if not student:

        return jsonify({

            "success": False,

            "message": (
                "Student profile not found."
            )

        }), 404


    summary = FeePayment.get_student_payment_summary(
        student["id"]
    )


    return jsonify({

        "success": True,

        "summary": summary

    })