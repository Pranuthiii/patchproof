import os


def read_note(base_dir, name):
    if ".." in name:
        raise ValueError("bad name")
    path = os.path.join(base_dir, name)
    with open(path) as f:
        return f.read()
