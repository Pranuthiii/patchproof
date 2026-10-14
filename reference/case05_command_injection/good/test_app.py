import os
import tempfile
import unittest
from app import count_lines


class TestCountLines(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_counts_lines(self):
        self.assertEqual(count_lines(self.write("a.txt", "one\ntwo\nthree\n")), 3)

    def test_empty_file_has_zero_lines(self):
        self.assertEqual(count_lines(self.write("b.txt", "")), 0)

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            count_lines(os.path.join(self.tmp.name, "missing.txt"))


if __name__ == "__main__":
    unittest.main()
