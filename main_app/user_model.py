import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB = "../database/users.db"

def create_user_table():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()

def register_user(email, password):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    hashed = generate_password_hash(password)

    cur.execute("INSERT INTO users(email,password) VALUES(?,?)",(email,hashed))
    conn.commit()
    conn.close()

def validate_user(email,password):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT password FROM users WHERE email=?",(email,))
    row = cur.fetchone()
    conn.close()

    if row and check_password_hash(row[0],password):
        return True
    return False