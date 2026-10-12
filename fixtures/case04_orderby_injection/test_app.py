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


if __name__ == "__main__":
    unittest.main()
