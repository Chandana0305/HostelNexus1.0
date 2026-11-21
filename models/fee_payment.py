from datetime import date
from utils.database import get_db_connection


class FeePayment:

    # ============================================================
    # FEE STRUCTURES
    # ============================================================

    @staticmethod
    def get_all_fee_structures():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    batch,
                    academic_year,
                    hostel_fee,
                    mess_fee,
                    security_deposit,
                    other_fee,
                    total_fee,
                    due_date,
                    status,
                    created_at,
                    updated_at
                FROM fee_structures
                ORDER BY id DESC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_active_fee_structures():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    batch,
                    academic_year,
                    hostel_fee,
                    mess_fee,
                    security_deposit,
                    other_fee,
                    total_fee,
                    due_date,
                    status
                FROM fee_structures
                WHERE status = 'active'
                ORDER BY batch ASC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_fee_structure_by_id(fee_structure_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    id,
                    batch,
                    academic_year,
                    hostel_fee,
                    mess_fee,
                    security_deposit,
                    other_fee,
                    total_fee,
                    due_date,
                    status,
                    created_at,
                    updated_at
                FROM fee_structures
                WHERE id = %s
                LIMIT 1
            """, (fee_structure_id,))

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def create_fee_structure(
        batch,
        academic_year,
        hostel_fee,
        mess_fee,
        security_deposit,
        other_fee,
        due_date,
        status="active"
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            hostel_fee = float(hostel_fee or 0)
            mess_fee = float(mess_fee or 0)
            security_deposit = float(
                security_deposit or 0
            )
            other_fee = float(
                other_fee or 0
            )

            total_fee = (
                hostel_fee
                + mess_fee
                + security_deposit
                + other_fee
            )

            cursor.execute("""
                INSERT INTO fee_structures (
                    batch,
                    academic_year,
                    hostel_fee,
                    mess_fee,
                    security_deposit,
                    other_fee,
                    total_fee,
                    due_date,
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
                    %s,
                    %s,
                    %s,
                    NOW(),
                    NOW()
                )
            """, (
                batch,
                academic_year,
                hostel_fee,
                mess_fee,
                security_deposit,
                other_fee,
                total_fee,
                due_date,
                status
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
    def update_fee_structure(
        fee_structure_id,
        batch,
        academic_year,
        hostel_fee,
        mess_fee,
        security_deposit,
        other_fee,
        due_date,
        status
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            hostel_fee = float(hostel_fee or 0)
            mess_fee = float(mess_fee or 0)
            security_deposit = float(
                security_deposit or 0
            )
            other_fee = float(
                other_fee or 0
            )

            total_fee = (
                hostel_fee
                + mess_fee
                + security_deposit
                + other_fee
            )

            cursor.execute("""
                UPDATE fee_structures
                SET
                    batch = %s,
                    academic_year = %s,
                    hostel_fee = %s,
                    mess_fee = %s,
                    security_deposit = %s,
                    other_fee = %s,
                    total_fee = %s,
                    due_date = %s,
                    status = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                batch,
                academic_year,
                hostel_fee,
                mess_fee,
                security_deposit,
                other_fee,
                total_fee,
                due_date,
                status,
                fee_structure_id
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
    def delete_fee_structure(fee_structure_id):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            # ----------------------------------------------------
            # CHECK WHETHER PAYMENTS EXIST
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    id
                FROM payments
                WHERE fee_structure_id = %s
                LIMIT 1
            """, (fee_structure_id,))

            payment = cursor.fetchone()

            if payment:

                return {
                    "success": False,
                    "message": (
                        "This fee structure cannot be deleted "
                        "because payments already exist."
                    )
                }

            cursor.execute("""
                DELETE FROM fee_structures
                WHERE id = %s
            """, (fee_structure_id,))

            connection.commit()

            if cursor.rowcount == 0:

                return {
                    "success": False,
                    "message": "Fee structure not found."
                }

            return {
                "success": True,
                "message": "Fee structure deleted successfully."
            }

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # STUDENTS
    # ============================================================

    @staticmethod
    def get_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    s.id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.batch,
                    s.course,
                    s.department,
                    s.registration_status
                FROM students s
                WHERE s.registration_status = 'approved'
                ORDER BY
                    s.student_id ASC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_student_by_id(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    s.id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.batch,
                    s.course,
                    s.department,
                    s.registration_status
                FROM students s
                WHERE s.id = %s
                LIMIT 1
            """, (student_id,))

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # PAYMENTS
    # ============================================================

    @staticmethod
    def get_all_payments():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    p.id,
                    p.student_id,
                    p.fee_structure_id,
                    p.receipt_number,
                    p.amount,
                    p.payment_method,
                    p.transaction_id,
                    p.payment_date,
                    p.remarks,
                    p.created_at,

                    s.student_id AS usn,
                    s.first_name,
                    s.last_name,
                    s.batch,

                    f.academic_year,
                    f.total_fee

                FROM payments p

                INNER JOIN students s
                    ON p.student_id = s.id

                LEFT JOIN fee_structures f
                    ON p.fee_structure_id = f.id

                ORDER BY
                    p.payment_date DESC,
                    p.id DESC
            """)

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_payment_by_id(payment_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    p.id,
                    p.student_id,
                    p.fee_structure_id,
                    p.receipt_number,
                    p.amount,
                    p.payment_method,
                    p.transaction_id,
                    p.payment_date,
                    p.remarks,
                    p.created_at,

                    s.student_id AS usn,
                    s.first_name,
                    s.last_name,
                    s.email,
                    s.phone,
                    s.batch,
                    s.course,
                    s.department,

                    f.batch AS fee_batch,
                    f.academic_year,
                    f.hostel_fee,
                    f.mess_fee,
                    f.security_deposit,
                    f.other_fee,
                    f.total_fee,
                    f.due_date

                FROM payments p

                INNER JOIN students s
                    ON p.student_id = s.id

                LEFT JOIN fee_structures f
                    ON p.fee_structure_id = f.id

                WHERE p.id = %s

                LIMIT 1
            """, (payment_id,))

            return cursor.fetchone()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_student_payments(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    p.id,
                    p.student_id,
                    p.fee_structure_id,
                    p.receipt_number,
                    p.amount,
                    p.payment_method,
                    p.transaction_id,
                    p.payment_date,
                    p.remarks,

                    f.batch,
                    f.academic_year,
                    f.total_fee

                FROM payments p

                LEFT JOIN fee_structures f
                    ON p.fee_structure_id = f.id

                WHERE p.student_id = %s

                ORDER BY
                    p.payment_date DESC,
                    p.id DESC
            """, (student_id,))

            return cursor.fetchall()

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_student_payment_summary(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            # ----------------------------------------------------
            # TOTAL PAID
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    COALESCE(
                        SUM(amount),
                        0
                    ) AS total_paid
                FROM payments
                WHERE student_id = %s
            """, (student_id,))

            payment_data = cursor.fetchone()

            total_paid = float(
                payment_data["total_paid"] or 0
            )

            # ----------------------------------------------------
            # TOTAL ASSIGNED FEE
            # ----------------------------------------------------

            cursor.execute("""
                SELECT
                    COALESCE(
                        MAX(f.total_fee),
                        0
                    ) AS total_fee
                FROM fee_structures f

                INNER JOIN students s
                    ON s.batch = f.batch

                WHERE s.id = %s
                AND f.status = 'active'
            """, (student_id,))

            fee_data = cursor.fetchone()

            total_fee = float(
                fee_data["total_fee"] or 0
            )

            pending = (
                total_fee - total_paid
            )

            if pending < 0:
                pending = 0

            return {
                "total_fee": total_fee,
                "total_paid": total_paid,
                "pending_amount": pending
            }

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def generate_receipt_number():

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                SELECT
                    id
                FROM payments
                ORDER BY id DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

            if row:

                next_id = int(
                    row[0]
                ) + 1

            else:

                next_id = 1

            return (
                "HN-"
                + str(date.today().year)
                + "-"
                + str(next_id).zfill(5)
            )

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def create_payment(
        student_id,
        fee_structure_id,
        amount,
        payment_method,
        transaction_id,
        payment_date,
        remarks
    ):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            receipt_number = (
                FeePayment.generate_receipt_number()
            )

            cursor.execute("""
                INSERT INTO payments (
                    student_id,
                    fee_structure_id,
                    receipt_number,
                    amount,
                    payment_method,
                    transaction_id,
                    payment_date,
                    remarks,
                    created_at
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
                    NOW()
                )
            """, (
                student_id,
                fee_structure_id,
                receipt_number,
                amount,
                payment_method,
                transaction_id,
                payment_date,
                remarks
            ))

            payment_id = cursor.lastrowid

            connection.commit()

            return {
                "success": True,
                "payment_id": payment_id,
                "receipt_number": receipt_number
            }

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()


    # ============================================================
    # BATCH-WISE REPORT
    # ============================================================

    @staticmethod
    def get_batch_payment_report(batch=None):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:

            query = """
                SELECT
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

                    COALESCE(
                        f.total_fee,
                        0
                    ) AS total_fee,

                    COALESCE(
                        SUM(p.amount),
                        0
                    ) AS paid_amount

                FROM students s

                LEFT JOIN fee_structures f
                    ON f.batch = s.batch
                    AND f.status = 'active'

                LEFT JOIN payments p
                    ON p.student_id = s.id
                    AND p.fee_structure_id = f.id

                WHERE s.registration_status = 'approved'
            """

            parameters = []

            if batch:

                query += """
                    AND s.batch = %s
                """

                parameters.append(
                    batch
                )

            query += """
                GROUP BY
                    s.id,
                    s.student_id,
                    s.first_name,
                    s.last_name,
                    s.batch,
                    f.total_fee

                ORDER BY
                    s.batch ASC,
                    s.student_id ASC
            """

            cursor.execute(
                query,
                tuple(parameters)
            )

            rows = cursor.fetchall()

            for row in rows:

                total_fee = float(
                    row["total_fee"] or 0
                )

                paid_amount = float(
                    row["paid_amount"] or 0
                )

                pending_amount = (
                    total_fee - paid_amount
                )

                if pending_amount < 0:
                    pending_amount = 0

                row["pending_amount"] = (
                    pending_amount
                )

            return rows

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def get_batches():

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                SELECT DISTINCT
                    batch
                FROM students
                WHERE batch IS NOT NULL
                AND batch <> ''
                ORDER BY batch ASC
            """)

            rows = cursor.fetchall()

            return [
                row[0]
                for row in rows
            ]

        finally:

            cursor.close()
            connection.close()