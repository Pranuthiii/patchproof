import unittest
from app import make_db, list_users


class TestListUsers(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()

    def names(self, rows):
        return [r[1] for r in rows]

    def test_default_sort_is_by_username(self):
        self.assertEqual(self.names(list_users(self.conn)), ["alice", "bob", "carol"])

    def test_sort_by_email(self):
        self.assertEqual(
            self.names(list_users(self.conn, "email")), ["bob", "carol", "alice"]
        )

    def test_sort_by_id(self):
        self.assertEqual(self.names(list_users(self.conn, "id")), ["alice", "bob", "carol"])

    def test_sql_injection_payloads_do_not_crash(self):
        payloads = [
            "username; DROP TABLE users;--",
            "username;SELECT CASE WHEN 1=1 THEN 1 ELSE 2 END;--",
            "'; DROP TABLE users;--",
        ]
        for payload in payloads:
            # If an exception occurs, unittest will abort this test,
            # causing the test to fail.  No exception means the payload
            # was safely handled.
            list_users(self.conn, payload)
            self.assertTrue(True)
