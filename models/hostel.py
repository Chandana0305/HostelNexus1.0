from utils.database import get_db_connection


class Hostel:

    # ============================================================
    # BLOCK MANAGEMENT
    # ============================================================

    @staticmethod
    def get_all_blocks():
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
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
                ORDER BY hb.block_name ASC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_block_by_id(block_id):
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

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_block_by_name(block_name):
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
                WHERE block_name = %s
                LIMIT 1
            """, (block_name,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def create_block(block_name, description=None):
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
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

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def update_block(block_id, block_name, description, status):
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
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

            connection.commit()

            return cursor.rowcount > 0

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def delete_block(block_id):
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM rooms
                WHERE block_id = %s
            """, (block_id,))

            result = cursor.fetchone()

            if result and result[0] > 0:
                return False, "Cannot delete a block that contains rooms."

            cursor.execute("""
                DELETE FROM hostel_blocks
                WHERE id = %s
            """, (block_id,))

            connection.commit()

            if cursor.rowcount == 0:
                return False, "Hostel block not found."

            return True, "Hostel block deleted successfully."

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # ROOM MANAGEMENT
    # ============================================================

    @staticmethod
    def get_all_rooms():
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
                    r.status,
                    r.created_at,
                    r.updated_at,
                    hb.block_name,
                    COUNT(
                        CASE
                            WHEN ra.status = 'active'
                            THEN ra.id
                        END
                    ) AS occupied_beds
                FROM rooms r
                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id
                LEFT JOIN room_allocations ra
                    ON r.id = ra.room_id
                GROUP BY
                    r.id,
                    r.block_id,
                    r.room_number,
                    r.floor,
                    r.capacity,
                    r.status,
                    r.created_at,
                    r.updated_at,
                    hb.block_name
                ORDER BY
                    hb.block_name ASC,
                    r.room_number ASC
            """)

            rooms = cursor.fetchall()

            for room in rooms:
                room["available_beds"] = max(
                    0,
                    int(room["capacity"]) - int(room["occupied_beds"])
                )

            return rooms

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_rooms_by_block(block_id):
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
                    r.status,
                    r.created_at,
                    r.updated_at,
                    hb.block_name,
                    COUNT(
                        CASE
                            WHEN ra.status = 'active'
                            THEN ra.id
                        END
                    ) AS occupied_beds
                FROM rooms r
                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id
                LEFT JOIN room_allocations ra
                    ON r.id = ra.room_id
                WHERE r.block_id = %s
                GROUP BY
                    r.id,
                    r.block_id,
                    r.room_number,
                    r.floor,
                    r.capacity,
                    r.status,
                    r.created_at,
                    r.updated_at,
                    hb.block_name
                ORDER BY r.room_number ASC
            """, (block_id,))

            rooms = cursor.fetchall()

            for room in rooms:
                room["available_beds"] = max(
                    0,
                    int(room["capacity"]) - int(room["occupied_beds"])
                )

            return rooms

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_room_by_id(room_id):
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

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def get_room_by_number(block_id, room_number):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    id,
                    block_id,
                    room_number,
                    floor,
                    capacity,
                    status
                FROM rooms
                WHERE block_id = %s
                  AND room_number = %s
                LIMIT 1
            """, (
                block_id,
                room_number
            ))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def create_room(
        block_id,
        room_number,
        floor,
        capacity
    ):
        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO rooms (
                    block_id,
                    room_number,
                    floor,
                    capacity,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'active',
                    NOW(),
                    NOW()
                )
            """, (
                block_id,
                room_number,
                floor,
                capacity
            ))

            connection.commit()

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def update_room(
        room_id,
        block_id,
        room_number,
        floor,
        capacity,
        status
    ):
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
            occupied_beds = int(result[0]) if result else 0

            if int(capacity) < occupied_beds:
                return False, (
                    "Room capacity cannot be less than "
                    "the number of currently allocated students."
                )

            cursor.execute("""
                UPDATE rooms
                SET
                    block_id = %s,
                    room_number = %s,
                    floor = %s,
                    capacity = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                block_id,
                room_number,
                floor,
                capacity,
                status,
                room_id
            ))

            connection.commit()

            if cursor.rowcount == 0:
                return False, "Room not found."

            return True, "Room updated successfully."

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    @staticmethod
    def delete_room(room_id):
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

            if result and result[0] > 0:
                return False, (
                    "Cannot delete a room with active student allocations."
                )

            cursor.execute("""
                DELETE FROM rooms
                WHERE id = %s
            """, (room_id,))

            connection.commit()

            if cursor.rowcount == 0:
                return False, "Room not found."

            return True, "Room deleted successfully."

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # ROOM OCCUPANCY
    # ============================================================

    @staticmethod
    def get_room_occupancy(room_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    r.id AS room_id,
                    r.room_number,
                    r.capacity,
                    r.status,
                    hb.block_name,
                    COUNT(
                        CASE
                            WHEN ra.status = 'active'
                            THEN ra.id
                        END
                    ) AS occupied_beds
                FROM rooms r
                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id
                LEFT JOIN room_allocations ra
                    ON r.id = ra.room_id
                WHERE r.id = %s
                GROUP BY
                    r.id,
                    r.room_number,
                    r.capacity,
                    r.status,
                    hb.block_name
                LIMIT 1
            """, (room_id,))

            occupancy = cursor.fetchone()

            if not occupancy:
                return None

            occupancy["available_beds"] = max(
                0,
                int(occupancy["capacity"]) -
                int(occupancy["occupied_beds"])
            )

            return occupancy

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # STUDENTS INSIDE A ROOM
    # ============================================================

    @staticmethod
    def get_students_in_room(room_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    ra.id AS allocation_id,
                    ra.room_id,
                    ra.student_id,
                    ra.bed_number,
                    ra.allocation_date,
                    ra.status,

                    s.student_id AS usn,
                    s.first_name,
                    s.last_name,
                    s.profile_photo,
                    s.email,
                    s.phone,
                    s.department,
                    s.batch,
                    s.year,

                    r.room_number,
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
                    s.first_name ASC
            """, (room_id,))

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # AVAILABLE ROOMS
    # ============================================================

    @staticmethod
    def get_available_rooms():
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
                    r.status,
                    hb.block_name,

                    COUNT(
                        CASE
                            WHEN ra.status = 'active'
                            THEN ra.id
                        END
                    ) AS occupied_beds

                FROM rooms r

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                LEFT JOIN room_allocations ra
                    ON r.id = ra.room_id

                WHERE r.status = 'active'

                GROUP BY
                    r.id,
                    r.block_id,
                    r.room_number,
                    r.floor,
                    r.capacity,
                    r.status,
                    hb.block_name

                HAVING occupied_beds < r.capacity

                ORDER BY
                    hb.block_name ASC,
                    r.room_number ASC
            """)

            rooms = cursor.fetchall()

            for room in rooms:
                room["available_beds"] = (
                    int(room["capacity"]) -
                    int(room["occupied_beds"])
                )

            return rooms

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # STUDENTS AVAILABLE FOR ALLOCATION
    # ============================================================

    @staticmethod
    def get_students_without_active_allocation():
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
                    s.department,
                    s.batch,
                    s.year,
                    s.registration_status

                FROM students s

                LEFT JOIN room_allocations ra
                    ON s.id = ra.student_id
                   AND ra.status = 'active'

                WHERE s.registration_status = 'approved'
                  AND ra.id IS NULL

                ORDER BY
                    s.student_id ASC
            """)

            return cursor.fetchall()

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # STUDENT CURRENT ROOM
    # ============================================================

    @staticmethod
    def get_student_current_room(student_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT
                    ra.id AS allocation_id,
                    ra.student_id,
                    ra.room_id,
                    ra.bed_number,
                    ra.allocation_date,
                    ra.status,

                    r.room_number,
                    r.floor,
                    r.capacity,

                    hb.id AS block_id,
                    hb.block_name

                FROM room_allocations ra

                INNER JOIN rooms r
                    ON ra.room_id = r.id

                INNER JOIN hostel_blocks hb
                    ON r.block_id = hb.id

                WHERE ra.student_id = %s
                  AND ra.status = 'active'

                ORDER BY ra.allocation_date DESC
                LIMIT 1
            """, (student_id,))

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()


    # ============================================================
    # ROOM STATISTICS
    # ============================================================

    @staticmethod
    def get_statistics():
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT COUNT(*) AS total_blocks
                FROM hostel_blocks
                WHERE status = 'active'
            """)

            total_blocks = cursor.fetchone()["total_blocks"]

            cursor.execute("""
                SELECT COUNT(*) AS total_rooms
                FROM rooms
                WHERE status = 'active'
            """)

            total_rooms = cursor.fetchone()["total_rooms"]

            cursor.execute("""
                SELECT
                    COALESCE(SUM(capacity), 0) AS total_capacity
                FROM rooms
                WHERE status = 'active'
            """)

            total_capacity = cursor.fetchone()["total_capacity"]

            cursor.execute("""
                SELECT COUNT(*) AS occupied_beds
                FROM room_allocations
                WHERE status = 'active'
            """)

            occupied_beds = cursor.fetchone()["occupied_beds"]

            available_beds = max(
                0,
                int(total_capacity) - int(occupied_beds)
            )

            return {
                "total_blocks": int(total_blocks),
                "total_rooms": int(total_rooms),
                "total_capacity": int(total_capacity),
                "occupied_beds": int(occupied_beds),
                "available_beds": int(available_beds)
            }

        finally:
            cursor.close()
            connection.close()