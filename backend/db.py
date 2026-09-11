import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1]/'.env')


def connect():
    url=os.environ.get('DATABASE_URL')
    if not url:
        raise psycopg.OperationalError('DATABASE_URL is not configured')
    return psycopg.connect(url,row_factory=dict_row,connect_timeout=5,options='-c statement_timeout=10000 -c timezone=UTC')
