from getpass import getpass

from werkzeug.security import generate_password_hash

from utils.database import get_db_connection


def main():

    print("=" * 55)
    print("        HostelNexus - Create Admin Account")
    print("=" * 55)

    username = input("Enter admin username/email: ").strip()

    if not username:
        print("\nUsername is required.")
        return

    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if not password:
        print("\nPassword is required.")
        return

    if password != confirm_password:
        print("\nPasswords do not match.")
        return

    if len(password) < 6:
        print("\nPassword must contain at least 6 characters.")
        return

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # -------------------------------------------------
        # CHECK WHETHER USERNAME ALREADY EXISTS
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT id, username, role
            FROM users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            print("\nAn account with this username already exists.")

            if existing_user["role"] == "admin":
                print("It is already registered as an Admin account.")
            else:
                print("It is registered as a Student account.")

            return

        # -------------------------------------------------
        # HASH PASSWORD
        # -------------------------------------------------

        hashed_password = generate_password_hash(password)

        # -------------------------------------------------
        # CREATE ADMIN
        # -------------------------------------------------

        cursor.execute(
            """
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
                'admin',
                'active',
                NOW(),
                NOW()
            )
            """,
            (
                username,
                hashed_password
            )
        )

        connection.commit()

        admin_id = cursor.lastrowid

        print("\n" + "=" * 55)
        print("Admin account created successfully!")
        print("=" * 55)
        print(f"Admin ID : {admin_id}")
        print(f"Username : {username}")
        print("Role     : admin")
        print("Status   : active")
        print("=" * 55)

    except Exception as error:

        if connection:
            connection.rollback()

        print("\nUnable to create Admin account.")
        print("Error:", error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    main()