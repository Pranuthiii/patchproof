import html
from urllib.parse import urlparse


def render_profile_link(name, url):
    if urlparse(url.strip()).scheme.lower() not in ("http", "https", ""):
        url = "#"
    return (
        '<a href="' + html.escape(url, quote=True)
        + '" title="' + html.escape(name, quote=True) + '">'
        + html.escape(name, quote=True) + "</a>"
    )
