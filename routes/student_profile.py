import os
import secrets
import uuid
from functools import wraps

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from werkzeug.utils import secure_filename

from config import Config
from models.student import Student
from models.user import User
from services.auth_service import AuthService


student_profile_bp = Blueprint(
    "student_profile",
    __name__,
    url_prefix="/student/profile"
)


# ============================================================
# CSRF TOKEN
# ============================================================

def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]


def validate_csrf():
    token = request.form.get("csrf_token", "")

    session_token = session.get("csrf_token", "")

    if not token or not session_token:
        return False

    return secrets.compare_digest(
        token,
        session_token
    )


# ============================================================
# STUDENT ACCESS DECORATOR
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

        return function(*args, **kwargs)

    return decorated_function


# ============================================================
# PROFILE PAGE
# ============================================================

@student_profile_bp.route("/")
@student_required
def profile():

    user_id = session.get("user_id")

    student = Student.get_by_user_id(user_id)

    if not student:
        return render_template(
            "errors/404.html"
        ), 404

    if student.get("registration_status") != "approved":
        return redirect(
            url_for("auth.pending")
        )

    csrf_token = ensure_csrf_token()

    return render_template(
        "student/profile.html",
        student=student,
        csrf_token=csrf_token
    )


@student_profile_bp.route(
    "/credentials",
    methods=["POST"]
)
@student_required
def update_credentials():

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Security token expired. Please refresh the page and try again."
        }), 400

    user_id = session.get("user_id")
    user = User.get_by_id(user_id)
    current_password = request.form.get("current_password", "")
    username = request.form.get("username", "").strip()
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not user or not AuthService.verify_password(
        user.get("password"), current_password
    ):
        return jsonify({
            "success": False,
            "message": "Current password is incorrect."
        }), 400

    if not username or len(username) < 4 or len(username) > 50:
        return jsonify({
            "success": False,
            "message": "Username must contain 4 to 50 characters."
        }), 400

    if new_password and len(new_password) < 8:
        return jsonify({
            "success": False,
            "message": "New password must contain at least 8 characters."
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "New passwords do not match."
        }), 400

    existing_user = User.get_by_username(username)

    if existing_user and int(existing_user["id"]) != int(user_id):
        return jsonify({
            "success": False,
            "message": "That username is already in use."
        }), 400

    hashed_password = (
        AuthService.hash_password(new_password)
        if new_password else None
    )

    User.update_credentials(
        user_id,
        username,
        hashed_password
    )

    session["username"] = username

    return jsonify({
        "success": True,
        "message": "Login credentials updated successfully."
    })


# ============================================================
# UPDATE PROFILE
# ============================================================

@student_profile_bp.route(
    "/update",
    methods=["POST"]
)
@student_required
def update_profile():

    # --------------------------------------------------------
    # CSRF VALIDATION
    # --------------------------------------------------------

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": (
                "Security token expired. "
                "Please refresh the page and try again."
            )
        }), 400

    # --------------------------------------------------------
    # CURRENT USER
    # --------------------------------------------------------

    user_id = session.get("user_id")

    student = Student.get_by_user_id(user_id)

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    # --------------------------------------------------------
    # GET FORM DATA
    # --------------------------------------------------------

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth",
        ""
    ).strip()

    parent_name = request.form.get(
        "parent_name",
        ""
    ).strip()

    parent_phone = request.form.get(
        "parent_phone",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    # --------------------------------------------------------
    # REQUIRED FIELD VALIDATION
    # --------------------------------------------------------

    if not first_name:

        return jsonify({
            "success": False,
            "message": "First name is required."
        }), 400

    if not last_name:

        return jsonify({
            "success": False,
            "message": "Last name is required."
        }), 400

    if not email:

        return jsonify({
            "success": False,
            "message": "Email address is required."
        }), 400

    if not phone:

        return jsonify({
            "success": False,
            "message": "Phone number is required."
        }), 400

    # --------------------------------------------------------
    # NAME VALIDATION
    # --------------------------------------------------------

    if len(first_name) < 2:

        return jsonify({
            "success": False,
            "message": (
                "First name must contain at least "
                "2 characters."
            )
        }), 400

    if len(last_name) < 1:

        return jsonify({
            "success": False,
            "message": "Please enter a valid last name."
        }), 400

    # --------------------------------------------------------
    # EMAIL VALIDATION
    # --------------------------------------------------------

    if (
        "@" not in email
        or "." not in email.split("@")[-1]
    ):

        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400

    # --------------------------------------------------------
    # PHONE VALIDATION
    # --------------------------------------------------------

    phone_digits = "".join(
        character
        for character in phone
        if character.isdigit()
    )

    if len(phone_digits) != 10:

        return jsonify({
            "success": False,
            "message": (
                "Phone number must contain "
                "10 digits."
            )
        }), 400

    # --------------------------------------------------------
    # PARENT PHONE VALIDATION
    # --------------------------------------------------------

    if parent_phone:

        parent_phone_digits = "".join(
            character
            for character in parent_phone
            if character.isdigit()
        )

        if len(parent_phone_digits) != 10:

            return jsonify({
                "success": False,
                "message": (
                    "Parent phone number must contain "
                    "10 digits."
                )
            }), 400

    # --------------------------------------------------------
    # GENDER VALIDATION
    # --------------------------------------------------------

    allowed_genders = {
        "Male",
        "Female",
        "Other"
    }

    if gender and gender not in allowed_genders:

        return jsonify({
            "success": False,
            "message": "Invalid gender selected."
        }), 400

    # --------------------------------------------------------
    # DUPLICATE EMAIL CHECK
    # --------------------------------------------------------

    if Student.email_exists_for_other_student(
        email,
        user_id
    ):

        return jsonify({
            "success": False,
            "message": (
                "This email address is already "
                "registered with another student."
            )
        }), 409

    # --------------------------------------------------------
    # PREPARE DATA
    # --------------------------------------------------------

    profile_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone_digits,
        "gender": gender or None,
        "date_of_birth": date_of_birth or None,
        "parent_name": parent_name or None,
        "parent_phone": (
            parent_phone_digits
            if parent_phone
            else None
        ),
        "address": address or None
    }

    # --------------------------------------------------------
    # UPDATE DATABASE
    # --------------------------------------------------------

    try:

        updated = Student.update_profile(
            user_id,
            profile_data
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to update your profile "
                "right now. Please try again."
            )
        }), 500

    if not updated:

        return jsonify({
            "success": False,
            "message": "No profile changes were saved."
        }), 400

    # --------------------------------------------------------
    # UPDATE SESSION NAME
    # --------------------------------------------------------

    session["student_name"] = (
        f"{first_name} {last_name}"
    ).strip()

    return jsonify({
        "success": True,
        "message": "Profile updated successfully."
    })


# ============================================================
# UPLOAD / CHANGE PROFILE PHOTO
# ============================================================

@student_profile_bp.route(
    "/photo/upload",
    methods=["POST"]
)
@student_required
def upload_profile_photo():

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": (
                "Security token expired. "
                "Please refresh the page and try again."
            )
        }), 400

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if "profile_photo" not in request.files:

        return jsonify({
            "success": False,
            "message": "Please select a profile photo."
        }), 400

    file = request.files["profile_photo"]

    if not file or not file.filename:

        return jsonify({
            "success": False,
            "message": "Please select a profile photo."
        }), 400

    # --------------------------------------------------------
    # FILE EXTENSION
    # --------------------------------------------------------

    original_filename = secure_filename(
        file.filename
    )

    if "." not in original_filename:

        return jsonify({
            "success": False,
            "message": "Invalid image file."
        }), 400

    extension = (
        original_filename
        .rsplit(".", 1)[1]
        .lower()
    )

    allowed_extensions = getattr(
        Config,
        "ALLOWED_IMAGE_EXTENSIONS",
        {
            "jpg",
            "jpeg",
            "png",
            "webp"
        }
    )

    if extension not in allowed_extensions:

        return jsonify({
            "success": False,
            "message": (
                "Only JPG, JPEG, PNG and WEBP "
                "images are allowed."
            )
        }), 400

    # --------------------------------------------------------
    # FILE SIZE CHECK
    # --------------------------------------------------------

    file.stream.seek(0, os.SEEK_END)

    file_size = file.stream.tell()

    file.stream.seek(0)

    max_size = 5 * 1024 * 1024

    if file_size > max_size:

        return jsonify({
            "success": False,
            "message": (
                "Profile photo must be "
                "5 MB or smaller."
            )
        }), 400

    if file_size == 0:

        return jsonify({
            "success": False,
            "message": "The selected image is empty."
        }), 400

    # --------------------------------------------------------
    # CURRENT STUDENT
    # --------------------------------------------------------

    user_id = session.get("user_id")

    student = Student.get_by_user_id(user_id)

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    # --------------------------------------------------------
    # CREATE UNIQUE FILE NAME
    # --------------------------------------------------------

    filename = (
        f"student_{user_id}_"
        f"{uuid.uuid4().hex}."
        f"{extension}"
    )

    upload_folder = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "static",
        "uploads",
        "profile_photos"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        filename
    )

    # --------------------------------------------------------
    # SAVE NEW PHOTO
    # --------------------------------------------------------

    try:

        file.save(file_path)

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to save the profile photo."
            )
        }), 500

    # --------------------------------------------------------
    # DELETE OLD PHOTO FROM SERVER
    # --------------------------------------------------------

    old_photo = student.get(
        "profile_photo"
    )

    if old_photo:

        old_filename = os.path.basename(
            old_photo
        )

        old_path = os.path.join(
            upload_folder,
            old_filename
        )

        if (
            os.path.isfile(old_path)
            and old_filename != filename
        ):

            try:
                os.remove(old_path)
            except OSError:
                pass

    # --------------------------------------------------------
    # DATABASE VALUE
    # --------------------------------------------------------

    photo_database_path = (
        f"uploads/profile_photos/{filename}"
    )

    try:

        updated = Student.update_profile_photo(
            user_id,
            photo_database_path
        )

    except Exception:

        # Remove newly uploaded file if DB update fails
        if os.path.isfile(file_path):

            try:
                os.remove(file_path)
            except OSError:
                pass

        return jsonify({
            "success": False,
            "message": (
                "Unable to update your profile "
                "photo right now."
            )
        }), 500

    if not updated:

        if os.path.isfile(file_path):

            try:
                os.remove(file_path)
            except OSError:
                pass

        return jsonify({
            "success": False,
            "message": (
                "Profile photo could not be updated."
            )
        }), 500

    return jsonify({
        "success": True,
        "message": "Profile photo updated successfully.",
        "photo_url": url_for(
            "static",
            filename=photo_database_path
        )
    })


# ============================================================
# DELETE PROFILE PHOTO
# ============================================================

@student_profile_bp.route(
    "/photo/delete",
    methods=["POST"]
)
@student_required
def delete_profile_photo():

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": (
                "Security token expired. "
                "Please refresh the page and try again."
            )
        }), 400

    # --------------------------------------------------------
    # CURRENT USER
    # --------------------------------------------------------

    user_id = session.get("user_id")

    student = Student.get_by_user_id(user_id)

    if not student:

        return jsonify({
            "success": False,
            "message": "Student profile not found."
        }), 404

    old_photo = student.get(
        "profile_photo"
    )

    # --------------------------------------------------------
    # DATABASE UPDATE
    # --------------------------------------------------------

    try:

        deleted = Student.delete_profile_photo(
            user_id
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": (
                "Unable to delete the profile photo "
                "right now."
            )
        }), 500

    if not deleted:

        return jsonify({
            "success": False,
            "message": (
                "Profile photo could not be deleted."
            )
        }), 400

    # --------------------------------------------------------
    # DELETE FILE FROM SERVER
    # --------------------------------------------------------

    if old_photo:

        upload_folder = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "static",
            "uploads",
            "profile_photos"
        )

        old_filename = os.path.basename(
            old_photo
        )

        old_path = os.path.join(
            upload_folder,
            old_filename
        )

        if os.path.isfile(old_path):

            try:
                os.remove(old_path)
            except OSError:
                pass

    return jsonify({
        "success": True,
        "message": (
            "Profile photo deleted successfully."
        )
    })