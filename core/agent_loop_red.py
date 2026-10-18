"""PatchProof agent with feedback loops: retries test-writing and patching using
verifier output. The hidden oracle is only used for the final verdict."""
import shutil
import sys
from pathlib import Path

from patcher import FENCE, MODELS, client, extract_code
import os
TEMPERATURE = os.environ.get('PATCHPROOF_TEMPERATURE')
EXTRA = {'temperature': float(TEMPERATURE)} if TEMPERATURE else {}
from verifier import run_in_sandbox, verify

AI_TEST = "test_ai_security.py"
MAX_TEST_TRIES = 2
MAX_PATCH_TRIES = 3
MAX_RED_ROUNDS = 2
LOG_DIR = None


def ask(model, prompt, label):
    """Returns (code_or_None, truncated)."""
    r = client.chat.completions.create(
        model=model, max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
        **EXTRA,
    )
    choice = r.choices[0]
    print(f"[{label}] tokens: {r.usage.total_tokens} finish: {choice.finish_reason}")
    if LOG_DIR is not None:
        (LOG_DIR / f"raw_{label}.txt").write_text(
            f"finish_reason: {choice.finish_reason}\n\n{choice.message.content}\n")
    if choice.finish_reason == "length":
        print(f"[{label}] reply hit the token limit (not used)")
        return None, True
    return extract_code(choice.message.content), False


def main(case_dir, model_key):
    global LOG_DIR
    case = Path(case_dir)
    model = MODELS[model_key]
    base = Path("runs") / f"agent_{case.name}_{model_key}"
    if base.exists():
        shutil.rmtree(base)
    LOG_DIR = base
    orig, patched, oracle = base / "original", base / "patched", base / "oracle"

    # The hidden oracle test and the finding are kept out of the workspace.
    shutil.copytree(case, orig, ignore=shutil.ignore_patterns(
        "__pycache__", "test_security.py", "finding.txt"))
    finding = (case / "finding.txt").read_text()
    app = (orig / "app.py").read_text()
    normal_tests = (orig / "test_app.py").read_text()
    print("Model:", model)

    # ---- Loop 1: write an attack test that proves the flaw ----
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
    test_code, truncated, test_ok, feedback = None, False, False, ""
    for attempt in range(1, MAX_TEST_TRIES + 1):
        prompt = test_prompt
        if test_code and feedback:
            prompt += ("\n--- your previous test was rejected ---\n" + test_code +
                       "\n--- why ---\n" + feedback +
                       "\nWrite a corrected complete file in ONE " + FENCE + "python block.\n")
        test_code, truncated = ask(model, prompt, f"test-writer-{attempt}")
        if not test_code:
            feedback = ""
            continue
        (orig / AI_TEST).write_text(test_code)
        code, out = run_in_sandbox(orig, ["-v", "test_ai_security"])
        if code != 0 and "FAILED (failures=" in out:
            test_ok = True
            print(f"Test proves the flaw (attempt {attempt}).")
            break
        feedback = ("The test must fail with an assertion failure on the vulnerable "
                    "code, not pass and not crash. Output:\n" + out[-1200:])
        print(f"Test attempt {attempt} rejected.")
    if not test_ok:
        if truncated:
            sys.exit("TRUNCATED: test-writer ran out of tokens. NOT VERIFIED")
        if not test_code:
            sys.exit("No test returned. NOT VERIFIED.")
        sys.exit("TEST REJECTED after retries. NOT VERIFIED")

    # ---- Loop 2: write a patch, using verifier output as feedback ----
    patch_prompt = (
        "You are a security engineer. Fix the vulnerability in app.py so the "
        "failing security test passes and the existing tests still pass.\n\n"
        "Rules: change app.py only. Keep every function name and signature. "
        "Reply with the complete new app.py in ONE " + FENCE + "python block "
        "and nothing else.\n\n"
        f"--- finding ---\n{finding}\n"
        f"--- app.py ---\n{app}\n"
        f"--- {AI_TEST} ---\n{test_code}\n"
    )
    ai_ok, new_app, prev, feedback, truncated = False, None, "", "", False
    for attempt in range(1, MAX_PATCH_TRIES + 1):
        prompt = patch_prompt
        if prev:
            prompt += ("\n--- your previous patch (failed verification) ---\n" + prev +
                       "\n--- verifier output ---\n" + feedback +
                       "\nFix it. Reply with the complete new app.py in ONE " +
                       FENCE + "python block.\n")
        new_app, truncated = ask(model, prompt, f"patcher-{attempt}")
        if not new_app:
            continue
        if patched.exists():
            shutil.rmtree(patched)
        shutil.copytree(orig, patched)
        (patched / "app.py").write_text(new_app)  # only app.py is ever written
        ai_ok, checks = verify(orig, patched, "test_ai_security")
        if ai_ok:
            print(f"Patch passed the AI's checks (attempt {attempt}).")
            break
        prev = new_app
        feedback = "\n".join(
            f"FAILED CHECK: {name}\n{out[-1200:]}" for name, ok, out in checks if not ok)
        print(f"Patch attempt {attempt} failed verification.")
    if not ai_ok:
        if not prev:
            if truncated:
                sys.exit("TRUNCATED: patcher ran out of tokens. NOT VERIFIED")
            sys.exit("No patch returned. NOT VERIFIED.")
        print("\nVERDICT: NOT VERIFIED")
        return

    # ---- Loop 3: red team. A fresh call attacks the patched code ----
    red = base / "redteam"
    for rnd in range(1, MAX_RED_ROUNDS + 1):
        red_prompt = (
            "You are a penetration tester. A security patch was written for the finding below. "
            "Try to find inputs that STILL exploit the flaw despite the patch.\n\n"
            "Rules: write a unittest file using only the standard library; import what you need "
            "from app. Think about parser differences, alternate encodings, unusual but valid "
            "forms of the input, and edge cases the patch logic does not handle. Include one "
            "payload for each idea. Assert ONLY that attack inputs do not achieve the attack "
            "(for example are not returned, do not leak data, do not execute code). Do not "
            "assert anything about how legitimate inputs behave. Reply with the complete file "
            "in ONE " + FENCE + "python block and nothing else.\n\n"
            f"--- finding ---\n{finding}\n"
            f"--- patched app.py ---\n{new_app}\n"
            f"--- test already written (do not just repeat it) ---\n{test_code}\n"
        )
        red_code, _ = ask(model, red_prompt, f"red-team-{rnd}")
        if not red_code:
            break
        if red.exists():
            shutil.rmtree(red)
        shutil.copytree(patched, red)
        (red / "test_redteam.py").write_text(red_code)
        rcode, rout = run_in_sandbox(red, ["-v", "test_redteam"])
        if not (rcode != 0 and "FAILED (failures=" in rout):
            print(f"Red team found no bypass (round {rnd}).")
            break
        print(f"Red team found a bypass (round {rnd}); asking for a stronger patch.")
        fix_prompt = (
            patch_prompt
            + "\n--- your current patch (a red-team test breaks it) ---\n" + new_app
            + "\n--- red-team test ---\n" + red_code
            + "\n--- its output ---\n" + rout[-1500:]
            + "\nFix the patch so the red-team test passes too, without breaking the other "
            "tests. Reply with the complete new app.py in ONE " + FENCE + "python block.\n"
        )
        cand, _ = ask(model, fix_prompt, f"patcher-red-{rnd}")
        if not cand:
            break
        (patched / "app.py").write_text(cand)
        ok2, checks2 = verify(orig, patched, "test_ai_security")
        if ok2:
            shutil.rmtree(red)
            shutil.copytree(patched, red)
            (red / "test_redteam.py").write_text(red_code)
            rc2, _ = run_in_sandbox(red, ["test_redteam"])
            if rc2 == 0:
                new_app, checks = cand, checks2
                print(f"Stronger patch accepted (round {rnd}).")
                continue
        (patched / "app.py").write_text(new_app)
        print(f"Stronger patch rejected (round {rnd}); keeping the previous one.")
        break

    print("\n--- Patched app.py ---\n" + new_app)
    for name, ok, _ in checks:
        print(("PASS  " if ok else "FAIL  ") + name)

    # ---- Final check: the hidden oracle has the last word ----
    if oracle.exists():
        shutil.rmtree(oracle)
    shutil.copytree(patched, oracle)
    shutil.copy(case / "test_security.py", oracle / "test_security.py")
    ocode, _ = run_in_sandbox(oracle, ["test_security"])
    oracle_ok = ocode == 0
    print(("PASS  " if oracle_ok else "FAIL  ") + "Hidden oracle test (never shown to the AI)")
    if oracle_ok:
        print("\nVERDICT: VERIFIED (confirmed by the hidden oracle)")
    else:
        print("\nVERDICT: FALSE FIX (AI checks passed, but the real flaw remains)")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in MODELS:
        sys.exit("usage: python core/agent_loop.py CASE_DIR lightning|nano|super|ultra")
    main(sys.argv[1], sys.argv[2])
