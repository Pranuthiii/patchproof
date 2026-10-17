from urllib.parse import urlparse

ALLOWED_HOST = "example.com"


def safe_redirect_target(target, default="/"):
    # Validate that the target is either a relative URL or points to the allowed host.
    if not target:
        return default

    try:
        parsed = urlparse(target)
    except Exception:
        return default

    # Relative URL (no netloc) is safe.
    if not parsed.netloc:
        return target

    # Only allow URLs whose netloc matches the allowed host (case‑insensitive).
    if parsed.netloc.lower() == ALLOWED_HOST.lower():
        return target

    # Anything else is considered unsafe.
    return default
