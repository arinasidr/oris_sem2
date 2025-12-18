import psycopg2

with open('props.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

db_password = lines[0].strip()

def get_connection():
    return psycopg2.connect(
    dbname='session_navigator',
    user='postgres',
    password=db_password,
    host='localhost'
)