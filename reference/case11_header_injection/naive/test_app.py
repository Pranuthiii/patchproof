import unittest
from app import build_redirect_response


class TestBuildRedirectResponse(unittest.TestCase):
    def test_basic_response(self):
        out = build_redirect_response("/home", "abc123")
        self.assertEqual(
            out,
            "HTTP/1.1 302 Found\r\nLocation: /home\r\nSet-Cookie: session=abc123; HttpOnly\r\n\r\n",
        )

    def test_absolute_location_kept(self):
        out = build_redirect_response("https://example.com/a?b=1&c=2", "tok")
        self.assertIn("Location: https://example.com/a?b=1&c=2\r\n", out)

    def test_cookie_value_kept(self):
        out = build_redirect_response("/", "XyZ-789_ok")
        self.assertIn("Set-Cookie: session=XyZ-789_ok; HttpOnly\r\n", out)

    def test_ends_with_blank_line(self):
        self.assertTrue(build_redirect_response("/", "a").endswith("\r\n\r\n"))


if __name__ == "__main__":
    unittest.main()
