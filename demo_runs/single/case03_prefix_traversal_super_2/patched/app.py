import os


def read_attachment(base_dir, filename):
    # Resolve base directory to an absolute path
    base_dir = os.path.abspath(base_dir)
    # Construct the requested path and resolve it to an absolute path
    requested_path = os.path.abspath(os.path.join(base_dir, filename))
    # Ensure the requested path is within the base directory
    if not requested_path.startswith(base_dir):
        raise ValueError("Path traversal attempt detected")
    # Open and read the file
    with open(requested_path) as f:
        return f.read()
