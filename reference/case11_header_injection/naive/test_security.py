import unittest
from app import build_redirect_response


def parse(raw):
    head, sep, body = raw.partition("\r\n\r\n")
    lines = head.split("\r\n")
    names = [l.split(":", 1)[0].strip().lower() for l in lines[1:] if ":" in l]
    bad_lines = [l for l in lines[1:] if ":" not in l]
    return names, bad_lines, body


class TestHeaderInjection(unittest.TestCase):
    def check(self, location, cookie, label):
        try:
            raw = build_redirect_response(location, cookie)
        except Exception:
            return  # rejecting the input with an error is fine
        names, bad_lines, body = parse(raw)
        self.assertEqual(sorted(names), ["location", "set-cookie"],
                         f"Header injection: {label} added or removed headers")
        self.assertEqual(bad_lines, [], f"Header injection: {label} produced a malformed header line")
        self.assertEqual(body, "", f"Header injection: {label} added a response body")

    def test_location_cannot_inject(self):
        payloads = [
            "/x\r\nSet-Cookie: admin=1",
            "/x\nX-Injected: 1",
            "/x\rX-Injected: 1",
            "/x\r\n\r\n<script>alert(1)</script>",
        ]
        for p in payloads:
            self.check(p, "abc", "location " + repr(p))

    def test_cookie_cannot_inject(self):
        payloads = [
            "abc\r\nX-Injected: 1",
            "abc\nSet-Cookie: admin=1",
            "abc\r\n\r\nbody",
        ]
        for p in payloads:
            self.check("/ok", p, "cookie " + repr(p))


if __name__ == "__main__":
    unittest.main()
