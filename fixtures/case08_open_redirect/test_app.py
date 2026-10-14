import unittest
from app import safe_redirect_target


class TestSafeRedirectTarget(unittest.TestCase):
    def test_relative_path_is_kept(self):
        self.assertEqual(safe_redirect_target("/dashboard"), "/dashboard")

    def test_same_site_absolute_url_is_kept(self):
        self.assertEqual(
            safe_redirect_target("https://example.com/account"),
            "https://example.com/account",
        )

    def test_empty_target_uses_default(self):
        self.assertEqual(safe_redirect_target(""), "/")

    def test_custom_default(self):
        self.assertEqual(safe_redirect_target("", default="/home"), "/home")


if __name__ == "__main__":
    unittest.main()
