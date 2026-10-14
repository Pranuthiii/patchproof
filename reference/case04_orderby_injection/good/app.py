import sqlite3

ALLOWED_SORT_COLUMNS = {"id", "username", "email"}


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)"
    )
    conn.executemany(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        [
            ("alice", "zed@example.com"),
            ("bob", "amy@example.com"),
            ("carol", "mia@example.com"),
        ],
    )
    conn.commit()
    return conn


def list_users(conn, sort_by="username"):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ValueError("invalid sort column")
    query = "SELECT id, username, email FROM users ORDER BY " + sort_by
    return conn.execute(query).fetchall()
