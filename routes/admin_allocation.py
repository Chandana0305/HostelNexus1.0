from functools import wraps
from datetime import date
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

from models.room_allocation import RoomAllocation
from utils.database import get_db_connection


admin_allocation_bp = Blueprint(
    "admin_allocation",
    __name__,
    url_prefix="/admin/allocation"
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
# CSRF TOKEN
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
# ALLOCATION DASHBOARD
# ============================================================

@admin_allocation_bp.route("/")
@admin_required
def allocation_dashboard():

    csrf_token = ensure_csrf_token()

    statistics = RoomAllocation.get_statistics()

    students = RoomAllocation.get_available_students()

    blocks = RoomAllocation.get_blocks()

    rooms = RoomAllocation.get_rooms()

    allocations = RoomAllocation.get_active_allocations()

    return render_template(
        "admin/allocation.html",
        statistics=statistics,
        students=students,
        blocks=blocks,
        rooms=rooms,
        allocations=allocations,
        csrf_token=csrf_token
    )


# ============================================================
# GET AVAILABLE STUDENTS
# ============================================================

@admin_allocation_bp.route(
    "/students",
    methods=["GET"]
)
@admin_required
def available_students():

    students = RoomAllocation.get_available_students()

    return jsonify({
        "success": True,
        "students": students
    })


# ============================================================
# GET BLOCKS
# ============================================================

@admin_allocation_bp.route(
    "/blocks",
    methods=["GET"]
)
@admin_required
def get_blocks():

    blocks = RoomAllocation.get_blocks()

    return jsonify({
        "success": True,
        "blocks": blocks
    })


# ============================================================
# GET ALL ROOMS
# ============================================================

@admin_allocation_bp.route(
    "/rooms",
    methods=["GET"]
)
@admin_required
def get_rooms():

    rooms = RoomAllocation.get_rooms()

    return jsonify({
        "success": True,
        "rooms": rooms
    })


# ============================================================
# GET ROOMS FOR PARTICULAR BLOCK
# ============================================================

@admin_allocation_bp.route(
    "/rooms/block/<int:block_id>",
    methods=["GET"]
)
@admin_required
def get_block_rooms(block_id):

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # ----------------------------------------------------
        # FETCH ROOMS DIRECTLY FOR SELECTED BLOCK
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                r.id,
                r.block_id,
                r.room_number,
                r.floor,
                r.capacity,
                r.room_type,
                r.status
            FROM rooms r
            WHERE r.block_id = %s
            ORDER BY
                r.floor ASC,
                r.room_number ASC
            """,
            (block_id,)
        )

        rooms = cursor.fetchall()

        # ----------------------------------------------------
        # CALCULATE AVAILABLE BEDS
        # ----------------------------------------------------

        for room in rooms:

            room_id = room["id"]

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS occupied_count
                FROM room_allocations
                WHERE room_id = %s
                AND status = 'active'
                """,
                (room_id,)
            )

            occupancy = cursor.fetchone()

            occupied_beds = int(
                occupancy["occupied_count"] or 0
            )

            capacity = int(
                room["capacity"] or 0
            )

            available_beds = (
                capacity - occupied_beds
            )

            if available_beds < 0:
                available_beds = 0

            room["occupied_beds"] = occupied_beds

            room["available_beds"] = available_beds

            # Keep both names available for frontend
            room["room_id"] = room["id"]

        return jsonify({
            "success": True,
            "rooms": rooms
        })

    except Exception as e:

        print(
            "GET BLOCK ROOMS ERROR:",
            e
        )

        return jsonify({
            "success": False,
            "message": "Unable to load rooms for this hostel block.",
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET SINGLE ROOM
# ============================================================

@admin_allocation_bp.route(
    "/room/<int:room_id>",
    methods=["GET"]
)
@admin_required
def get_room(room_id):

    room = RoomAllocation.get_room(
        room_id
    )

    if not room:

        return jsonify({
            "success": False,
            "message": "Room not found."
        }), 404

    occupied_beds = RoomAllocation.get_occupied_beds(
        room_id
    )

    return jsonify({
        "success": True,
        "room": room,
        "occupied_beds": occupied_beds
    })


# ============================================================
# GET AVAILABLE BEDS
# ============================================================

@admin_allocation_bp.route(
    "/room/<int:room_id>/beds",
    methods=["GET"]
)
@admin_required
def get_room_beds(room_id):

    room = RoomAllocation.get_room(
        room_id
    )

    if not room:

        return jsonify({
            "success": False,
            "message": "Room not found."
        }), 404

    capacity = int(
        room["capacity"] or 0
    )

    occupied_beds = set(
        str(bed)
        for bed in RoomAllocation.get_occupied_beds(
            room_id
        )
    )

    beds = []

    for bed_number in range(
        1,
        capacity + 1
    ):

        bed_string = str(
            bed_number
        )

        beds.append({
            "bed_number": bed_string,
            "occupied": (
                bed_string in occupied_beds
            ),
            "available": (
                bed_string not in occupied_beds
            )
        })

    return jsonify({
        "success": True,
        "room": room,
        "beds": beds
    })


# ============================================================
# ALLOCATE STUDENT
# ============================================================

@admin_allocation_bp.route(
    "/allocate",
    methods=["POST"]
)
@admin_required
def allocate_student():

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    student_id = request.form.get(
        "student_id",
        ""
    ).strip()

    room_id = request.form.get(
        "room_id",
        ""
    ).strip()

    bed_number = request.form.get(
        "bed_number",
        ""
    ).strip()

    allocation_date = request.form.get(
        "allocation_date",
        ""
    ).strip()

    if not student_id:

        return jsonify({
            "success": False,
            "message": "Please select a student."
        }), 400

    if not room_id:

        return jsonify({
            "success": False,
            "message": "Please select a room."
        }), 400

    if not bed_number:

        return jsonify({
            "success": False,
            "message": "Please select a bed."
        }), 400

    if not allocation_date:

        allocation_date = date.today().isoformat()

    try:

        student_id = int(
            student_id
        )

        room_id = int(
            room_id
        )

    except ValueError:

        return jsonify({
            "success": False,
            "message": "Invalid student or room."
        }), 400

    result = RoomAllocation.allocate_student(
        student_id=student_id,
        room_id=room_id,
        bed_number=bed_number,
        allocation_date=allocation_date
    )

    if not result["success"]:

        return jsonify(result), 400

    return jsonify(result)


# ============================================================
# GET ROOM STUDENTS
# ============================================================

@admin_allocation_bp.route(
    "/room/<int:room_id>/students",
    methods=["GET"]
)
@admin_required
def room_students(room_id):

    room = RoomAllocation.get_room(
        room_id
    )

    if not room:

        return jsonify({
            "success": False,
            "message": "Room not found."
        }), 404

    students = RoomAllocation.get_room_students(
        room_id
    )

    return jsonify({
        "success": True,
        "room": room,
        "students": students
    })


# ============================================================
# GET STUDENT ACTIVE ALLOCATION
# ============================================================

@admin_allocation_bp.route(
    "/student/<int:student_id>",
    methods=["GET"]
)
@admin_required
def student_allocation(student_id):

    allocation = RoomAllocation.get_student_active_allocation(
        student_id
    )

    return jsonify({
        "success": True,
        "allocation": allocation
    })


# ============================================================
# VACATE STUDENT
# ============================================================

@admin_allocation_bp.route(
    "/<int:allocation_id>/vacate",
    methods=["POST"]
)
@admin_required
def vacate_student(allocation_id):

    if not validate_csrf():

        return jsonify({
            "success": False,
            "message": "Invalid security token."
        }), 403

    vacated_date = request.form.get(
        "vacated_date",
        ""
    ).strip()

    if not vacated_date:

        vacated_date = date.today().isoformat()

    result = RoomAllocation.vacate_student(
        allocation_id=allocation_id,
        vacated_date=vacated_date
    )

    if not result["success"]:

        return jsonify(result), 400

    return jsonify(result)


# ============================================================
# ALLOCATION STATISTICS
# ============================================================

@admin_allocation_bp.route(
    "/statistics",
    methods=["GET"]
)
@admin_required
def statistics():

    return jsonify({
        "success": True,
        "statistics": RoomAllocation.get_statistics()
    })