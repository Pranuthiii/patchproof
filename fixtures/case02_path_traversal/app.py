import os


def read_note(base_dir, name):
    # VULNERABLE: the file name is joined to the folder without any checks
    path = os.path.join(base_dir, name)
    with open(path) as f:
        return f.read()
