import psycopg2
import psycopg2.extras
from config import Config
import os

def get_connection():
    if Config.DATABASE_URL:
        # На Render используем DATABASE_URL
        return psycopg2.connect(Config.DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        # Локально используем отдельные параметры
        return psycopg2.connect(
            host=Config.DB_HOST,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            cursor_factory=psycopg2.extras.RealDictCursor
        )

def execute_query(sql, params=None, fetch_all=False, fetch_one=False):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    result = None
    if fetch_all:
        result = cur.fetchall()
    elif fetch_one:
        result = cur.fetchone()
    conn.commit()          # <-- ДОБАВИТЬ ЭТУ СТРОКУ
    cur.close()
    conn.close()
    return result