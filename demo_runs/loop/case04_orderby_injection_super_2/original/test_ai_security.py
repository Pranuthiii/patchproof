import unittest
from app import make_db, list_users

class TestSQLInjection(unittest.TestCase):
    def setUp(self):
        # Create an in-memory database for each test.
        self.conn = make_db()

    def _get_usernames(self, rows):
        """Helper to extract usernames from query result rows."""
        return [row[1] for row in rows]

    def test_order_by_injection_is_prevented(self):
        # If the sort_by parameter is directly concatenated into the ORDER BY clause,
        # supplying a value like "username DESC" will change the sort order.
        # A fixed implementation should restrict sort_by to a whitelist of safe column
        # names (e.g., only "username", "email", "id") and ignore or safely handle
        # any other input, thus preserving the default ascending username order.
        rows = list_users(self.conn, "username DESC")
        usernames = self._get_usernames(rows)
        # Expected order when injection is prevented (or input is sanitized):
        self.assertEqual(usernames, ["alice", "bob", "carol"])

if __name__ == "__main__":
    unittest.main()
