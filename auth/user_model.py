import sqlite3
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), "../database/game_data.db")

def register_user(username, email, password):
    """
    Registers a new user.
    Returns (True, message) on success, (False, error_message) on failure.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                  (username, email, password))
        conn.commit()
        conn.close()
        return True, "Registration successful!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, f"Error: {e}"

def login_user(username, password):
    """
    Checks login credentials.
    Returns (True, user_row) if correct, (False, error_message) if not.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return True, user
    else:
        return False, "Incorrect username or password."

def get_user_by_username(username):
    """
    Returns the user row (or None) for a given username.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user
