from urllib.parse import urlparse

ALLOWED_HOST = "example.com"


def safe_redirect_target(target, default="/"):
    if not target:
        return default
    if "\\" in target or any(ord(c) < 32 for c in target):
        return default
    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme in ("http", "https") and parsed.hostname == ALLOWED_HOST \
                and parsed.username is None and target.startswith(parsed.scheme + "://"):
            return target
        return default
    if target.startswith("/") and not target.startswith("//"):
        return target
    return default
