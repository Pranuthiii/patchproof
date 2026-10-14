import subprocess


def count_lines(path):
    result = subprocess.run(["wc", "-l", "--", path], capture_output=True, text=True)
    if result.returncode != 0:
        raise FileNotFoundError(path)
    return int(result.stdout.split()[0])
