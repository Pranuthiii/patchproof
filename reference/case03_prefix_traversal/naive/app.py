import os


def read_attachment(base_dir, filename):
    base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base, filename))
    if not path.startswith(base):
        raise ValueError("path outside base_dir")
    with open(path) as f:
        return f.read()
