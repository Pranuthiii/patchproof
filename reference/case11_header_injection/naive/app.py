def build_redirect_response(location, cookie_value):
    location = location.replace("\r\n", "")
    cookie_value = cookie_value.replace("\r\n", "")
    return ("HTTP/1.1 302 Found\r\n"
            "Location: " + location + "\r\n"
            "Set-Cookie: session=" + cookie_value + "; HttpOnly\r\n"
            "\r\n")
