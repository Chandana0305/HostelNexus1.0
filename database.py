import mysql.connector
from config import Config


def get_db_connection():
    """Create a MySQL connection using environment-based configuration."""
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        charset="utf8mb4",
        use_unicode=True,
        connection_timeout=10,
        autocommit=False,
    )
