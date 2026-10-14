import unittest
from app import render_profile_link


class TestRenderProfileLink(unittest.TestCase):
    def test_plain_name_and_url(self):
        self.assertEqual(
            render_profile_link("Alice", "https://example.com/alice"),
            '<a href="https://example.com/alice" title="Alice">Alice</a>',
        )

    def test_name_with_spaces(self):
        self.assertEqual(
            render_profile_link("Bob Smith", "https://example.com/b"),
            '<a href="https://example.com/b" title="Bob Smith">Bob Smith</a>',
        )

    def test_url_with_path_is_kept(self):
        out = render_profile_link("Carol", "https://example.com/people/carol")
        self.assertIn('href="https://example.com/people/carol"', out)


if __name__ == "__main__":
    unittest.main()
