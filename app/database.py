import os

import psycopg
from dotenv import load_dotenv
load_dotenv()

def get_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise Exception("DATABASE_URL environment variable is not set")
    return psycopg.connect(DATABASE_URL)

