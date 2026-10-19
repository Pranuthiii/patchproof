def _clean(value):
    if any(c in value for c in "\r\n\x00"):
        raise ValueError("invalid characters in header value")
    return value


def build_redirect_response(location, cookie_value):
    return ("HTTP/1.1 302 Found\r\n"
            "Location: " + _clean(location) + "\r\n"
            "Set-Cookie: session=" + _clean(cookie_value) + "; HttpOnly\r\n"
            "\r\n")
