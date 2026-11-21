from utils.database import get_db_connection


class Complaint:

    # ============================================================
    # COMPLAINT CATEGORIES
    # ============================================================

    CATEGORIES = [
        "Electrical",
        "Water & Plumbing",
        "Room Maintenance",
        "Cleaning",
        "Mess & Food",
        "Internet & Wi-Fi",
        "Furniture",
        "Security",
        "Hostel Facilities",
        "Other"
    ]


    # ============================================================
    # CREATE COMPLAINT
    # ============================================================

    @staticmethod
    def create_complaint(
        student_id,
        category,
        subject,
        description,
        priority="medium",
        ai_generated=0
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO complaints (
                    student_id,
                    category,
                    subject,
                    description,
                    priority,
                    status,
                    ai_generated,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'open',
                    %s,
                    NOW(),
                    NOW()
                )
            """, (
                student_id,
                category,
                subject,
                description,
                priority,
                ai_generated
            ))

            complaint_id = cursor.lastrowid

            connection.commit()

            return complaint_id

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADD COMPLAINT MESSAGE
    # ============================================================

    @staticmethod
    def add_message(
        complaint_id,
        sender_type,
        message
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO complaint_messages (
                    complaint_id,
                    sender_type,
                    message,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    NOW()
                )
            """, (
                complaint_id,
                sender_type,
                message
            ))

            connection.commit()

            return cursor.lastrowid

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET STUDENT COMPLAINTS
    # ============================================================

    @staticmethod
    def get_student_complaints(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    student_id,
                    category,
                    subject,
                    description,
                    priority,
                    status,
                    ai_generated,
                    created_at,
                    updated_at,
                    resolved_at
                FROM complaints
                WHERE student_id = %s
                ORDER BY
                    created_at DESC,
                    id DESC
            """, (
                student_id,
            ))

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET SINGLE COMPLAINT
    # ============================================================

    @staticmethod
    def get_by_id(complaint_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    c.id,
                    c.student_id,
                    c.category,
                    c.subject,
                    c.description,
                    c.priority,
                    c.status,
                    c.ai_generated,
                    c.created_at,
                    c.updated_at,
                    c.resolved_at,

                    s.student_id AS usn,
                    s.first_name,
                    s.last_name,
                    s.email

                FROM complaints c

                INNER JOIN students s
                    ON c.student_id = s.id

                WHERE c.id = %s

                LIMIT 1
            """, (
                complaint_id,
            ))

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET COMPLAINT MESSAGES
    # ============================================================

    @staticmethod
    def get_messages(complaint_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    complaint_id,
                    sender_type,
                    message,
                    created_at
                FROM complaint_messages
                WHERE complaint_id = %s
                ORDER BY
                    created_at ASC,
                    id ASC
            """, (
                complaint_id,
            ))

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # STUDENT COMPLAINT STATISTICS
    # ============================================================

    @staticmethod
    def get_student_statistics(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT

                    COUNT(*) AS total,

                    SUM(
                        CASE
                            WHEN status = 'open'
                            THEN 1
                            ELSE 0
                        END
                    ) AS open_count,

                    SUM(
                        CASE
                            WHEN status = 'in_progress'
                            THEN 1
                            ELSE 0
                        END
                    ) AS in_progress_count,

                    SUM(
                        CASE
                            WHEN status = 'resolved'
                            THEN 1
                            ELSE 0
                        END
                    ) AS resolved_count

                FROM complaints

                WHERE student_id = %s
            """, (
                student_id,
            ))

            row = cursor.fetchone()

            return {
                "total": int(
                    row["total"] or 0
                ),
                "open": int(
                    row["open_count"] or 0
                ),
                "in_progress": int(
                    row["in_progress_count"] or 0
                ),
                "resolved": int(
                    row["resolved_count"] or 0
                )
            }

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # SAVE AI CONVERSATION MESSAGE
    # ============================================================

    @staticmethod
    def save_ai_message(
        student_id,
        session_id,
        sender,
        message
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO ai_conversations (
                    student_id,
                    session_id,
                    sender,
                    message,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    NOW()
                )
            """, (
                student_id,
                session_id,
                sender,
                message
            ))

            connection.commit()

            return cursor.lastrowid

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET AI CONVERSATION
    # ============================================================

    @staticmethod
    def get_ai_conversation(
        student_id,
        session_id
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    student_id,
                    session_id,
                    sender,
                    message,
                    created_at
                FROM ai_conversations
                WHERE student_id = %s
                AND session_id = %s
                ORDER BY
                    created_at ASC,
                    id ASC
            """, (
                student_id,
                session_id
            ))

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADMIN - ALL COMPLAINTS
    # ============================================================

    @staticmethod
    def get_all_complaints():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT

                    c.id,
                    c.student_id,
                    c.category,
                    c.subject,
                    c.description,
                    c.priority,
                    c.status,
                    c.ai_generated,
                    c.created_at,
                    c.updated_at,
                    c.resolved_at,

                    s.student_id AS usn,

                    CONCAT(
                        s.first_name,
                        ' ',
                        COALESCE(
                            s.last_name,
                            ''
                        )
                    ) AS student_name,

                    s.batch,
                    s.department,
                    s.phone

                FROM complaints c

                INNER JOIN students s
                    ON c.student_id = s.id

                ORDER BY

                    CASE c.priority

                        WHEN 'urgent'
                        THEN 1

                        WHEN 'high'
                        THEN 2

                        WHEN 'medium'
                        THEN 3

                        WHEN 'low'
                        THEN 4

                        ELSE 5

                    END,

                    c.created_at DESC

            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADMIN - UPDATE COMPLAINT STATUS
    # ============================================================

    @staticmethod
    def update_status(
        complaint_id,
        status
    ):

        allowed_statuses = [
            "open",
            "in_progress",
            "resolved",
            "closed"
        ]

        if status not in allowed_statuses:

            return {
                "success": False,
                "message": "Invalid complaint status."
            }


        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            if status == "resolved":

                cursor.execute("""
                    UPDATE complaints

                    SET
                        status = %s,
                        updated_at = NOW(),
                        resolved_at = NOW()

                    WHERE id = %s
                """, (
                    status,
                    complaint_id
                ))

            else:

                cursor.execute("""
                    UPDATE complaints

                    SET
                        status = %s,
                        updated_at = NOW()

                    WHERE id = %s
                """, (
                    status,
                    complaint_id
                ))

            if cursor.rowcount == 0:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Complaint not found."
                }

            connection.commit()

            return {
                "success": True,
                "message": (
                    "Complaint status updated successfully."
                )
            }

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADMIN - UPDATE PRIORITY
    # ============================================================

    @staticmethod
    def update_priority(
        complaint_id,
        priority
    ):

        allowed_priorities = [
            "low",
            "medium",
            "high",
            "urgent"
        ]

        if priority not in allowed_priorities:

            return {
                "success": False,
                "message": "Invalid complaint priority."
            }


        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                UPDATE complaints

                SET
                    priority = %s,
                    updated_at = NOW()

                WHERE id = %s
            """, (
                priority,
                complaint_id
            ))

            if cursor.rowcount == 0:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Complaint not found."
                }

            connection.commit()

            return {
                "success": True,
                "message": (
                    "Complaint priority updated successfully."
                )
            }

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADMIN - ADD RESPONSE
    # ============================================================

    @staticmethod
    def add_admin_response(
        complaint_id,
        message
    ):

        if not message:

            return {
                "success": False,
                "message": "Response cannot be empty."
            }


        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO complaint_messages (
                    complaint_id,
                    sender_type,
                    message,
                    created_at
                )
                VALUES (
                    %s,
                    'admin',
                    %s,
                    NOW()
                )
            """, (
                complaint_id,
                message
            ))

            message_id = cursor.lastrowid

            cursor.execute("""
                UPDATE complaints

                SET
                    updated_at = NOW()

                WHERE id = %s
            """, (
                complaint_id
            ))

            connection.commit()

            return {
                "success": True,
                "message_id": message_id,
                "message": (
                    "Admin response added successfully."
                )
            }

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ADMIN DASHBOARD STATISTICS
    # ============================================================

    @staticmethod
    def get_admin_statistics():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT

                    COUNT(*) AS total,

                    SUM(
                        CASE
                            WHEN status = 'open'
                            THEN 1
                            ELSE 0
                        END
                    ) AS open_count,

                    SUM(
                        CASE
                            WHEN status = 'in_progress'
                            THEN 1
                            ELSE 0
                        END
                    ) AS in_progress_count,

                    SUM(
                        CASE
                            WHEN status = 'resolved'
                            THEN 1
                            ELSE 0
                        END
                    ) AS resolved_count,

                    SUM(
                        CASE
                            WHEN priority = 'urgent'
                            THEN 1
                            ELSE 0
                        END
                    ) AS urgent_count,

                    SUM(
                        CASE
                            WHEN priority = 'high'
                            THEN 1
                            ELSE 0
                        END
                    ) AS high_count

                FROM complaints
            """)

            row = cursor.fetchone()

            return {
                "total": int(
                    row["total"] or 0
                ),
                "open": int(
                    row["open_count"] or 0
                ),
                "in_progress": int(
                    row["in_progress_count"] or 0
                ),
                "resolved": int(
                    row["resolved_count"] or 0
                ),
                "urgent": int(
                    row["urgent_count"] or 0
                ),
                "high": int(
                    row["high_count"] or 0
                )
            }

        finally:

            cursor.close()
            connection.close()