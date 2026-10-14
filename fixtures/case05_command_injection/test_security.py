import os
import tempfile
import unittest
from app import count_lines


class TestCommandInjection(unittest.TestCase):
    def test_path_cannot_run_shell_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            real = os.path.join(tmp, "data.txt")
            with open(real, "w") as f:
                f.write("a\nb\n")
            marker = os.path.join(tmp, "pwned")
            payloads = [
                f"{real}; touch {marker}",
                f"{real} && touch {marker}",
                f"{real} | touch {marker}",
                f"$(touch {marker})",
                f"`touch {marker}`",
                f"{real}\ntouch {marker}",
            ]
            for payload in payloads:
                try:
                    count_lines(payload)
                except Exception:
                    pass  # rejecting the input with an error is fine
                self.assertFalse(
                    os.path.exists(marker),
                    f"Command injection: payload {payload!r} ran a shell command",
                )


if __name__ == "__main__":
    unittest.main()
