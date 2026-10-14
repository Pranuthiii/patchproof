import subprocess


def count_lines(path):
    # VULNERABLE: path is pasted into a shell command that runs with shell=True
    result = subprocess.run("wc -l " + path, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise FileNotFoundError(path)
    return int(result.stdout.split()[0])
