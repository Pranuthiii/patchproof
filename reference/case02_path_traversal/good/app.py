import os


def read_note(base_dir, name):
    base = os.path.realpath(base_dir)
    path = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, path]) != base:
        raise ValueError("path outside base_dir")
    with open(path) as f:
        return f.read()
