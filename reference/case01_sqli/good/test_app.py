import unittest
from app import make_db, find_user


class TestFindUser(unittest.TestCase):
    def setUp(self):
        self.conn = make_db()

    def test_finds_existing_user(self):
        rows = find_user(self.conn, "alice")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "alice")

    def test_unknown_user_returns_nothing(self):
        self.assertEqual(find_user(self.conn, "nobody"), [])


if __name__ == "__main__":
    unittest.main()
