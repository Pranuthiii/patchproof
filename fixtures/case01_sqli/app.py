import sqlite3


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)"
    )
    conn.executemany(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        [("alice", "alice@example.com"), ("bob", "bob@example.com")],
    )
    conn.commit()
    return conn


def find_user(conn, username):
    # VULNERABLE: username is pasted directly into the SQL text
    query = "SELECT id, username, email FROM users WHERE username = '" + username + "'"
    return conn.execute(query).fetchall()
