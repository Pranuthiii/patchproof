import subprocess


def count_lines(path):
    if ";" in path:
        raise ValueError("bad path")
    result = subprocess.run("wc -l " + path, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise FileNotFoundError(path)
    return int(result.stdout.split()[0])
