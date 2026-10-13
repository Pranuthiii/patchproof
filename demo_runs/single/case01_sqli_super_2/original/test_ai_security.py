import unittest
from app import make_db, find_user

class TestSQLInjection(unittest.TestCase):
    def setUp(self):
        # Use the existing in-memory database creator
        self.conn = make_db()

    def test_sql_injection_is_prevented(self):
        # Payloads that would cause the vulnerable query to return extra rows
        injection_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' UNION SELECT id, username, email FROM users --",
        ]

        for payload in injection_payloads:
            with self.subTest(payload=payload):
                rows = find_user(self.conn, payload)
                # If the code is vulnerable, rows will contain data (e.g., both alice and bob)
                # After fixing with parameterized queries, no user matches the literal payload,
                # so the result should be an empty list.
                self.assertEqual(
                    rows,
                    [],
                    f"SQL injection succeeded with payload: {payload!r}"
                )

if __name__ == "__main__":
    unittest.main()
