from utils.database import get_db_connection


class Student:

    # ============================================================
    # GET ALL STUDENTS
    # ============================================================

    @staticmethod
    def get_all_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    s.id,
                    s.user_id,
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
                    s.registration_status,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.status AS account_status
                FROM students s
                LEFT JOIN users u
                    ON s.user_id = u.id
                ORDER BY s.id DESC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # GET PENDING STUDENTS
    # ============================================================

    @staticmethod
    def get_pending_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    s.id,
                    s.user_id,
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
                    s.registration_status,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.status AS account_status
                FROM students s
                LEFT JOIN users u
                    ON s.user_id = u.id
                WHERE s.registration_status = 'pending'
                ORDER BY s.id DESC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # GET STUDENT BY DATABASE ID
    # ============================================================

    @staticmethod
    def get_by_id(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    s.id,
                    s.user_id,
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
                    s.registration_status,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.status AS account_status
                FROM students s
                LEFT JOIN users u
                    ON s.user_id = u.id
                WHERE s.id = %s
                LIMIT 1
            """, (student_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # GET STUDENT BY STUDENT ID / USN
    # ============================================================

    @staticmethod
    def get_by_student_id(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    s.id,
                    s.user_id,
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
                    s.registration_status,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.status AS account_status
                FROM students s
                LEFT JOIN users u
                    ON s.user_id = u.id
                WHERE s.student_id = %s
                LIMIT 1
            """, (student_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # GET STUDENT BY USER ID
    # ============================================================

    @staticmethod
    def get_by_user_id(user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    s.id,
                    s.user_id,
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
                    s.registration_status,
                    s.created_at,
                    s.updated_at,
                    u.username,
                    u.status AS account_status
                FROM students s
                LEFT JOIN users u
                    ON s.user_id = u.id
                WHERE s.user_id = %s
                LIMIT 1
            """, (user_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # SEARCH BY STUDENT ID
    # ============================================================

    @staticmethod
    def search_by_student_id(student_id):

        return Student.get_by_student_id(student_id)

    # ============================================================
    # UPDATE REGISTRATION STATUS
    # ============================================================

    @staticmethod
    def update_registration_status(student_id, status):

        allowed_statuses = {
            "pending",
            "approved",
            "rejected"
        }

        if status not in allowed_statuses:
            return False

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            connection.start_transaction()

            cursor.execute("""
                SELECT
                    id,
                    user_id
                FROM students
                WHERE id = %s
                LIMIT 1
            """, (student_id,))

            student = cursor.fetchone()

            if not student:
                connection.rollback()
                return False

            cursor.execute("""
                UPDATE students
                SET
                    registration_status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                status,
                student_id
            ))

            if status == "approved":

                cursor.execute("""
                    UPDATE users
                    SET
                        status = 'active',
                        updated_at = NOW()
                    WHERE id = %s
                """, (student["user_id"],))

            elif status == "rejected":

                cursor.execute("""
                    UPDATE users
                    SET
                        status = 'inactive',
                        updated_at = NOW()
                    WHERE id = %s
                """, (student["user_id"],))

            else:

                cursor.execute("""
                    UPDATE users
                    SET
                        status = 'active',
                        updated_at = NOW()
                    WHERE id = %s
                """, (student["user_id"],))

            connection.commit()

            return True

        except Exception:

            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # STUDENT STATISTICS
    # ============================================================

    @staticmethod
    def get_statistics():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_students,
                    SUM(
                        CASE
                            WHEN registration_status = 'pending'
                            THEN 1
                            ELSE 0
                        END
                    ) AS pending_students,
                    SUM(
                        CASE
                            WHEN registration_status = 'approved'
                            THEN 1
                            ELSE 0
                        END
                    ) AS approved_students,
                    SUM(
                        CASE
                            WHEN registration_status = 'rejected'
                            THEN 1
                            ELSE 0
                        END
                    ) AS rejected_students
                FROM students
            """)

            result = cursor.fetchone()

            return {
                "total_students": result["total_students"] or 0,
                "pending_students": result["pending_students"] or 0,
                "approved_students": result["approved_students"] or 0,
                "rejected_students": result["rejected_students"] or 0
            }

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # CHECK WHETHER EMAIL BELONGS TO ANOTHER STUDENT
    # ============================================================

    @staticmethod
    def email_exists_for_other_student(email, user_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id
                FROM students
                WHERE email = %s
                  AND user_id <> %s
                LIMIT 1
            """, (
                email,
                user_id
            ))

            result = cursor.fetchone()

            return result is not None

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # UPDATE STUDENT PROFILE
    # ============================================================

    @staticmethod
    def update_profile(user_id, profile_data):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                UPDATE students
                SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    phone = %s,
                    gender = %s,
                    date_of_birth = %s,
                    parent_name = %s,
                    parent_phone = %s,
                    address = %s,
                    updated_at = NOW()
                WHERE user_id = %s
            """, (
                profile_data.get("first_name"),
                profile_data.get("last_name"),
                profile_data.get("email"),
                profile_data.get("phone"),
                profile_data.get("gender"),
                profile_data.get("date_of_birth"),
                profile_data.get("parent_name"),
                profile_data.get("parent_phone"),
                profile_data.get("address"),
                user_id
            ))

            connection.commit()

            return cursor.rowcount > 0

        except Exception:

            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # UPDATE PROFILE PHOTO
    # ============================================================

    @staticmethod
    def update_profile_photo(
        user_id,
        profile_photo
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                UPDATE students
                SET
                    profile_photo = %s,
                    updated_at = NOW()
                WHERE user_id = %s
            """, (
                profile_photo,
                user_id
            ))

            connection.commit()

            return cursor.rowcount > 0

        except Exception:

            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # DELETE PROFILE PHOTO
    # ============================================================

    @staticmethod
    def delete_profile_photo(user_id):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                UPDATE students
                SET
                    profile_photo = NULL,
                    updated_at = NOW()
                WHERE user_id = %s
            """, (user_id,))

            connection.commit()

            return cursor.rowcount > 0

        except Exception:

            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()