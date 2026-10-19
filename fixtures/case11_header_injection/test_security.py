import re
import unittest
from app import build_redirect_response


def parse(raw):
    lines = re.split(r"\r\n|\r|\n", raw)
    rest = lines[1:]
    headers, body, in_body = [], [], False
    for line in rest:
        if in_body:
            body.append(line)
        elif line == "":
            in_body = True
        else:
            headers.append(line)
    names = [h.split(":", 1)[0].strip().lower() for h in headers if ":" in h]
    bad_lines = [h for h in headers if ":" not in h]
    return names, bad_lines, "".join(body)


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
