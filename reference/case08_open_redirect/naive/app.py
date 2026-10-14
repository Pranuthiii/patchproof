ALLOWED_HOST = "example.com"


def safe_redirect_target(target, default="/"):
    if not target:
        return default
    if target.startswith("/") or target.startswith("https://" + ALLOWED_HOST):
        return target
    return default
