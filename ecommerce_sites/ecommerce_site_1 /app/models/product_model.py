import sqlite3
import os

# ✅ Base directory (safe for Render)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ Ensure database folder exists
DB_FOLDER = os.path.join(BASE_DIR, "database")
os.makedirs(DB_FOLDER, exist_ok=True)

# ✅ Database path
DB_PATH = os.path.join(DB_FOLDER, "database2.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                discount INTEGER,
                availability TEXT
            )
        """)

        conn.commit()
        conn.close()

    except Exception as e:
        print("Create table error:", e)


def add_rating_column():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("ALTER TABLE products ADD COLUMN rating REAL DEFAULT 0")

        conn.commit()
        conn.close()

    except Exception:
        # Column already exists
        pass