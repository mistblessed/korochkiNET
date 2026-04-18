import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if DATABASE_URL is None:

        DB_HOST = os.getenv('DB_HOST','localhost')
        DB_PORT= os.getenv('DB_PORT','5432')
        DB_USER = os.getenv('DB_USER','postgres')
        DB_PASSWORD = os.getenv('DB_PASSWORD','5432')
        DB_NAME = os.getenv('DB_NAME','korochki')

    else:
        pass

    SECRET_KEY = os.getenv('SECRET_KEY', 'fdsjfioegwifjef8w39rjwefioqwd3wr25refdg')

    @staticmethod
    def get_db_uri():
        return f'host={Config.DB_HOST} port={Config.DB_PORT} user={Config.DB_USER} password={Config.DB_PASSWORD} dbname={Config.DB_NAME}'
