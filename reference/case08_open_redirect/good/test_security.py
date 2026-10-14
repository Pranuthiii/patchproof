import unittest
from app import safe_redirect_target


class TestOpenRedirect(unittest.TestCase):
    def test_external_targets_are_rejected(self):
        payloads = [
            "https://evil.test/",
            "//evil.test/",
            "https://example.com.evil.test/",
            "https://example.com@evil.test/",
            "https://evil.test/?next=https://example.com",
            "///evil.test/",
            "/\\evil.test",
            "javascript:alert(1)",
            "https:evil.test",
        ]
        for payload in payloads:
            self.assertEqual(
                safe_redirect_target(payload, default="/fallback"), "/fallback",
                f"Open redirect: target {payload!r} was accepted",
            )

    def test_legitimate_targets_are_kept(self):
        for target in ["/a/b?x=1", "https://example.com/p", "http://example.com/"]:
            self.assertEqual(safe_redirect_target(target, default="/fallback"), target)


if __name__ == "__main__":
    unittest.main()
