"""PatchProof agent (single-shot): the model writes the attack test, then the patch.
A hidden hand-written oracle test then checks whether the fix is real."""
import shutil
import sys
from pathlib import Path

from patcher import FENCE, MODELS, client, extract_code
from verifier import run_in_sandbox, verify

AI_TEST = "test_ai_security.py"


LOG_DIR = None


def ask(model, prompt, label):
    r = client.chat.completions.create(
        model=model, max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )
    choice = r.choices[0]
    print(f"[{label}] tokens: {r.usage.total_tokens} finish: {choice.finish_reason}")
    if LOG_DIR is not None:
        (LOG_DIR / f"raw_{label}.txt").write_text(
            f"finish_reason: {choice.finish_reason}\n\n{choice.message.content}\n")
    return extract_code(choice.message.content)


def main(case_dir, model_key):
    case = Path(case_dir)
    model = MODELS[model_key]
    base = Path("runs") / f"agent_{case.name}_{model_key}"
    if base.exists():
        shutil.rmtree(base)
    orig, patched, oracle = base / "original", base / "patched", base / "oracle"
    global LOG_DIR
    LOG_DIR = base

    # The hidden oracle test and the finding are kept out of the workspace.
    shutil.copytree(case, orig, ignore=shutil.ignore_patterns(
        "__pycache__", "test_security.py", "finding.txt"))
    finding = (case / "finding.txt").read_text()
    app = (orig / "app.py").read_text()
    normal_tests = (orig / "test_app.py").read_text()

    # Step 1: the model writes the attack test.
    print("Model:", model)
    test_code = ask(model, (
        "You are a security engineer. Write a unittest file that PROVES a "
        "vulnerability exists.\n\n"
        "Rules: use only the Python standard library and unittest. Import what "
        "you need from app. Use temporary directories for any files and clean "
        "them up. The test must FAIL on the current vulnerable code and PASS "
        "once the vulnerability is correctly fixed. Test the real attack, with "
        "more than one payload when sensible, and do not assert on error "
        "message text. Reply with the complete file in ONE " + FENCE +
        "python block and nothing else.\n\n"
        f"--- finding ---\n{finding}\n"
        f"--- app.py ---\n{app}\n"
        f"--- test_app.py (existing normal tests, for API reference) ---\n{normal_tests}\n"
    ), "test-writer")
    if not test_code:
        sys.exit("No test returned. NOT VERIFIED.")
    (orig / AI_TEST).write_text(test_code)
    print("\n--- AI-written test ---\n" + test_code)

    # Step 2: the test must fail on the original code.
    code, out = run_in_sandbox(orig, ["-v", "test_ai_security"])
    if not (code != 0 and "FAILED (failures=" in out):
        print("TEST REJECTED: it does not reproduce the flaw on the original code.")
        print(out[-600:])
        sys.exit("NOT VERIFIED")
    print("Test proves the flaw (fails on original code).\n")

    # Step 3: the model writes the patch.
    new_app = ask(model, (
        "You are a security engineer. Fix the vulnerability in app.py so the "
        "failing security test passes and the existing tests still pass.\n\n"
        "Rules: change app.py only. Keep every function name and signature. "
        "Reply with the complete new app.py in ONE " + FENCE + "python block "
        "and nothing else.\n\n"
        f"--- finding ---\n{finding}\n"
        f"--- app.py ---\n{app}\n"
        f"--- {AI_TEST} ---\n{test_code}\n"
        f"--- failing test output ---\n{out}\n"
    ), "patcher")
    if not new_app:
        sys.exit("No patch returned. NOT VERIFIED.")
    shutil.copytree(orig, patched)
    (patched / "app.py").write_text(new_app)  # only app.py is ever written
    print("\n--- Patched app.py ---\n" + new_app)

    # Step 4: verify with the AI's own test.
    ai_ok, checks = verify(orig, patched, "test_ai_security")
    for name, ok, _ in checks:
        print(("PASS  " if ok else "FAIL  ") + name)

    # Step 5: the hidden oracle (your hand-written test) has the final say.
    shutil.copytree(patched, oracle)
    shutil.copy(case / "test_security.py", oracle / "test_security.py")
    ocode, _ = run_in_sandbox(oracle, ["test_security"])
    oracle_ok = ocode == 0
    print(("PASS  " if oracle_ok else "FAIL  ") + "Hidden oracle test (never shown to the AI)")

    if ai_ok and oracle_ok:
        print("\nVERDICT: VERIFIED (confirmed by the hidden oracle)")
    elif ai_ok and not oracle_ok:
        print("\nVERDICT: FALSE FIX (AI checks passed, but the real flaw remains)")
    else:
        print("\nVERDICT: NOT VERIFIED")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in MODELS:
        sys.exit("usage: python core/agent.py CASE_DIR lightning|nano|super|ultra")
    main(sys.argv[1], sys.argv[2])
