from werkzeug.security import generate_password_hash, check_password_hash

from models.user import User


class AuthService:

    # ---------------------------------------------------------
    # FIND USER
    # ---------------------------------------------------------
    @staticmethod
    def find_user(username):
        return User.get_by_username(username)

    # ---------------------------------------------------------
    # FIND USER WITH STUDENT DETAILS
    # ---------------------------------------------------------
    @staticmethod
    def find_user_with_student(username):
        return User.get_user_with_student(username)

    # ---------------------------------------------------------
    # FIND STUDENT
    # ---------------------------------------------------------
    @staticmethod
    def find_student(user_id):
        return User.get_student_by_user_id(user_id)

    # ---------------------------------------------------------
    # PASSWORD HASHING
    # ---------------------------------------------------------
    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    # ---------------------------------------------------------
    # PASSWORD VERIFICATION
    # ---------------------------------------------------------
    @staticmethod
    def verify_password(hashed_password, password):
        if not hashed_password or not password:
            return False

        try:
            return check_password_hash(hashed_password, password)
        except Exception:
            return False

    # ---------------------------------------------------------
    # REGISTRATION VALIDATION
    # ---------------------------------------------------------
    @staticmethod
    def validate_registration_data(username, password, confirm_password, student_data):

        errors = []

        # Username
        if not username:
            errors.append("Username is required.")
        elif len(username) < 4:
            errors.append("Username must contain at least 4 characters.")
        elif len(username) > 50:
            errors.append("Username must not exceed 50 characters.")

        # Password
        if not password:
            errors.append("Password is required.")
        elif len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        elif len(password) > 255:
            errors.append("Password is too long.")

        # Confirm password
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Student ID / USN
        student_id = student_data.get("student_id")

        if not student_id:
            errors.append("Student ID / USN is required.")
        elif len(student_id) > 50:
            errors.append("Student ID / USN is too long.")

        # First name
        first_name = student_data.get("first_name")

        if not first_name:
            errors.append("First name is required.")

        # Last name
        last_name = student_data.get("last_name")

        if not last_name:
            errors.append("Last name is required.")

        # Email
        email = student_data.get("email")

        if not email:
            errors.append("Email address is required.")
        elif "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")

        # Phone
        phone = student_data.get("phone")

        if not phone:
            errors.append("Phone number is required.")
        elif not phone.isdigit() or len(phone) != 10:
            errors.append("Phone number must contain exactly 10 digits.")

        # Gender
        gender = student_data.get("gender")

        if gender and gender not in ["Male", "Female", "Other"]:
            errors.append("Invalid gender selected.")

        # Course
        course = student_data.get("course")

        if not course:
            errors.append("Course is required.")

        # Department
        department = student_data.get("department")

        if not department:
            errors.append("Department is required.")

        # Batch
        batch = student_data.get("batch")

        if not batch:
            errors.append("Batch is required.")

        # Year
        year = student_data.get("year")

        if not year:
            errors.append("Year is required.")

        return errors

    # ---------------------------------------------------------
    # REGISTER STUDENT
    # ---------------------------------------------------------
    @staticmethod
    def register_student(username, password, confirm_password, student_data):
        """
        Creates a new student account.

        Returns exactly THREE values:

            success
            user_id
            error_message

        Example:

            (True, 15, None)

        or

            (False, None, "Username already exists.")
        """

        try:

            # -------------------------------------------------
            # BASIC VALIDATION
            # -------------------------------------------------
            validation_errors = AuthService.validate_registration_data(
                username,
                password,
                confirm_password,
                student_data
            )

            if validation_errors:
                return (
                    False,
                    None,
                    " ".join(validation_errors)
                )

            # -------------------------------------------------
            # CHECK USERNAME
            # -------------------------------------------------
            existing_user = User.get_by_username(username)

            if existing_user:
                return (
                    False,
                    None,
                    "Username already exists. Please choose another username."
                )

            # -------------------------------------------------
            # CHECK STUDENT ID / EMAIL
            # -------------------------------------------------
            existing_student = User.find_student_by_student_id_or_email(
                student_data.get("student_id"),
                student_data.get("email")
            )

            if existing_student:

                existing_student_id = existing_student.get("student_id")
                existing_email = existing_student.get("email")

                if (
                    existing_student_id
                    and existing_student_id.lower()
                    == student_data.get("student_id").lower()
                ):
                    return (
                        False,
                        None,
                        "Student ID / USN is already registered."
                    )

                if (
                    existing_email
                    and existing_email.lower()
                    == student_data.get("email").lower()
                ):
                    return (
                        False,
                        None,
                        "Email address is already registered."
                    )

                return (
                    False,
                    None,
                    "Student account already exists."
                )

            # -------------------------------------------------
            # HASH PASSWORD
            # -------------------------------------------------
            hashed_password = AuthService.hash_password(password)

            # -------------------------------------------------
            # CREATE ACCOUNT
            # -------------------------------------------------
            user_id = User.create_student_account(
                username,
                hashed_password,
                student_data
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------
            return (
                True,
                user_id,
                None
            )

        except Exception as error:

            print("Registration Error:", error)

            return (
                False,
                None,
                "Unable to complete registration. Please try again."
            )