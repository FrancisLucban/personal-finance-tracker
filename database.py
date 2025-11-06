import sqlite3

DB_NAME = "finance.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        type TEXT NOT NULL,         -- 'income' or 'expense'
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT
    )
    """)

    conn.commit()
    conn.close()
