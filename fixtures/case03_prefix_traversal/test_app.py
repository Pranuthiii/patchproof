import os
import tempfile
import unittest
from app import read_attachment


class TestReadAttachment(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = os.path.join(self.tmp.name, "files")
        os.makedirs(os.path.join(self.base, "sub"))
        with open(os.path.join(self.base, "a.txt"), "w") as f:
            f.write("alpha")
        with open(os.path.join(self.base, "sub", "b.txt"), "w") as f:
            f.write("beta")

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_top_level_file(self):
        self.assertEqual(read_attachment(self.base, "a.txt"), "alpha")

    def test_reads_file_in_subfolder(self):
        self.assertEqual(read_attachment(self.base, os.path.join("sub", "b.txt")), "beta")

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            read_attachment(self.base, "missing.txt")


if __name__ == "__main__":
    unittest.main()
