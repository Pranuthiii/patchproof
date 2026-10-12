import unittest
from app import make_db, list_users


class TestOrderByInjection(unittest.TestCase):
    def test_sort_by_cannot_run_arbitrary_sql(self):
        payloads = ["canary()", "username, canary()", "(SELECT canary())"]
        for payload in payloads:
            conn = make_db()
            calls = []
            # A harmless stand-in for attacker-chosen SQL. Safe code must never call it.
            conn.create_function("canary", 0, lambda: calls.append(1) or 1)
            try:
                list_users(conn, payload)
            except Exception:
                pass  # rejecting the input with an error is fine
            self.assertEqual(
                calls, [],
                f"SQL injection: sort_by={payload!r} executed attacker-supplied SQL",
            )


if __name__ == "__main__":
    unittest.main()
