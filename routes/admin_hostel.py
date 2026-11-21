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

from utils.database import get_db_connection


admin_hostel_bp = Blueprint(
    "admin_hostel",
    __name__,
    url_prefix="/admin/hostel"
)


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("auth.login_user"))

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

def validate_csrf():
    token = request.form.get("csrf_token", "")

    session_token = session.get(
        "csrf_token",
        ""
    )

    return (
        token
        and session_token
        and token == session_token
    )


# ============================================================
# HOSTEL MANAGEMENT PAGE
# ============================================================

@admin_hostel_bp.route("/")
@admin_required
def hostel_management():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Blocks
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                hb.id,
                hb.block_name,
                hb.description,
                hb.status,
                hb.created_at,
                hb.updated_at,
                COUNT(r.id) AS total_rooms
            FROM hostel_blocks hb
            LEFT JOIN rooms r
                ON hb.id = r.block_id
            GROUP BY
                hb.id,
                hb.block_name,
                hb.description,
                hb.status,
                hb.created_at,
                hb.updated_at
            ORDER BY hb.id ASC
        """)

        blocks = cursor.fetchall()


        # ----------------------------------------------------
        # Rooms
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                r.id,
                r.block_id,
                r.room_number,
                r.floor,
                r.capacity,
                r.room_type,
                r.status,
                r.created_at,
                r.updated_at,
                hb.block_name
            FROM rooms r
            INNER JOIN hostel_blocks hb
                ON r.block_id = hb.id
            ORDER BY
                hb.id ASC,
                r.floor ASC,
                r.room_number ASC
        """)

        rooms = cursor.fetchall()


        # ----------------------------------------------------
        # Occupied Beds
        #
        # room_allocations is used to calculate active
        # student allocations.
        # ----------------------------------------------------

        for room in rooms:

            cursor.execute("""
                SELECT COUNT(*) AS occupied_beds
                FROM room_allocations
                WHERE room_id = %s
                  AND status = 'active'
            """, (room["id"],))

            result = cursor.fetchone()

            occupied_beds = (
                result["occupied_beds"]
                if result
                else 0
            )

            capacity = int(
                room["capacity"] or 0
            )

            room["occupied_beds"] = occupied_beds

            room["available_beds"] = max(
                capacity - occupied_beds,
                0
            )


        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        total_blocks = len(blocks)
        total_rooms = len(rooms)

        total_capacity = sum(
            int(room["capacity"] or 0)
            for room in rooms
        )

        occupied_beds = sum(
            int(room["occupied_beds"] or 0)
            for room in rooms
        )

        available_beds = max(
            total_capacity - occupied_beds,
            0
        )

        statistics = {
            "total_blocks": total_blocks,
            "total_rooms": total_rooms,
            "total_capacity": total_capacity,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds
        }


        # Make sure CSRF exists.
        import secrets

        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)

        csrf_token = session["csrf_token"]


        return render_template(
            "admin/hostel.html",
            blocks=blocks,
            rooms=rooms,
            statistics=statistics,
            csrf_token=csrf_token
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# ADD BLOCK
# ============================================================

@admin_hostel_bp.route(
    "/blocks/add",
    methods=["POST"]
)
@admin_required
def add_block():

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    block_name = request.form.get(
        "block_name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()


    if not block_name:

        return jsonify({
            "success": False,
            "message": "Block name is required."
        }), 400


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT id
            FROM hostel_blocks
            WHERE block_name = %s
            LIMIT 1
        """, (block_name,))

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "success": False,
                "message": "A hostel block with this name already exists."
            }), 409


        cursor.execute("""
            INSERT INTO hostel_blocks (
                block_name,
                description,
                status,
                created_at,
                updated_at
            )
            VALUES (
                %s,
                %s,
                'active',
                NOW(),
                NOW()
            )
        """, (
            block_name,
            description
        ))

        connection.commit()


        return jsonify({
            "success": True,
            "message": "Hostel block added successfully.",
            "block_id": cursor.lastrowid
        })


    except Exception:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to add hostel block."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET BLOCK
# ============================================================

@admin_hostel_bp.route(
    "/blocks/<int:block_id>",
    methods=["GET"]
)
@admin_required
def get_block(block_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                id,
                block_name,
                description,
                status,
                created_at,
                updated_at
            FROM hostel_blocks
            WHERE id = %s
            LIMIT 1
        """, (block_id,))

        block = cursor.fetchone()


        if not block:

            return jsonify({
                "success": False,
                "message": "Hostel block not found."
            }), 404


        return jsonify({
            "success": True,
            "block": block
        })


    finally:

        cursor.close()
        connection.close()


# ============================================================
# UPDATE BLOCK
# ============================================================

@admin_hostel_bp.route(
    "/blocks/<int:block_id>/update",
    methods=["POST"]
)
@admin_required
def update_block(block_id):

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    block_name = request.form.get(
        "block_name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    status = request.form.get(
        "status",
        "active"
    ).strip().lower()


    if not block_name:

        return jsonify({
            "success": False,
            "message": "Block name is required."
        }), 400


    if status not in [
        "active",
        "inactive"
    ]:

        status = "active"


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT id
            FROM hostel_blocks
            WHERE block_name = %s
              AND id != %s
            LIMIT 1
        """, (
            block_name,
            block_id
        ))

        existing = cursor.fetchone()

        if existing:

            return jsonify({
                "success": False,
                "message": "Another block already uses this name."
            }), 409


        cursor.execute("""
            UPDATE hostel_blocks
            SET
                block_name = %s,
                description = %s,
                status = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            block_name,
            description,
            status,
            block_id
        ))


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Hostel block not found."
            }), 404


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Hostel block updated successfully."
        })


    except Exception:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to update hostel block."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DELETE BLOCK
# ============================================================

@admin_hostel_bp.route(
    "/blocks/<int:block_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_block(block_id):

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # A block cannot be deleted if rooms exist.
        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE block_id = %s
        """, (block_id,))

        result = cursor.fetchone()

        room_count = result[0] if result else 0


        if room_count > 0:

            return jsonify({
                "success": False,
                "message": (
                    "This block cannot be deleted because "
                    "it contains rooms. Delete or move the rooms first."
                )
            }), 409


        cursor.execute("""
            DELETE FROM hostel_blocks
            WHERE id = %s
        """, (block_id,))


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Hostel block not found."
            }), 404


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Hostel block deleted successfully."
        })


    except Exception:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to delete hostel block."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# ADD ROOM
# ============================================================

@admin_hostel_bp.route(
    "/rooms/add",
    methods=["POST"]
)
@admin_required
def add_room():

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    block_id = request.form.get(
        "block_id",
        ""
    ).strip()

    room_number = request.form.get(
        "room_number",
        ""
    ).strip()

    floor = request.form.get(
        "floor",
        ""
    ).strip()

    capacity = request.form.get(
        "capacity",
        ""
    ).strip()

    # Room type is required by MySQL schema.
    # The current UI doesn't ask for it, so use
    # Standard as the default.
    room_type = request.form.get(
        "room_type",
        "Standard"
    ).strip()

    status = request.form.get(
        "status",
        "active"
    ).strip().lower()


    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not block_id:

        return jsonify({
            "success": False,
            "message": "Please select a hostel block."
        }), 400


    if not room_number:

        return jsonify({
            "success": False,
            "message": "Room number is required."
        }), 400


    try:

        block_id = int(block_id)
        floor = int(floor)
        capacity = int(capacity)

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Floor, capacity and block must be valid numbers."
        }), 400


    if floor < 0:

        return jsonify({
            "success": False,
            "message": "Floor cannot be negative."
        }), 400


    if capacity < 1 or capacity > 20:

        return jsonify({
            "success": False,
            "message": "Bed capacity must be between 1 and 20."
        }), 400


    if not room_type:

        room_type = "Standard"


    if status not in [
        "active",
        "inactive",
        "available",
        "occupied"
    ]:

        status = "active"


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Verify block
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id, status
            FROM hostel_blocks
            WHERE id = %s
            LIMIT 1
        """, (block_id,))

        block = cursor.fetchone()


        if not block:

            return jsonify({
                "success": False,
                "message": "Selected hostel block does not exist."
            }), 404


        if block[1] != "active":

            return jsonify({
                "success": False,
                "message": "Cannot add a room to an inactive block."
            }), 400


        # ----------------------------------------------------
        # Check duplicate room number within same block
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM rooms
            WHERE block_id = %s
              AND room_number = %s
            LIMIT 1
        """, (
            block_id,
            room_number
        ))

        existing = cursor.fetchone()


        if existing:

            return jsonify({
                "success": False,
                "message": (
                    "This room number already exists in the selected block."
                )
            }), 409


        # ----------------------------------------------------
        # Insert room
        # ----------------------------------------------------

        cursor.execute("""
            INSERT INTO rooms (
                block_id,
                room_number,
                floor,
                capacity,
                room_type,
                status,
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
                NOW(),
                NOW()
            )
        """, (
            block_id,
            room_number,
            floor,
            capacity,
            room_type,
            status
        ))


        room_id = cursor.lastrowid

        connection.commit()


        return jsonify({
            "success": True,
            "message": "Room added successfully.",
            "room_id": room_id
        })


    except Exception as error:

        connection.rollback()

        print(
            "ADD ROOM ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to add room."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET ROOM
# ============================================================

@admin_hostel_bp.route(
    "/rooms/<int:room_id>",
    methods=["GET"]
)
@admin_required
def get_room(room_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute("""
            SELECT
                r.id,
                r.block_id,
                r.room_number,
                r.floor,
                r.capacity,
                r.room_type,
                r.status,
                r.created_at,
                r.updated_at,
                hb.block_name
            FROM rooms r
            INNER JOIN hostel_blocks hb
                ON r.block_id = hb.id
            WHERE r.id = %s
            LIMIT 1
        """, (room_id,))

        room = cursor.fetchone()


        if not room:

            return jsonify({
                "success": False,
                "message": "Room not found."
            }), 404


        return jsonify({
            "success": True,
            "room": room
        })


    finally:

        cursor.close()
        connection.close()


# ============================================================
# UPDATE ROOM
# ============================================================

@admin_hostel_bp.route(
    "/rooms/<int:room_id>/update",
    methods=["POST"]
)
@admin_required
def update_room(room_id):

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    block_id = request.form.get(
        "block_id",
        ""
    ).strip()

    room_number = request.form.get(
        "room_number",
        ""
    ).strip()

    floor = request.form.get(
        "floor",
        ""
    ).strip()

    capacity = request.form.get(
        "capacity",
        ""
    ).strip()

    room_type = request.form.get(
        "room_type",
        "Standard"
    ).strip()

    status = request.form.get(
        "status",
        "active"
    ).strip().lower()


    if not block_id or not room_number:

        return jsonify({
            "success": False,
            "message": "Block and room number are required."
        }), 400


    try:

        block_id = int(block_id)
        floor = int(floor)
        capacity = int(capacity)

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Invalid room information."
        }), 400


    if capacity < 1 or capacity > 20:

        return jsonify({
            "success": False,
            "message": "Bed capacity must be between 1 and 20."
        }), 400


    if not room_type:

        room_type = "Standard"


    if status not in [
        "active",
        "inactive",
        "available",
        "occupied"
    ]:

        status = "active"


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # ----------------------------------------------------
        # Check duplicate
        # ----------------------------------------------------

        cursor.execute("""
            SELECT id
            FROM rooms
            WHERE block_id = %s
              AND room_number = %s
              AND id != %s
            LIMIT 1
        """, (
            block_id,
            room_number,
            room_id
        ))

        existing = cursor.fetchone()


        if existing:

            return jsonify({
                "success": False,
                "message": (
                    "Another room with this number "
                    "already exists in the selected block."
                )
            }), 409


        # ----------------------------------------------------
        # Check current occupied count
        # ----------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM room_allocations
            WHERE room_id = %s
              AND status = 'active'
        """, (room_id,))

        result = cursor.fetchone()

        occupied = result[0] if result else 0


        if capacity < occupied:

            return jsonify({
                "success": False,
                "message": (
                    f"Capacity cannot be reduced below "
                    f"the current occupancy of {occupied}."
                )
            }), 400


        cursor.execute("""
            UPDATE rooms
            SET
                block_id = %s,
                room_number = %s,
                floor = %s,
                capacity = %s,
                room_type = %s,
                status = %s,
                updated_at = NOW()
            WHERE id = %s
        """, (
            block_id,
            room_number,
            floor,
            capacity,
            room_type,
            status,
            room_id
        ))


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Room not found."
            }), 404


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Room updated successfully."
        })


    except Exception as error:

        connection.rollback()

        print(
            "UPDATE ROOM ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to update room."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DELETE ROOM
# ============================================================

@admin_hostel_bp.route(
    "/rooms/<int:room_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_room(room_id):

    if not validate_csrf():
        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403


    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM room_allocations
            WHERE room_id = %s
              AND status = 'active'
        """, (room_id,))

        result = cursor.fetchone()

        active_allocations = (
            result[0]
            if result
            else 0
        )


        if active_allocations > 0:

            return jsonify({
                "success": False,
                "message": (
                    "This room cannot be deleted because "
                    "students are currently allocated to it."
                )
            }), 409


        cursor.execute("""
            DELETE FROM rooms
            WHERE id = %s
        """, (room_id,))


        if cursor.rowcount == 0:

            return jsonify({
                "success": False,
                "message": "Room not found."
            }), 404


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Room deleted successfully."
        })


    except Exception as error:

        connection.rollback()

        print(
            "DELETE ROOM ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Unable to delete room."
        }), 500

    finally:

        cursor.close()
        connection.close()


# ============================================================
# ROOM STUDENTS
# ============================================================

@admin_hostel_bp.route(
    "/rooms/<int:room_id>/students",
    methods=["GET"]
)
@admin_required
def room_students(room_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Room information
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                r.id,
                r.room_number,
                r.floor,
                r.capacity,
                r.room_type,
                r.status,
                hb.block_name
            FROM rooms r
            INNER JOIN hostel_blocks hb
                ON r.block_id = hb.id
            WHERE r.id = %s
            LIMIT 1
        """, (room_id,))

        room = cursor.fetchone()


        if not room:

            return jsonify({
                "success": False,
                "message": "Room not found."
            }), 404


        # ----------------------------------------------------
        # Students
        # ----------------------------------------------------

        cursor.execute("""
            SELECT
                s.id,
                s.student_id,
                s.first_name,
                s.last_name,
                s.profile_photo,
                s.batch,
                s.department,
                ra.bed_number
            FROM room_allocations ra
            INNER JOIN students s
                ON ra.student_id = s.id
            WHERE ra.room_id = %s
              AND ra.status = 'active'
            ORDER BY
                ra.bed_number ASC,
                s.first_name ASC
        """, (room_id,))

        students = cursor.fetchall()


        # Frontend currently expects `usn`.
        for student in students:
            student["usn"] = student.get(
                "student_id"
            )


        return jsonify({
            "success": True,
            "room": room,
            "students": students
        })


    finally:

        cursor.close()
        connection.close()


# ============================================================
# STATISTICS API
# ============================================================

@admin_hostel_bp.route(
    "/statistics",
    methods=["GET"]
)
@admin_required
def statistics():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM hostel_blocks
        """)

        total_blocks = cursor.fetchone()[0]


        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(capacity), 0)
            FROM rooms
        """)

        room_result = cursor.fetchone()

        total_rooms = room_result[0]
        total_capacity = room_result[1]


        cursor.execute("""
            SELECT COUNT(*)
            FROM room_allocations
            WHERE status = 'active'
        """)

        occupied_beds = cursor.fetchone()[0]


        available_beds = max(
            total_capacity - occupied_beds,
            0
        )


        return jsonify({
            "success": True,
            "statistics": {
                "total_blocks": total_blocks,
                "total_rooms": total_rooms,
                "total_capacity": total_capacity,
                "occupied_beds": occupied_beds,
                "available_beds": available_beds
            }
        })


    finally:

        cursor.close()
        connection.close()