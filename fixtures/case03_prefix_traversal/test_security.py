import os
import tempfile
import unittest
from app import read_attachment

SECRET = "TOP-SECRET-DATA"


class TestPrefixTraversal(unittest.TestCase):
    def test_cannot_read_outside_base_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "files")
            sibling = os.path.join(tmp, "files_private")  # shares the "files" prefix
            os.makedirs(base)
            os.makedirs(sibling)
            outside = os.path.join(sibling, "secret.txt")
            with open(outside, "w") as f:
                f.write(SECRET)
            with open(os.path.join(tmp, "secret.txt"), "w") as f:
                f.write(SECRET)

            payloads = [
                "../secret.txt",
                "../files_private/secret.txt",
                outside,
            ]
            for payload in payloads:
                try:
                    result = read_attachment(base, payload)
                except Exception:
                    continue  # blocking with an error is fine
                self.assertNotIn(
                    SECRET, str(result),
                    f"Path traversal: payload {payload!r} leaked a file outside base_dir",
                )


if __name__ == "__main__":
    unittest.main()
