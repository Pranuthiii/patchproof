import unittest
from app import parse_setting


class TestParseSetting(unittest.TestCase):
    def test_parses_int(self):
        self.assertEqual(parse_setting("42"), 42)

    def test_parses_float(self):
        self.assertEqual(parse_setting("3.5"), 3.5)

    def test_parses_list(self):
        self.assertEqual(parse_setting("[1, 2, 3]"), [1, 2, 3])

    def test_parses_dict(self):
        self.assertEqual(parse_setting("{'a': 1, 'b': [2, 3]}"), {"a": 1, "b": [2, 3]})

    def test_parses_string(self):
        self.assertEqual(parse_setting("'hello'"), "hello")

    def test_parses_bool_and_none(self):
        self.assertEqual(parse_setting("[True, False, None]"), [True, False, None])


if __name__ == "__main__":
    unittest.main()
