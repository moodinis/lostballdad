import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

_config = dict(
    host=os.environ['DB_HOST'],
    port=int(os.environ.get('DB_PORT', 3306)),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    ssl_disabled=False,
)

def get_conn():
    return mysql.connector.connect(**_config)
