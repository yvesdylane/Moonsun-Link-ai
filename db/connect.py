import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

class AutoReconnectConnection:
    def __init__(self):
        self._conn = None
        self._connect()

    def _connect(self):
        self._conn = psycopg.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
        )

    def cursor(self, *args, **kwargs):
        try:
            return self._conn.cursor(*args, **kwargs)
        except psycopg.OperationalError:
            print("DB connection lost, reconnecting...")
            self._connect()
            return self._conn.cursor(*args, **kwargs)

    def commit(self):
        try:
            self._conn.commit()
        except psycopg.OperationalError:
            print("DB connection lost on commit, reconnecting...")
            self._connect()
            self._conn.commit()

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)

try:
    conn = AutoReconnectConnection()
    print("Connected to PostgreSQL successfully!")
except Exception as e:
    print("Connection failed!")
    print(e)
    conn = None
