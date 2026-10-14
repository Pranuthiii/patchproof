"""Baseline: one model call sees only app.py and the finding, writes a patch.
No AI-written test and no retries. Judged by the normal tests plus the hidden oracle."""
import os
import shutil
import sys
from pathlib import Path

from patcher import FENCE, MODELS, client, extract_code
from verifier import run_in_sandbox

TEMPERATURE = os.environ.get("PATCHPROOF_TEMPERATURE")
EXTRA = {"temperature": float(TEMPERATURE)} if TEMPERATURE else {}


def main(case_dir, model_key):
    case = Path(case_dir)
    model = MODELS[model_key]
    base = Path("runs") / f"agent_{case.name}_{model_key}"
    if base.exists():
        shutil.rmtree(base)
    orig, patched = base / "original", base / "patched"
    shutil.copytree(case, orig, ignore=shutil.ignore_patterns(
        "__pycache__", "test_security.py", "finding.txt"))
    finding = (case / "finding.txt").read_text()
    app = (orig / "app.py").read_text()

    prompt = (
        "You are a security engineer. Fix the vulnerability described below in app.py.\n\n"
        "Rules: change app.py only. Keep every function name and signature. "
        "Reply with the complete new app.py in ONE " + FENCE + "python block "
        "and nothing else.\n\n"
        f"--- finding ---\n{finding}\n--- app.py ---\n{app}\n"
    )
    print("Model:", model)
    r = client.chat.completions.create(
        model=model, max_tokens=16000,
        messages=[{"role": "user", "content": prompt}], **EXTRA)
    choice = r.choices[0]
    print(f"[baseline-patcher] tokens: {r.usage.total_tokens} finish: {choice.finish_reason}")
    base.mkdir(parents=True, exist_ok=True)
    (base / "raw_baseline.txt").write_text(
        f"finish_reason: {choice.finish_reason}\n\n{choice.message.content}\n")
    if choice.finish_reason == "length":
        sys.exit("TRUNCATED: baseline reply hit the token limit. NOT VERIFIED")
    new_app = extract_code(choice.message.content)
    if not new_app:
        sys.exit("No patch returned. NOT VERIFIED.")

    shutil.copytree(orig, patched)
    (patched / "app.py").write_text(new_app)
    # Judge with the normal tests and the hidden oracle, copied in only now.
    shutil.copy(case / "test_security.py", patched / "test_security.py")
    code_n, _ = run_in_sandbox(patched, ["test_app"])
    code_s, _ = run_in_sandbox(patched, ["test_security"])
    print(("PASS  " if code_n == 0 else "FAIL  ") + "Normal tests")
    print(("PASS  " if code_s == 0 else "FAIL  ") + "Hidden oracle test")
    if code_n == 0 and code_s == 0:
        print("\nVERDICT: VERIFIED (confirmed by the hidden oracle)")
    elif code_n == 0:
        print("\nVERDICT: FALSE FIX (unverified patch passed the normal tests but the flaw remains)")
    else:
        print("\nVERDICT: NOT VERIFIED")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in MODELS:
        sys.exit("usage: python core/agent_baseline.py CASE_DIR lightning|nano|super|ultra")
    main(sys.argv[1], sys.argv[2])
