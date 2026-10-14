def render_profile_link(name, url):
    def esc(s):
        return s.replace("<", "&lt;").replace(">", "&gt;")
    return '<a href="' + esc(url) + '" title="' + esc(name) + '">' + esc(name) + "</a>"
