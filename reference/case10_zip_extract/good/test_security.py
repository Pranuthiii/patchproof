import os
import tempfile
import unittest
import zipfile
from app import extract_zip


class TestZipSlip(unittest.TestCase):
    def outside_files(self, tmp, dest, zip_path):
        found = []
        for root, _, files in os.walk(tmp):
            for name in files:
                path = os.path.join(root, name)
                if path != zip_path and not path.startswith(dest + os.sep):
                    found.append(path)
        return found

    def test_entries_cannot_write_outside_dest(self):
        with tempfile.TemporaryDirectory() as probe:
            absolute = os.path.join(probe, "abs_evil.txt")
        payloads = ["../evil.txt", "a/../../evil2.txt", "../out_evil/x.txt", absolute]
        for payload in payloads:
            with tempfile.TemporaryDirectory() as tmp:
                zip_path = os.path.join(tmp, "a.zip")
                dest = os.path.join(tmp, "out")
                name = payload
                if payload == absolute:
                    name = os.path.join(tmp, "abs_evil.txt")
                with zipfile.ZipFile(zip_path, "w") as zf:
                    zf.writestr("ok.txt", "fine")
                    zf.writestr(name, "pwned")
                try:
                    extract_zip(zip_path, dest)
                except Exception:
                    pass  # rejecting the archive with an error is fine
                outside = self.outside_files(tmp, dest, zip_path)
                self.assertEqual(outside, [], f"Zip slip: entry {payload!r} wrote outside dest_dir")


if __name__ == "__main__":
    unittest.main()
