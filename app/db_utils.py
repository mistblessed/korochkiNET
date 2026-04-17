import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user='postgres',
        password='5432',
        dbname='korochki',
        client_encoding='UTF8'
    )
    return conn

def execute_query(query: str, params=None, fetch_one=False, fetch_all=False):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query, params)
        if fetch_one:
            result = cur.fetchone()
        elif fetch_all:
            result = cur.fetchall()
        else:
            result = None
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise e
    
    finally:
        cur.close()
        conn.close()
        

