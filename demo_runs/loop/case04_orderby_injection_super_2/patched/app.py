import sqlite3


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
    # Whitelist allowed column names to prevent SQL injection
    allowed_columns = {"username", "email", "id"}
    if sort_by not in allowed_columns:
        sort_by = "username"
    query = f"SELECT id, username, email FROM users ORDER BY {sort_by}"
    return conn.execute(query).fetchall()
