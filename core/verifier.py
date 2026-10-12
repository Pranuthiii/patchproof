"""PatchProof verifier: decides whether a patch is VERIFIED, using only test results."""
import hashlib
import subprocess
import sys
from pathlib import Path

IMAGE = "python:3.11-slim"


def run_in_sandbox(folder, unittest_args):
    """Run unittest inside a locked Docker box: no network, read-only code, limits."""
    cmd = [
        "docker", "run", "--rm", "--network", "none",
        "--memory", "256m", "--cpus", "1",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-v", f"{Path(folder).resolve()}:/work:ro", "-w", "/work",
        IMAGE, "python", "-m", "unittest", *unittest_args,
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT: tests took longer than 60 seconds"


def test_hashes(folder):
    """Fingerprint every test_*.py file so tampering can be detected."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(Path(folder).glob("test_*.py"))
    }


def verify(original_dir, patched_dir, security_module="test_security"):
    checks = []

    same = test_hashes(original_dir) == test_hashes(patched_dir)
    checks.append(("Test files unchanged by the patch", same, ""))

    code, out = run_in_sandbox(original_dir, ["-v", security_module])
    flaw = code != 0 and "FAILED (failures=" in out
    checks.append(("Security test FAILS on original code (flaw proven)", flaw, out))

    code, out = run_in_sandbox(patched_dir, ["-v", security_module])
    fixed = code == 0 and "OK" in out
    checks.append(("Security test PASSES on patched code", fixed, out))

    code, out = run_in_sandbox(patched_dir, ["-v"])
    suite = code == 0 and "OK" in out
    checks.append(("Full test suite PASSES on patched code", suite, out))

    return all(ok for _, ok, _ in checks), checks


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python core/verifier.py ORIGINAL_DIR PATCHED_DIR")
    verified, checks = verify(sys.argv[1], sys.argv[2])
    for name, ok, _ in checks:
        print(("PASS  " if ok else "FAIL  ") + name)
    print("\nVERDICT:", "VERIFIED" if verified else "NOT VERIFIED")
    sys.exit(0 if verified else 1)
