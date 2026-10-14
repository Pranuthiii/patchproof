import os
import tempfile
import unittest
from app import read_note

SECRET = "TOP-SECRET-DATA"


class TestPathTraversal(unittest.TestCase):
    def test_cannot_read_files_outside_base_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "notes")
            os.makedirs(base)
            secret_path = os.path.join(tmp, "secret.txt")
            with open(secret_path, "w") as f:
                f.write(SECRET)

            # Two attacks: a relative escape and an absolute path.
            for payload in ["../secret.txt", secret_path]:
                try:
                    result = read_note(base, payload)
                except Exception:
                    continue  # blocking the attack with an error is fine
                self.assertNotIn(
                    SECRET, str(result),
                    f"Path traversal: payload {payload!r} leaked a file outside base_dir",
                )


if __name__ == "__main__":
    unittest.main()
