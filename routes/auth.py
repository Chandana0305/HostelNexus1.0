import os
import secrets
import uuid
from datetime import datetime
from models.user import User
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.utils import secure_filename

from services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]


def ensure_csrf_token():
    return get_csrf_token()


def validate_csrf():
    token = request.form.get("csrf_token", "")
    session_token = session.get("csrf_token", "")

    if not token or not session_token:
        return False

    return secrets.compare_digest(token, session_token)


def allowed_image(filename):
    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in current_app.config.get(
        "ALLOWED_IMAGE_EXTENSIONS",
        {"jpg", "jpeg", "png", "webp"}
    )


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template(
            "auth/register.html",
            csrf_token=get_csrf_token()
        )

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Security token expired. Please refresh the page and try again."
        }), 400

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    student_data = {
        "student_id": request.form.get("student_id", "").strip(),
        "first_name": request.form.get("first_name", "").strip(),
        "last_name": request.form.get("last_name", "").strip() or None,
        "email": request.form.get("email", "").strip().lower(),
        "phone": request.form.get("phone", "").strip() or None,
        "gender": request.form.get("gender", "").strip() or None,
        "date_of_birth": request.form.get("date_of_birth", "").strip() or None,
        "course": request.form.get("course", "").strip() or None,
        "department": request.form.get("department", "").strip() or None,
        "batch": request.form.get("batch", "").strip() or None,
        "year": request.form.get("year", "").strip() or None,
        "parent_name": request.form.get("parent_name", "").strip() or None,
        "parent_phone": request.form.get("parent_phone", "").strip() or None,
        "address": request.form.get("address", "").strip() or None,
        "profile_photo": None
    }

    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match."
        }), 400

    # -----------------------------------------------------
    # PROFILE PHOTO
    # -----------------------------------------------------

    photo = request.files.get("profile_photo")

    if photo and photo.filename:

        if not allowed_image(photo.filename):
            return jsonify({
                "success": False,
                "message": "Only JPG, JPEG, PNG and WEBP images are allowed."
            }), 400

        extension = secure_filename(
            photo.filename
        ).rsplit(".", 1)[1].lower()

        unique_filename = (
            uuid.uuid4().hex + "." + extension
        )

        upload_folder = os.path.join(
            current_app.root_path,
            "static",
            "uploads",
            "profile_photos"
        )

        os.makedirs(upload_folder, exist_ok=True)

        photo.save(
            os.path.join(
                upload_folder,
                unique_filename
            )
        )

        student_data["profile_photo"] = (
            "uploads/profile_photos/" + unique_filename
        )

    # -----------------------------------------------------
    # CREATE ACCOUNT
    # -----------------------------------------------------

    success, user_id, error_message = AuthService.register_student(
        username,
        password,
        confirm_password,
        student_data
    )

    if not success:

        if student_data.get("profile_photo"):

            saved_file = os.path.join(
                current_app.root_path,
                "static",
                student_data["profile_photo"]
            )

            if os.path.exists(saved_file):
                os.remove(saved_file)

        return jsonify({
            "success": False,
            "message": error_message
        }), 400

    return jsonify({
        "success": True,
        "message": (
            "Registration submitted successfully. "
            "Your account is waiting for Admin approval."
        ),
        "user_id": user_id,
        "redirect": url_for("login")
    }), 201


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login_user():

    if request.method == "GET":
        csrf_token = get_csrf_token()
        return render_template(
            "auth/login.html",
            csrf_token=csrf_token
        )

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Security token expired. Please refresh the page and try again."
        }), 400

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    selected_role = request.form.get(
        "role",
        "student"
    ).strip().lower()

    if selected_role not in ("student", "admin"):
        return jsonify({
            "success": False,
            "message": "Invalid account type."
        }), 400

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required."
        }), 400

    account = AuthService.find_user_with_student(username)

    if not account:
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    if account["role"] != selected_role:
        return jsonify({
            "success": False,
            "message": (
                "This username is not registered as a "
                + selected_role
                + " account."
            )
        }), 403

    if not AuthService.verify_password(
        account["password"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Invalid username or password."
        }), 401

    if account["status"] != "active":
        return jsonify({
            "success": False,
            "message": (
                "This account is currently inactive. "
                "Please contact the Administrator."
            )
        }), 403

    # -----------------------------------------------------
    # CREATE SESSION
    # -----------------------------------------------------

    session.clear()

    session["user_id"] = account["user_id"]
    session["username"] = account["username"]
    session["role"] = account["role"]
    session["login_at"] = datetime.now().isoformat()

    session["csrf_token"] = secrets.token_hex(32)

    # -----------------------------------------------------
    # STUDENT
    # -----------------------------------------------------

    if account["role"] == "student":

        registration_status = account.get(
            "registration_status"
        )

        if registration_status == "rejected":

            session.clear()

            return jsonify({
                "success": False,
                "message": (
                    "Your student registration was rejected. "
                    "Please contact the Administrator."
                )
            }), 403

        if registration_status != "approved":

            return jsonify({
                "success": True,
                "pending": True,
                "message": (
                    "Login successful. "
                    "Your account is waiting for Admin approval."
                ),
                "redirect": url_for(
                    "auth.pending"
                )
            }), 200

        return jsonify({
            "success": True,
            "message": "Welcome back!",
            "redirect": url_for(
                "auth.student_dashboard"
            )
        }), 200

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    return jsonify({
        "success": True,
        "message": "Admin login successful.",
        "redirect": url_for(
            "auth.admin_dashboard"
        )
    }), 200


# =========================================================
# STUDENT APPROVAL PENDING
# =========================================================

@auth_bp.route("/pending")
def pending():

    if session.get("role") != "student":
        return redirect(url_for("login"))

    student = AuthService.find_student(
        session.get("user_id")
    )

    if not student:
        session.clear()
        return redirect(url_for("login"))

    if student["registration_status"] == "approved":
        return redirect(
            url_for("auth.student_dashboard")
        )

    return render_template(
        "auth/pending.html",
        student=student,
        csrf_token=get_csrf_token()
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@auth_bp.route("/student/dashboard")
def student_dashboard():

    # ============================================================
    # STUDENT LOGIN CHECK
    # ============================================================

    if "user_id" not in session:

        return redirect(
            url_for("auth.login_user")
        )

    # ============================================================
    # ROLE CHECK
    # ============================================================

    if session.get("role") != "student":

        return jsonify({
            "success": False,
            "message": "Student access required."
        }), 403

    # ============================================================
    # GET CURRENT USER
    # ============================================================

    user_id = session.get("user_id")

    user = User.get_by_id(user_id)

    if not user:

        session.clear()

        return redirect(
            url_for("auth.login_user")
        )

    # ============================================================
    # ACCOUNT STATUS CHECK
    # ============================================================

    if user.get("status") != "active":

        session.clear()

        return jsonify({
            "success": False,
            "message": (
                "Your account is currently inactive. "
                "Please contact the administrator."
            )
        }), 403

    # ============================================================
    # GET STUDENT PROFILE
    # ============================================================

    student = User.get_student_by_user_id(
        user_id
    )

    if not student:

        return jsonify({
            "success": False,
            "message": (
                "Student profile could not be found."
            )
        }), 404

    # ============================================================
    # REGISTRATION APPROVAL CHECK
    # ============================================================

    if student.get("registration_status") != "approved":

        return redirect(
            url_for("auth.pending")
        )

    # ============================================================
    # RENDER STUDENT DASHBOARD
    # ============================================================

    return render_template(
        "dashboard/student.html",
        student=student,
        user=user,
        csrf_token=ensure_csrf_token()
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@auth_bp.route("/admin/dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    return render_template(
        "dashboard/admin.html",
        admin_username=session.get("username"),
        csrf_token=get_csrf_token()
    )


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout", methods=["POST"])
def logout():

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Security token expired."
        }), 400

    session.clear()

    if request.form:
        return redirect(url_for("login"))

    return jsonify({
        "success": True,
        "message": "You have been logged out.",
        "redirect": url_for("login")
    }), 200