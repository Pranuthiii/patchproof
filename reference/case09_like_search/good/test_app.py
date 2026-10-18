import unittest
from app import make_db, search_users


class TestSearchUsers(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()

    def names(self, rows):
        return [r[1] for r in rows]

    def test_partial_match(self):
        self.assertEqual(self.names(search_users(self.conn, "ali")), ["alice", "alina"])

    def test_exact_match(self):
        self.assertEqual(self.names(search_users(self.conn, "bob")), ["bob"])

    def test_case_insensitive(self):
        self.assertEqual(self.names(search_users(self.conn, "ALI")), ["alice", "alina"])

    def test_no_match(self):
        self.assertEqual(search_users(self.conn, "zzz"), [])

    def test_empty_term_returns_everyone(self):
        self.assertEqual(len(search_users(self.conn, "")), 4)


if __name__ == "__main__":
    unittest.main()
