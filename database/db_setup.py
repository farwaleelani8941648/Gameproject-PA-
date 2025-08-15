import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "game_data.db")

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Users table (already exists)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Improved saves table for MULTIPLE saves per user, progress tracking, and timestamp
    c.execute("""
        CREATE TABLE IF NOT EXISTS saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            level INTEGER,
            resources TEXT,
            grid TEXT,
            level1_start TEXT,
            level2_start TEXT,
            save_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database, users and saves table created!")
