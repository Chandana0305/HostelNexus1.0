from utils.database import get_db_connection


class User:

    @staticmethod
    def update_credentials(user_id, username, hashed_password=None):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            if hashed_password:
                cursor.execute("""
                    UPDATE users
                    SET username = %s,
                        password = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (username, hashed_password, user_id))
            else:
                cursor.execute("""
                    UPDATE users
                    SET username = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (username, user_id))

            connection.commit()
            return cursor.rowcount > 0

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    # =====================================================
    # GET USER BY USERNAME
    # =====================================================

    @staticmethod
    def get_by_username(username):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id,
                    username,
                    password,
                    role,
                    status,
                    created_at,
                    updated_at
                FROM users
                WHERE username = %s
                LIMIT 1
            """, (username,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # =====================================================
    # GET USER BY ID
    # =====================================================

    @staticmethod
    def get_by_id(user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id,
                    username,
                    password,
                    role,
                    status,
                    created_at,
                    updated_at
                FROM users
                WHERE id = %s
                LIMIT 1
            """, (user_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # =====================================================
    # GET STUDENT BY USER ID
    # =====================================================

    @staticmethod
    def get_student_by_user_id(user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id,
                    user_id,
                    student_id,
                    first_name,
                    last_name,
                    profile_photo,
                    email,
                    phone,
                    gender,
                    date_of_birth,
                    course,
                    department,
                    batch,
                    year,
                    parent_name,
                    parent_phone,
                    address,
                    registration_status,
                    created_at,
                    updated_at
                FROM students
                WHERE user_id = %s
                LIMIT 1
            """, (user_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # =====================================================
    # GET USER + STUDENT INFORMATION
    # =====================================================

    @staticmethod
    def get_user_with_student(username):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    u.id AS user_id,
                    u.username,
                    u.password,
                    u.role,
                    u.status,
                    u.created_at AS user_created_at,
                    u.updated_at AS user_updated_at,

                    s.id AS student_record_id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.profile_photo,
                    s.email,
                    s.phone,
                    s.gender,
                    s.date_of_birth,
                    s.course,
                    s.department,
                    s.batch,
                    s.year,
                    s.parent_name,
                    s.parent_phone,
                    s.address,
                    s.registration_status

                FROM users u

                LEFT JOIN students s
                    ON u.id = s.user_id

                WHERE u.username = %s

                LIMIT 1
            """, (username,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # =====================================================
    # CHECK STUDENT ID / EMAIL
    # =====================================================

    @staticmethod
    def find_student_by_student_id_or_email(
        student_id,
        email
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    student_id,
                    email
                FROM students
                WHERE student_id = %s
                   OR email = %s
                LIMIT 1
            """, (
                student_id,
                email
            ))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # =====================================================
    # CREATE STUDENT ACCOUNT
    # =====================================================

    @staticmethod
    def create_student_account(
        username,
        hashed_password,
        student_data
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            connection.start_transaction()

            # -------------------------------------------------
            # CREATE USER ACCOUNT
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO users (
                    username,
                    password,
                    role,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    NOW()
                )
            """, (
                username,
                hashed_password,
                "student",
                "active"
            ))

            user_id = cursor.lastrowid


            # -------------------------------------------------
            # CREATE STUDENT PROFILE
            # -------------------------------------------------

            cursor.execute("""
                INSERT INTO students (
                    user_id,
                    student_id,
                    first_name,
                    last_name,
                    profile_photo,
                    email,
                    phone,
                    gender,
                    date_of_birth,
                    course,
                    department,
                    batch,
                    year,
                    parent_name,
                    parent_phone,
                    address,
                    registration_status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW(),
                    NOW()
                )
            """, (
                user_id,
                student_data.get("student_id"),
                student_data.get("first_name"),
                student_data.get("last_name"),
                student_data.get("profile_photo"),
                student_data.get("email"),
                student_data.get("phone"),
                student_data.get("gender"),
                student_data.get("date_of_birth"),
                student_data.get("course"),
                student_data.get("department"),
                student_data.get("batch"),
                student_data.get("year"),
                student_data.get("parent_name"),
                student_data.get("parent_phone"),
                student_data.get("address"),
                "pending"
            ))


            # -------------------------------------------------
            # COMMIT
            # -------------------------------------------------

            connection.commit()

            return user_id


        except Exception:

            connection.rollback()

            raise


        finally:

            cursor.close()
            connection.close()