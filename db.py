import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    unix_socket = os.environ.get('DB_SOCKET')
    if unix_socket:
        return mysql.connector.connect(
            unix_socket=unix_socket,
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            database=os.environ['DB_NAME'],
        )
    return mysql.connector.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ.get('DB_PORT', 3306)),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'],
        ssl_disabled=False,
    )
