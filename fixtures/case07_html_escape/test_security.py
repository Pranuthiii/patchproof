import unittest
from html.parser import HTMLParser
from app import render_profile_link


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, [k for k, _ in attrs], dict(attrs)))


class TestHtmlInjection(unittest.TestCase):
    def parse(self, name, url):
        c = Collector()
        c.feed(render_profile_link(name, url))
        return c.tags

    def test_name_cannot_break_out(self):
        payloads = [
            '" onmouseover="alert(1)',
            '"><script>alert(1)</script>',
            "x\" autofocus onfocus=\"alert(1)",
            "</a><img src=x onerror=alert(1)>",
        ]
        for name in payloads:
            tags = self.parse(name, "https://example.com/u")
            self.assertEqual([t[0] for t in tags], ["a"],
                             f"HTML injection: name {name!r} created extra elements")
            self.assertEqual(sorted(tags[0][1]), ["href", "title"],
                             f"HTML injection: name {name!r} added attributes")

    def test_url_cannot_break_out_or_use_script_scheme(self):
        payloads = [
            'https://example.com/" onclick="alert(1)',
            'https://example.com/"><script>alert(1)</script>',
        ]
        for url in payloads:
            tags = self.parse("Alice", url)
            self.assertEqual([t[0] for t in tags], ["a"],
                             f"HTML injection: url {url!r} created extra elements")
            self.assertEqual(sorted(tags[0][1]), ["href", "title"],
                             f"HTML injection: url {url!r} added attributes")
        tags = self.parse("Alice", "javascript:alert(1)")
        href = tags[0][2].get("href", "")
        self.assertFalse(href.strip().lower().startswith("javascript:"),
                         "HTML injection: javascript: URL was accepted")


if __name__ == "__main__":
    unittest.main()
