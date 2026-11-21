from utils.database import get_db_connection


class RoomAllocation:

    # ============================================================
    # GET ALL APPROVED STUDENTS AVAILABLE FOR ALLOCATION
    # ============================================================

    @staticmethod
    def get_available_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    s.id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.profile_photo,
                    s.email,
                    s.phone,
                    s.course,
                    s.department,
                    s.batch,
                    s.year
                FROM students s
                INNER JOIN users u
                    ON s.user_id = u.id
                WHERE s.registration_status = 'approved'
                  AND u.status = 'active'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM room_allocations ra
                      WHERE ra.student_id = s.id
                        AND ra.status = 'active'
                  )
                ORDER BY
                    s.student_id ASC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET ALL BLOCKS
    # ============================================================

    @staticmethod
    def get_blocks():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    block_name,
                    description,
                    status
                FROM hostel_blocks
                WHERE status = 'active'
                ORDER BY block_name ASC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET ROOMS WITH OCCUPANCY
    # ============================================================

    @staticmethod
    def get_rooms():

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
                    hb.block_name,

                    (
                        SELECT COUNT(*)
                        FROM room_allocations ra
                        WHERE ra.room_id = r.id
                          AND ra.status = 'active'
                    ) AS occupied_beds

                FROM rooms r

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE hb.status = 'active'

                ORDER BY
                    hb.block_name ASC,
                    r.floor ASC,
                    r.room_number ASC
            """)

            rooms = cursor.fetchall()

            for room in rooms:

                capacity = int(
                    room["capacity"] or 0
                )

                occupied = int(
                    room["occupied_beds"] or 0
                )

                room["available_beds"] = max(
                    capacity - occupied,
                    0
                )

            return rooms

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET ONE ROOM WITH OCCUPANCY
    # ============================================================

    @staticmethod
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
                    hb.block_name,

                    (
                        SELECT COUNT(*)
                        FROM room_allocations ra
                        WHERE ra.room_id = r.id
                          AND ra.status = 'active'
                    ) AS occupied_beds

                FROM rooms r

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE r.id = %s

                LIMIT 1
            """, (room_id,))

            room = cursor.fetchone()

            if room:

                capacity = int(
                    room["capacity"] or 0
                )

                occupied = int(
                    room["occupied_beds"] or 0
                )

                room["available_beds"] = max(
                    capacity - occupied,
                    0
                )

            return room

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET OCCUPIED BED NUMBERS FOR A ROOM
    # ============================================================

    @staticmethod
    def get_occupied_beds(room_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    bed_number
                FROM room_allocations
                WHERE room_id = %s
                  AND status = 'active'
                ORDER BY bed_number ASC
            """, (room_id,))

            rows = cursor.fetchall()

            return [
                str(row["bed_number"])
                for row in rows
            ]

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET STUDENT ACTIVE ALLOCATION
    # ============================================================

    @staticmethod
    def get_student_active_allocation(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    ra.id,
                    ra.student_id,
                    ra.room_id,
                    ra.bed_number,
                    ra.allocation_date,
                    ra.vacated_date,
                    ra.status,

                    r.room_number,
                    r.floor,
                    r.capacity,
                    r.room_type,

                    hb.id AS block_id,
                    hb.block_name

                FROM room_allocations ra

                INNER JOIN rooms r
                    ON ra.room_id = r.id

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE ra.student_id = %s
                  AND ra.status = 'active'

                ORDER BY
                    ra.id DESC

                LIMIT 1
            """, (student_id,))

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET ALL ACTIVE ALLOCATIONS
    # ============================================================

    @staticmethod
    def get_active_allocations():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    ra.id,
                    ra.student_id,
                    ra.room_id,
                    ra.bed_number,
                    ra.allocation_date,
                    ra.status,

                    s.student_id AS usn,
                    s.first_name,
                    s.last_name,
                    s.profile_photo,
                    s.department,
                    s.batch,
                    s.year,

                    r.room_number,
                    r.floor,

                    hb.block_name

                FROM room_allocations ra

                INNER JOIN students s
                    ON ra.student_id = s.id

                INNER JOIN rooms r
                    ON ra.room_id = r.id

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE ra.status = 'active'

                ORDER BY
                    hb.block_name ASC,
                    r.room_number ASC,
                    ra.bed_number ASC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # GET STUDENTS INSIDE A ROOM
    # ============================================================

    @staticmethod
    def get_room_students(room_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    ra.id AS allocation_id,
                    ra.bed_number,
                    ra.allocation_date,

                    s.id AS student_record_id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.profile_photo,
                    s.email,
                    s.phone,
                    s.department,
                    s.batch,
                    s.year,

                    r.room_number,
                    r.floor,

                    hb.block_name

                FROM room_allocations ra

                INNER JOIN students s
                    ON ra.student_id = s.id

                INNER JOIN rooms r
                    ON ra.room_id = r.id

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE ra.room_id = %s
                  AND ra.status = 'active'

                ORDER BY
                    ra.bed_number ASC,
                    s.student_id ASC
            """, (room_id,))

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # ALLOCATE STUDENT
    # ============================================================

    @staticmethod
    def allocate_student(
        student_id,
        room_id,
        bed_number,
        allocation_date
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            connection.start_transaction()


            # ----------------------------------------------------
            # Validate student
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    s.id,
                    s.registration_status,
                    u.status
                FROM students s
                INNER JOIN users u
                    ON s.user_id = u.id
                WHERE s.id = %s
                LIMIT 1
            """, (student_id,))

            student = cursor.fetchone()


            if not student:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Student not found."
                }


            if student["registration_status"] != "approved":

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "Only approved students can be allocated "
                        "to a hostel room."
                    )
                }


            if student["status"] != "active":

                connection.rollback()

                return {
                    "success": False,
                    "message": "Student account is not active."
                }


            # ----------------------------------------------------
            # Check existing active allocation
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    id
                FROM room_allocations
                WHERE student_id = %s
                  AND status = 'active'
                LIMIT 1
            """, (student_id,))

            existing_student = cursor.fetchone()


            if existing_student:

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "This student is already allocated "
                        "to a hostel room."
                    )
                }


            # ----------------------------------------------------
            # Validate room
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    r.id,
                    r.block_id,
                    r.room_number,
                    r.capacity,
                    r.status,
                    hb.status AS block_status

                FROM rooms r

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE r.id = %s

                LIMIT 1
            """, (room_id,))

            room = cursor.fetchone()


            if not room:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Room not found."
                }


            if room["block_status"] != "active":

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "This hostel block is inactive."
                    )
                }


            if room["status"] not in [
                "active",
                "available"
            ]:

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "This room is currently unavailable."
                    )
                }


            # ----------------------------------------------------
            # Validate bed number
            # ----------------------------------------------------

            bed_number = str(
                bed_number
            ).strip()


            if not bed_number:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Bed number is required."
                }


            # ----------------------------------------------------
            # Check whether bed is already occupied
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    id
                FROM room_allocations
                WHERE room_id = %s
                  AND bed_number = %s
                  AND status = 'active'
                LIMIT 1
            """, (
                room_id,
                bed_number
            ))

            existing_bed = cursor.fetchone()


            if existing_bed:

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        f"Bed {bed_number} is already occupied."
                    )
                }


            # ----------------------------------------------------
            # Check current room occupancy
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    COUNT(*) AS occupied
                FROM room_allocations
                WHERE room_id = %s
                  AND status = 'active'
            """, (room_id,))

            occupancy = cursor.fetchone()

            occupied = int(
                occupancy["occupied"]
                if occupancy
                else 0
            )

            capacity = int(
                room["capacity"]
                or 0
            )


            if occupied >= capacity:

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "This room is already full."
                    )
                }


            # ----------------------------------------------------
            # Validate bed number against capacity
            #
            # Numeric bed numbers 1..capacity are supported.
            # Non-numeric values are also allowed for future
            # configurations such as A, B, C, etc.
            # ----------------------------------------------------

            try:

                numeric_bed = int(
                    bed_number
                )

                if (
                    numeric_bed < 1
                    or numeric_bed > capacity
                ):

                    connection.rollback()

                    return {
                        "success": False,
                        "message": (
                            f"Bed number must be between "
                            f"1 and {capacity}."
                        )
                    }

            except ValueError:

                pass


            # ----------------------------------------------------
            # Create allocation
            # ----------------------------------------------------

            cursor.execute("""
                INSERT INTO room_allocations (
                    student_id,
                    room_id,
                    bed_number,
                    allocation_date,
                    vacated_date,
                    status,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    'active',
                    NOW()
                )
            """, (
                student_id,
                room_id,
                bed_number,
                allocation_date
            ))


            allocation_id = cursor.lastrowid


            # ----------------------------------------------------
            # Update room status when completely occupied
            # ----------------------------------------------------

            new_occupied = occupied + 1


            if new_occupied >= capacity:

                cursor.execute("""
                    UPDATE rooms
                    SET
                        status = 'occupied',
                        updated_at = NOW()
                    WHERE id = %s
                """, (room_id,))

            else:

                cursor.execute("""
                    UPDATE rooms
                    SET
                        status = 'active',
                        updated_at = NOW()
                    WHERE id = %s
                """, (room_id,))


            connection.commit()


            return {
                "success": True,
                "message": "Student allocated successfully.",
                "allocation_id": allocation_id
            }


        except Exception as error:

            connection.rollback()

            print(
                "ALLOCATE STUDENT ERROR:",
                error
            )

            return {
                "success": False,
                "message": "Unable to allocate student."
            }

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # VACATE STUDENT
    # ============================================================

    @staticmethod
    def vacate_student(
        allocation_id,
        vacated_date
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            connection.start_transaction()


            # ----------------------------------------------------
            # Get allocation
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    id,
                    room_id,
                    student_id,
                    status
                FROM room_allocations
                WHERE id = %s
                LIMIT 1
            """, (allocation_id,))

            allocation = cursor.fetchone()


            if not allocation:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Allocation not found."
                }


            if allocation["status"] != "active":

                connection.rollback()

                return {
                    "success": False,
                    "message": (
                        "This allocation is already inactive."
                    )
                }


            # ----------------------------------------------------
            # Mark allocation as vacated
            # ----------------------------------------------------

            cursor.execute("""
                UPDATE room_allocations
                SET
                    status = 'vacated',
                    vacated_date = %s
                WHERE id = %s
                  AND status = 'active'
            """, (
                vacated_date,
                allocation_id
            ))


            if cursor.rowcount == 0:

                connection.rollback()

                return {
                    "success": False,
                    "message": "Unable to vacate allocation."
                }


            # ----------------------------------------------------
            # Check remaining occupancy
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    COUNT(*) AS occupied
                FROM room_allocations
                WHERE room_id = %s
                  AND status = 'active'
            """, (
                allocation["room_id"],
            ))

            occupancy = cursor.fetchone()

            occupied = int(
                occupancy["occupied"]
                if occupancy
                else 0
            )


            # ----------------------------------------------------
            # Change room status
            # ----------------------------------------------------

            cursor.execute("""
                UPDATE rooms
                SET
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                "active",
                allocation["room_id"]
            ))


            connection.commit()


            return {
                "success": True,
                "message": "Student vacated successfully.",
                "remaining_occupancy": occupied
            }


        except Exception as error:

            connection.rollback()

            print(
                "VACATE STUDENT ERROR:",
                error
            )

            return {
                "success": False,
                "message": "Unable to vacate student."
            }

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # STATISTICS
    # ============================================================

    @staticmethod
    def get_statistics():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            # Total rooms
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_rooms
                FROM rooms
            """)

            total_rooms = cursor.fetchone()["total_rooms"]


            # Total capacity
            cursor.execute("""
                SELECT
                    COALESCE(SUM(capacity), 0) AS total_capacity
                FROM rooms
            """)

            total_capacity = cursor.fetchone()["total_capacity"]


            # Occupied beds
            cursor.execute("""
                SELECT
                    COUNT(*) AS occupied_beds
                FROM room_allocations
                WHERE status = 'active'
            """)

            occupied_beds = cursor.fetchone()["occupied_beds"]


            # Active allocations
            cursor.execute("""
                SELECT
                    COUNT(*) AS active_allocations
                FROM room_allocations
                WHERE status = 'active'
            """)

            active_allocations = cursor.fetchone()[
                "active_allocations"
            ]


            available_beds = max(
                int(total_capacity or 0)
                - int(occupied_beds or 0),
                0
            )


            return {
                "total_rooms": int(
                    total_rooms or 0
                ),
                "total_capacity": int(
                    total_capacity or 0
                ),
                "occupied_beds": int(
                    occupied_beds or 0
                ),
                "available_beds": int(
                    available_beds
                ),
                "active_allocations": int(
                    active_allocations or 0
                )
            }

        finally:

            cursor.close()
            connection.close()