import os
import tempfile
import unittest
from app import read_note


class TestReadNote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.join(self.tmp.name, "notes")
        os.makedirs(self.base)
        with open(os.path.join(self.base, "hello.txt"), "w") as f:
            f.write("hi there")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_existing_note(self):
        self.assertEqual(read_note(self.base, "hello.txt"), "hi there")

    def test_missing_note_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            read_note(self.base, "missing.txt")


if __name__ == "__main__":
    unittest.main()
