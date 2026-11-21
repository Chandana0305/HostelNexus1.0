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

from utils.database import get_db_connection


admin_complaints_bp = Blueprint(
    "admin_complaints",
    __name__,
    url_prefix="/admin/complaints"
)


# ============================================================
# ADMIN AUTHENTICATION
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
# DATABASE HELPERS
# ============================================================

def get_all_complaints():

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

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
                s.email,
                s.phone,
                s.department,
                s.batch,
                s.year,

                CONCAT(
                    COALESCE(s.first_name, ''),
                    ' ',
                    COALESCE(s.last_name, '')
                ) AS student_name

            FROM complaints c

            INNER JOIN students s
                ON c.student_id = s.id

            ORDER BY
                CASE
                    WHEN c.priority = 'urgent'
                    THEN 1
                    WHEN c.priority = 'high'
                    THEN 2
                    WHEN c.priority = 'medium'
                    THEN 3
                    ELSE 4
                END,
                c.created_at DESC
        """)

        return cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


def get_complaint(
    complaint_id
):

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

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
                s.email,
                s.phone,
                s.department,
                s.batch,
                s.year,

                CONCAT(
                    COALESCE(s.first_name, ''),
                    ' ',
                    COALESCE(s.last_name, '')
                ) AS student_name

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


def get_messages(
    complaint_id
):

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

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


def get_statistics():

    connection = get_db_connection()
    cursor = connection.cursor(
        dictionary=True
    )

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
                        WHEN status = 'closed'
                        THEN 1
                        ELSE 0
                    END
                ) AS closed_count,

                SUM(
                    CASE
                        WHEN priority = 'urgent'
                        THEN 1
                        ELSE 0
                    END
                ) AS urgent_count

            FROM complaints
        """)

        row = cursor.fetchone()

        if not row:
            return {
                "total": 0,
                "open": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0,
                "urgent": 0
            }

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
            "closed": int(
                row["closed_count"] or 0
            ),
            "urgent": int(
                row["urgent_count"] or 0
            )
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# ADMIN COMPLAINT DASHBOARD
# ============================================================

@admin_complaints_bp.route(
    "/",
    methods=["GET"]
)
@admin_required
def complaint_dashboard():

    csrf_token = ensure_csrf_token()

    complaints = get_all_complaints()

    statistics = get_statistics()

    return render_template(
        "admin/complaints.html",
        complaints=complaints,
        statistics=statistics,
        csrf_token=csrf_token
    )


# ============================================================
# COMPLAINT LIST API
# ============================================================

@admin_complaints_bp.route(
    "/list",
    methods=["GET"]
)
@admin_required
def complaint_list():

    complaints = get_all_complaints()

    return jsonify({
        "success": True,
        "complaints": complaints,
        "statistics": get_statistics()
    })


# ============================================================
# COMPLAINT DETAILS
# ============================================================

@admin_complaints_bp.route(
    "/<int:complaint_id>",
    methods=["GET"]
)
@admin_required
def complaint_details(
    complaint_id
):

    complaint = get_complaint(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    messages = get_messages(
        complaint_id
    )

    return jsonify({
        "success": True,
        "complaint": complaint,
        "messages": messages
    })


# ============================================================
# UPDATE STATUS
# ============================================================

@admin_complaints_bp.route(
    "/<int:complaint_id>/status",
    methods=["POST"]
)
@admin_required
def update_status(
    complaint_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    status = request.form.get(
        "status",
        ""
    ).strip().lower()

    allowed_statuses = {
        "open",
        "in_progress",
        "resolved",
        "closed"
    }

    if status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Invalid complaint status."
        }), 400

    complaint = get_complaint(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        if status in {
            "resolved",
            "closed"
        }:

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
                    updated_at = NOW(),
                    resolved_at = NULL

                WHERE id = %s
            """, (
                status,
                complaint_id
            ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Complaint status updated successfully.",
            "status": status
        })

    except Exception as error:

        connection.rollback()

        print(
            "Complaint status update error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update complaint status."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# UPDATE PRIORITY
# ============================================================

@admin_complaints_bp.route(
    "/<int:complaint_id>/priority",
    methods=["POST"]
)
@admin_required
def update_priority(
    complaint_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    priority = request.form.get(
        "priority",
        ""
    ).strip().lower()

    allowed_priorities = {
        "low",
        "medium",
        "high",
        "urgent"
    }

    if priority not in allowed_priorities:

        return jsonify({
            "success": False,
            "message": "Invalid complaint priority."
        }), 400

    complaint = get_complaint(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

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

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Complaint priority updated successfully.",
            "priority": priority
        })

    except Exception as error:

        connection.rollback()

        print(
            "Complaint priority update error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update complaint priority."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# ADMIN REPLY
# ============================================================

@admin_complaints_bp.route(
    "/<int:complaint_id>/reply",
    methods=["POST"]
)
@admin_required
def admin_reply(
    complaint_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    message = request.form.get(
        "message",
        ""
    ).strip()

    if not message:

        return jsonify({
            "success": False,
            "message": "Please enter a response."
        }), 400

    if len(message) > 5000:

        return jsonify({
            "success": False,
            "message": "Response cannot exceed 5000 characters."
        }), 400

    complaint = get_complaint(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # INSERT ADMIN MESSAGE
        # ----------------------------------------------------

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
            "admin",
            message
        ))

        # ----------------------------------------------------
        # UPDATE COMPLAINT TIMESTAMP
        # ----------------------------------------------------

        cursor.execute("""
            UPDATE complaints

            SET
                updated_at = NOW()

            WHERE id = %s
        """, (
            complaint_id,
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Response sent successfully."
        })

    except Exception as error:

        connection.rollback()

        print(
            "ADMIN REPLY ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to send response."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# RESOLVE COMPLAINT
# ============================================================

@admin_complaints_bp.route(
    "/<int:complaint_id>/resolve",
    methods=["POST"]
)
@admin_required
def resolve_complaint(
    complaint_id
):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    complaint = get_complaint(
        complaint_id
    )

    if not complaint:

        return jsonify({
            "success": False,
            "message": "Complaint not found."
        }), 404

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE complaints

            SET
                status = 'resolved',
                resolved_at = NOW(),
                updated_at = NOW()

            WHERE id = %s
        """, (
            complaint_id,
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Complaint resolved successfully."
        })

    except Exception as error:

        connection.rollback()

        print(
            "Complaint resolve error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to resolve complaint."
        }), 500

    finally:

        cursor.close()
        connection.close()