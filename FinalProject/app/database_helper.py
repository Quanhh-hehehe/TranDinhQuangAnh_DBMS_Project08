import mysql.connector
from mysql.connector import pooling
from .config import DB_CONFIG

class DatabaseHelper:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="cinema_pool",
        pool_size=10,
        pool_reset_session=True,
        **DB_CONFIG
    )

    @staticmethod
    def get_connection():
        return DatabaseHelper.connection_pool.get_connection()
    
    