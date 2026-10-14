def render_profile_link(name, url):
    # VULNERABLE: name and url are put into HTML without escaping
    return '<a href="' + url + '" title="' + name + '">' + name + "</a>"
