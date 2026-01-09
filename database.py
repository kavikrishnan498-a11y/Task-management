import sqlite3

DB_NAME = "task_manager.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # -------- Users Table --------
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # -------- Tasks Table --------
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        task TEXT,
        description TEXT,
        due_date TEXT,
        due_time TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
