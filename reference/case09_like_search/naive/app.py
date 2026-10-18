import sqlite3


def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)")
    conn.execute("CREATE TABLE secrets (id INTEGER PRIMARY KEY, token TEXT)")
    conn.executemany(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        [
            ("alice", "alice@example.com"),
            ("alina", "alina@example.com"),
            ("bob", "bob@example.com"),
            ("carol", "carol@example.com"),
        ],
    )
    conn.execute("INSERT INTO secrets (token) VALUES ('S3CRET-TOKEN')")
    conn.commit()
    return conn


def search_users(conn, term):
    lowered = term.lower()
    if any(w in lowered for w in ("union", "select", ";", "--")):
        raise ValueError("bad search term")
    query = ("SELECT id, username, email FROM users WHERE username LIKE '%"
             + term + "%' ORDER BY id")
    return conn.execute(query).fetchall()
