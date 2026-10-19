import os
import tempfile
import unittest
import zipfile
from app import extract_zip


class TestExtractZip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.zip_path = os.path.join(self.tmp.name, "a.zip")
        self.dest = os.path.join(self.tmp.name, "out")

    def tearDown(self):
        self.tmp.cleanup()

    def make_zip(self, entries):
        with zipfile.ZipFile(self.zip_path, "w") as zf:
            for name, data in entries:
                zf.writestr(name, data)

    def test_extracts_files(self):
        self.make_zip([("a.txt", "alpha"), ("sub/b.txt", "beta")])
        names = extract_zip(self.zip_path, self.dest)
        self.assertEqual(sorted(names), ["a.txt", "sub/b.txt"])
        with open(os.path.join(self.dest, "a.txt")) as f:
            self.assertEqual(f.read(), "alpha")
        with open(os.path.join(self.dest, "sub", "b.txt")) as f:
            self.assertEqual(f.read(), "beta")

    def test_empty_archive(self):
        self.make_zip([])
        self.assertEqual(extract_zip(self.zip_path, self.dest), [])

    def test_directory_entries_are_created(self):
        self.make_zip([("docs/", ""), ("docs/readme.txt", "hi")])
        extract_zip(self.zip_path, self.dest)
        self.assertTrue(os.path.isdir(os.path.join(self.dest, "docs")))
        self.assertTrue(os.path.isfile(os.path.join(self.dest, "docs", "readme.txt")))

    def test_missing_archive_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract_zip(os.path.join(self.tmp.name, "missing.zip"), self.dest)


if __name__ == "__main__":
    unittest.main()
