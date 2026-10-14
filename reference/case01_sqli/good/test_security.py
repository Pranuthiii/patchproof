import unittest
from app import make_db, find_user


class TestSqlInjection(unittest.TestCase):
    def test_injection_payload_returns_no_rows(self):
        conn = make_db()
        # A crafted "username" that tries to change the meaning of the query.
        payload = "nobody' OR '1'='1"
        rows = find_user(conn, payload)
        # Safe code treats the payload as a plain name, finds nobody, returns [].
        self.assertEqual(rows, [], "SQL injection: payload returned rows")


if __name__ == "__main__":
    unittest.main()
