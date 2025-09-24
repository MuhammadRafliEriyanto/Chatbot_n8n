# app/utils/db_conn.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("USER_SUPER")
PASSWORD = os.getenv("PASS_SUPER")
HOST = os.getenv("HOST_SUPER")
PORT = os.getenv("PORT_SUPER")
DBNAME = os.getenv("DATABASE_SUPER")

def get_connection():
    return psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME
    )