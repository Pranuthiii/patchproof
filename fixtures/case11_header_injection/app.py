def build_redirect_response(location, cookie_value):
    # VULNERABLE: values are placed into raw header lines without any checks
    return ("HTTP/1.1 302 Found\r\n"
            "Location: " + location + "\r\n"
            "Set-Cookie: session=" + cookie_value + "; HttpOnly\r\n"
            "\r\n")
