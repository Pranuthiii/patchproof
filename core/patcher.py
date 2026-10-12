"""Single-shot patcher: ask a Nemotron model to fix app.py, then verify the result."""
import ast
import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from verifier import run_in_sandbox, verify

load_dotenv()
FENCE = "`" * 3
MODELS = {
    "lightning": "nvidia/Nemotron-3_5-Lightning",
    "nano": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    "super": "nvidia/nemotron-3-super-120b-a12b",
    "ultra": "nvidia/Nemotron-3-Ultra-550b-a55b",
}

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY"),
)


def extract_code(text):
    text = text or ""
    m = re.search(FENCE + r"(?:python)?\s*\n(.*?)" + FENCE, text, re.DOTALL)
    if m:
        return m.group(1).strip() + "\n"
    stripped = text.strip()
    if stripped:
        try:
            ast.parse(stripped)  # bare code with no fences: accept only if valid Python
            return stripped + "\n"
        except SyntaxError:
            pass
    return None


def main(case_dir, model_key):
    case = Path(case_dir)
    work = Path("runs") / f"{case.name}_{model_key}"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(case, work, ignore=shutil.ignore_patterns("__pycache__"))

    _, failure = run_in_sandbox(case, ["test_security"])
    prompt = (
        "You are a security engineer. A security test fails because of a "
        "vulnerability in app.py. Fix the vulnerability.\n\n"
        "Rules: change app.py only. Keep every function name and signature. "
        "Reply with the complete new contents of app.py in ONE "
        + FENCE + "python block and nothing else.\n\n"
        f"--- app.py ---\n{(case / 'app.py').read_text()}\n"
        f"--- test_security.py ---\n{(case / 'test_security.py').read_text()}\n"
        f"--- failing test output ---\n{failure}\n"
    )

    model = MODELS[model_key]
    print("Asking", model, "...")
    r = client.chat.completions.create(
        model=model, max_tokens=6000,
        messages=[{"role": "user", "content": prompt}],
    )
    code = extract_code(r.choices[0].message.content)
    print("Tokens used:", r.usage.total_tokens)
    if not code:
        sys.exit("The model did not return a code block. NOT VERIFIED.")

    (work / "app.py").write_text(code)  # only app.py is ever written
    print("\n--- Patched app.py ---\n" + code)

    verified, checks = verify(case, work)
    for name, ok, _ in checks:
        print(("PASS  " if ok else "FAIL  ") + name)
    print("\nVERDICT:", "VERIFIED" if verified else "NOT VERIFIED")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] not in MODELS:
        sys.exit("usage: python core/patcher.py CASE_DIR lightning|nano|super|ultra")
    main(sys.argv[1], sys.argv[2])
