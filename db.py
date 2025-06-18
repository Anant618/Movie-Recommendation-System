import sqlite3
from hashlib import sha256

DB_NAME = "users.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    name TEXT,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    email TEXT,
                    movie_title TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_user(name, email, password):
    hashed = sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", (email, name, hashed))
    conn.commit()
    conn.close()

def verify_user(email, password):
    hashed = sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE email=? AND password=?", (email, hashed))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def log_watch(email, movie_title):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO history (email, movie_title) VALUES (?, ?)", (email, movie_title))
    conn.commit()
    conn.close()

def get_watch_history(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT movie_title, timestamp FROM history WHERE email=? ORDER BY timestamp DESC", (email,))
    history = c.fetchall()
    conn.close()
    return history

