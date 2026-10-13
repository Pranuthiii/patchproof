import os


def read_attachment(base_dir, filename):
    # VULNERABLE: filename is joined to base_dir without any checks
    path = os.path.join(base_dir, filename)
    with open(path) as f:
        return f.read()
