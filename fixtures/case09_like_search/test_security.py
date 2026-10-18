import unittest
from app import make_db, search_users


class TestLikeInjection(unittest.TestCase):
    def test_term_cannot_change_the_query(self):
        payloads = [
            "' OR '1'='1",
            "zzz' UNION SELECT id, token, token FROM secrets --",
            "zzz%' OR canary()=1 --",
            "zzz' OR 1=1 --",
        ]
        for payload in payloads:
            conn = make_db()
            calls = []
            conn.create_function("canary", 0, lambda: calls.append(1) or 1)
            try:
                rows = search_users(conn, payload)
            except Exception:
                rows = []  # rejecting the input with an error is fine
            self.assertEqual(rows, [], f"SQL injection: term {payload!r} returned rows")
            self.assertEqual(calls, [], f"SQL injection: term {payload!r} ran attacker SQL")


if __name__ == "__main__":
    unittest.main()
