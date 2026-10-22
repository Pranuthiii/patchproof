"""Hybrid agent. Starts from a one-shot patch (retried only if the existing tests fail), then uses an
AI-written attack test as extra evidence. A patch that passes the existing tests is never discarded just
because the AI test is missing or unusable. The hidden oracle is used only for the final verdict."""
import os
import shutil
import sys
from pathlib import Path

from patcher import FENCE, MODELS, client, extract_code
from verifier import run_in_sandbox

TEMPERATURE = os.environ.get("PATCHPROOF_TEMPERATURE")
EXTRA = {"temperature": float(TEMPERATURE)} if TEMPERATURE else {}
AI_TEST = "test_ai_security.py"
MAX_PATCH_TRIES = 3
MAX_TEST_TRIES = 2
MAX_FIX_TRIES = 2
LOG_DIR = None


def ask(model, prompt, label):
    """Returns (code_or_None, truncated)."""
    r = client.chat.completions.create(
        model=model, max_tokens=16000,
        messages=[{"role": "user", "content": prompt}], **EXTRA)
    choice = r.choices[0]
    print(f"[{label}] tokens: {r.usage.total_tokens} finish: {choice.finish_reason}")
    if LOG_DIR is not None:
        (LOG_DIR / f"raw_{label}.txt").write_text(
            f"finish_reason: {choice.finish_reason}\n\n{choice.message.content}\n")
    if choice.finish_reason == "length":
        print(f"[{label}] reply hit the token limit (not used)")
        return None, True
    return extract_code(choice.message.content), False


def passes(folder, module):
    code, out = run_in_sandbox(folder, ["-v", module])
    return code == 0, out


def main(case_dir, model_key):
    global LOG_DIR
    case = Path(case_dir)
    model = MODELS[model_key]
    base = Path("runs") / f"agent_{case.name}_{model_key}"
    if base.exists():
        shutil.rmtree(base)
    LOG_DIR = base
    orig, patched, oracle = base / "original", base / "patched", base / "oracle"
    shutil.copytree(case, orig, ignore=shutil.ignore_patterns(
        "__pycache__", "test_security.py", "finding.txt"))
    finding = (case / "finding.txt").read_text()
    app = (orig / "app.py").read_text()
    normal_tests = (orig / "test_app.py").read_text()
    print("Model:", model)

    # Stage 1: one-shot patch, retried only while the existing tests fail.
    patch_prompt = (
        "You are a security engineer. Fix the vulnerability described below in app.py.\n\n"
        "Rules: change app.py only. Keep every function name and signature. "
        "Reply with the complete new app.py in ONE " + FENCE + "python block and nothing else.\n\n"
        f"--- finding ---\n{finding}\n--- app.py ---\n{app}\n"
    )
    shutil.copytree(orig, patched)
    best, prev, feedback, truncated = None, None, "", False
    for attempt in range(1, MAX_PATCH_TRIES + 1):
        prompt = patch_prompt
        if prev:
            prompt += ("\n--- your previous patch (it fails the existing tests) ---\n" + prev
                       + "\n--- test output ---\n" + feedback
                       + "\nFix it. Reply with the complete new app.py in ONE " + FENCE + "python block.\n")
        cand, truncated = ask(model, prompt, f"patcher-{attempt}")
        if not cand:
            continue
        (patched / "app.py").write_text(cand)
        ok, out = passes(patched, "test_app")
        if ok:
            best = cand
            break
        prev, feedback = cand, out[-1200:]
        print(f"Patch attempt {attempt} fails the existing tests.")
    if best is None:
        if truncated:
            sys.exit("TRUNCATED: patcher ran out of tokens. NOT VERIFIED")
        if prev is None:
            sys.exit("No patch returned. NOT VERIFIED.")
        print("TIER: failed")
        print("\nVERDICT: NOT VERIFIED")
        return

    # Stage 2: an AI-written attack test, used as extra evidence only.
    test_prompt = (
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
    )
    tier, t_code, tfeedback, test_ok = "unproven", None, "", False
    for attempt in range(1, MAX_TEST_TRIES + 1):
        prompt = test_prompt
        if t_code and tfeedback:
            prompt += ("\n--- your previous test was rejected ---\n" + t_code
                       + "\n--- why ---\n" + tfeedback
                       + "\nWrite a corrected complete file in ONE " + FENCE + "python block.\n")
        t_code, _ = ask(model, prompt, f"test-writer-{attempt}")
        if not t_code:
            tfeedback = ""
            continue
        (orig / AI_TEST).write_text(t_code)
        code, out = run_in_sandbox(orig, ["-v", "test_ai_security"])
        if code != 0 and "FAILED (failures=" in out:
            test_ok = True
            break
        tfeedback = ("The test must fail with an assertion failure on the vulnerable code, "
                     "not pass and not crash. Output:\n" + out[-1200:])
        print(f"Test attempt {attempt} rejected.")

    # Stage 3: compare the patch with the AI test. Replace the patch only on clear improvement.
    if test_ok:
        (patched / AI_TEST).write_text(t_code)
        ok, out = passes(patched, "test_ai_security")
        if ok:
            tier = "verified"
        else:
            tier = "contested"
            for attempt in range(1, MAX_FIX_TRIES + 1):
                fix_prompt = (patch_prompt
                              + "\n--- your current patch (an attack test breaks it) ---\n" + best
                              + "\n--- attack test ---\n" + t_code
                              + "\n--- its output ---\n" + out[-1500:]
                              + "\nFix the patch so this test passes and the existing tests still pass. "
                              "Reply with the complete new app.py in ONE " + FENCE + "python block.\n")
                cand, _ = ask(model, fix_prompt, f"patcher-fix-{attempt}")
                if not cand:
                    break
                (patched / "app.py").write_text(cand)
                ok_n, _ = passes(patched, "test_app")
                ok_t, out = passes(patched, "test_ai_security")
                if ok_n and ok_t:
                    best, tier = cand, "verified"
                    break
                print(f"Fix attempt {attempt} rejected.")

    # Stage 4: the hidden oracle gives the final verdict.
    (patched / "app.py").write_text(best)
    if oracle.exists():
        shutil.rmtree(oracle)
    shutil.copytree(patched, oracle)
    shutil.copy(case / "test_security.py", oracle / "test_security.py")
    n_ok, _ = passes(oracle, "test_app")
    o_ok, _ = passes(oracle, "test_security")
    print("TIER:", tier)
    print(("PASS  " if n_ok else "FAIL  ") + "Existing tests")
    print(("PASS  " if o_ok else "FAIL  ") + "Hidden oracle test (never shown to the AI)")
    if n_ok and o_ok:
        print("\nVERDICT: VERIFIED (confirmed by the hidden oracle)")
    elif n_ok:
        print("\nVERDICT: FALSE FIX (existing tests pass but the real flaw remains)")
    else:
        print("\nVERDICT: NOT VERIFIED")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in MODELS:
        sys.exit("usage: python core/agent_hybrid.py CASE_DIR lightning|nano|super|ultra")
    main(sys.argv[1], sys.argv[2])
