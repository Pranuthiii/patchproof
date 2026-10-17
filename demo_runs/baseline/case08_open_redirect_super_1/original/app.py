ALLOWED_HOST = "example.com"


def safe_redirect_target(target, default="/"):
    # VULNERABLE: any target is accepted, including other sites
    return target or default
