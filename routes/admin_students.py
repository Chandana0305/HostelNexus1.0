from functools import wraps
import secrets

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from models.student import Student
from services.auth_service import AuthService


admin_students_bp = Blueprint(
    "admin_students",
    __name__,
    url_prefix="/admin/students"
)


# ============================================================
# ADMIN ACCESS PROTECTION
# ============================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        # User must be logged in
        if "user_id" not in session:
            return redirect(
                url_for("auth.login_user")
            )

        # Only Admin can access these routes
        if session.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": "Administrator access required."
            }), 403

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# CSRF PROTECTION
# ============================================================

def validate_csrf():

    token = request.form.get(
        "csrf_token",
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
# STUDENT MANAGEMENT HOME
# ============================================================

@admin_students_bp.route("/")
@admin_required
def students():

    statistics = Student.get_statistics()

    return render_template(
        "admin/students.html",
        statistics=statistics,
        students=Student.get_pending_students(),
        current_filter="pending"
    )


# ============================================================
# PENDING STUDENTS
# ============================================================

@admin_students_bp.route("/pending")
@admin_required
def pending_students():

    students = Student.get_pending_students()

    statistics = Student.get_statistics()

    return render_template(
        "admin/students.html",
        students=students,
        statistics=statistics,
        current_filter="pending"
    )


# ============================================================
# ALL STUDENTS
# ============================================================

@admin_students_bp.route("/all")
@admin_required
def all_students():

    students = Student.get_all_students()

    statistics = Student.get_statistics()

    return render_template(
        "admin/students.html",
        students=students,
        statistics=statistics,
        current_filter="all"
    )


@admin_students_bp.route(
    "/add",
    methods=["POST"]
)
@admin_required
def add_student():

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    student_data = {
        "student_id": request.form.get("student_id", "").strip(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "phone": request.form.get("phone", "").strip(),
        "gender": request.form.get("gender", "").strip() or None,
        "date_of_birth": request.form.get("date_of_birth", "").strip() or None,
        "course": request.form.get("course", "").strip(),
        "department": request.form.get("department", "").strip(),
        "batch": request.form.get("batch", "").strip(),
        "year": request.form.get("year", "").strip(),
        "parent_name": request.form.get("parent_name", "").strip() or None,
        "parent_phone": request.form.get("parent_phone", "").strip() or None,
        "address": request.form.get("address", "").strip() or None,
        "profile_photo": None
    }

    success, user_id, error_message = AuthService.register_student(
        request.form.get("username", "").strip(),
        request.form.get("password", ""),
        request.form.get("confirm_password", ""),
        student_data
    )

    if not success:
        return jsonify({
            "success": False,
            "message": error_message
        }), 400

    return jsonify({
        "success": True,
        "message": "Student added and sent for approval.",
        "user_id": user_id
    }), 201


# ============================================================
# SEARCH STUDENT BY USN / STUDENT ID ONLY
# ============================================================

@admin_students_bp.route("/search", methods=["GET"])
@admin_required
def search_student():

    student_id = request.args.get(
        "student_id",
        ""
    ).strip()

    if not student_id:

        return jsonify({
            "success": False,
            "message": "Please enter a Student ID / USN."
        }), 400

    student = Student.get_by_student_id(
        student_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": (
                "No student found with this "
                "Student ID / USN."
            )
        }), 404

    return jsonify({
        "success": True,
        "student": student
    })


# ============================================================
# VIEW STUDENT DETAILS
# ============================================================

@admin_students_bp.route(
    "/view/<int:student_id>"
)
@admin_required
def view_student(student_id):

    student = Student.get_by_id(
        student_id
    )

    if not student:

        return render_template(
            "errors/404.html"
        ), 404

    return render_template(
        "admin/student_details.html",
        student=student
    )


# ============================================================
# APPROVE STUDENT
# ============================================================

@admin_students_bp.route(
    "/<int:student_id>/approve",
    methods=["POST"]
)
@admin_required
def approve_student(student_id):

    # ----------------------------------------
    # CSRF validation
    # ----------------------------------------

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": (
                "Security token expired. "
                "Please refresh the page and try again."
            )
        }), 400

    # ----------------------------------------
    # Update registration status
    # ----------------------------------------

    try:

        success = Student.update_registration_status(
            student_id,
            "approved"
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to approve the student. "
                "Please try again."
            )
        }), 500

    if not success:

        return jsonify({
            "success": False,
            "message": "Student record not found."
        }), 404

    return jsonify({
        "success": True,
        "message": (
            "Student registration approved successfully."
        )
    }), 200


# ============================================================
# REJECT STUDENT
# ============================================================

@admin_students_bp.route(
    "/<int:student_id>/reject",
    methods=["POST"]
)
@admin_required
def reject_student(student_id):

    # ----------------------------------------
    # CSRF validation
    # ----------------------------------------

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": (
                "Security token expired. "
                "Please refresh the page and try again."
            )
        }), 400

    # ----------------------------------------
    # Update registration status
    # ----------------------------------------

    try:

        success = Student.update_registration_status(
            student_id,
            "rejected"
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to reject the student. "
                "Please try again."
            )
        }), 500

    if not success:

        return jsonify({
            "success": False,
            "message": "Student record not found."
        }), 404

    return jsonify({
        "success": True,
        "message": (
            "Student registration rejected."
        )
    }), 200


# ============================================================
# STUDENT STATISTICS API
# ============================================================

@admin_students_bp.route(
    "/statistics",
    methods=["GET"]
)
@admin_required
def statistics():

    try:

        data = Student.get_statistics()

        return jsonify({
            "success": True,
            "statistics": data
        }), 200

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to load student statistics."
            )
        }), 500