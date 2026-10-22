# PatchProof: AI fixes that show their receipts

PatchProof runs AI-written security patches inside a locked-down sandbox and judges them against a test the model never sees. We used it to measure four NVIDIA Nemotron models, served through Nebius Token Factory, on eight hand-built vulnerabilities.

**Live demo (recorded runs):** https://pranuthiii.github.io/patchproof/

Built for the Nebius x NVIDIA Global AI Hackathon, Coding and Agentic Engineering track.

## What we found

- **One-shot fixes pass easy cases and fail subtle ones.** Four models patched code in a single call with no test. On five common flaw types, 99 of 100 patches were verified. On open redirect, all 20 patches passed the existing tests and failed the hidden oracle test.
- **A hidden oracle catches what ordinary tests miss.** On the prefix-traversal, HTML-escaping and open-redirect cases it flagged patches that looked correct and were not.
- **An AI-written test with retries did not help.** Across four models and eight cases, five runs each: 112/160 verified with the loop against 126/160 one-shot, at about 12 times the tokens. The loop's losses were mostly runs with no usable output, such as truncated replies and rejected tests, and not wrong patches.
- **A longer attack list made it worse.** On three held-out cases (09 to 11, built after the library was written), a general attack-variant library in the test-writer prompt verified 40/80 on cases 09 and 10 against 67/80 for the plain loop and 76/80 one-shot. Lightning was truncated on every library run. Excluding Lightning the gap narrows but remains. The library was written after we had seen the oracles for cases 01 to 08, so only cases 09 to 11 test it fairly.
- **A hybrid tied the one-shot fix at 11 times the cost.** Keeping the one-shot patch and using the AI test only as extra evidence verified 183/220 against 183/220, at about 10,600 tokens per run against 985. Its tier label did not predict correctness: runs labelled verified passed the hidden oracle 152/183 (83%), the same as the overall rate. The hybrid was designed after all 11 cases had been seen, so this is a development result.
- **Why:** the AI-written attack tests cover attacks the model already knows. The open-redirect tests we inspected did not include the `///evil.test` form the oracle uses.

Full tables: [eval/summary.md](eval/summary.md). Raw per-run results: [eval/](eval/).

## What "verified" means

In the benchmark, a run is verified only if all of these hold: the AI's attack test fails on the vulnerable code, the same test passes on the patch, the existing tests still pass, and a hand-written hidden oracle test passes. On real code there is no hidden oracle, so a verdict there would be only as strong as the AI-written test. This project measures how often that weaker verdict is wrong.

## How it works

1. A plain-English **finding** names a vulnerability and the function it affects.
2. A Nemotron model writes an **attack test** that must fail on the vulnerable code.
3. The model writes a **patch** to `app.py` only, and may retry using the verifier's output.
4. A **sandbox verifier** (plain code, not the model) runs every test in Docker.
5. A **hidden oracle** the model never sees gives the final verdict.

The sandbox runs with no network, a read-only root filesystem, dropped Linux capabilities, a non-root user, memory, CPU and process limits, and a 45 second timeout. Test files are hash-checked so a patch cannot edit the tests it is judged by. Docker is not a production security boundary, and this tool is a research prototype.

## How we use NVIDIA and Nebius

- **Models (NVIDIA Nemotron, via Nebius Token Factory):** `nvidia/Nemotron-3_5-Lightning`, `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`. Check exact IDs with the models endpoint, because casing varies.
- **Nebius Token Factory:** every model call goes through the OpenAI-compatible endpoint `https://api.tokenfactory.nebius.com/v1/`. We did not use Nebius AI Cloud compute.
- **Tavily:** `core/web_context.py` makes a runtime Tavily search and `core/agent_loop_web.py` adds the results to the test-writer prompt as untrusted reference text. In a 12-run test on one case the results were mixed, so we report no measured accuracy benefit.

## Run it yourself

Requirements: Python 3.11 or newer, Docker, a Nebius Token Factory API key, and optionally a Tavily key.

```bash
git clone https://github.com/Pranuthiii/patchproof.git
cd patchproof
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your keys to .env
python smoke.py             # lists the Nemotron models on your account
```

Run the agent on one case:

```bash
export PATCHPROOF_TEMPERATURE=0.7
python core/agent_loop.py fixtures/case08_open_redirect super      # AI test + patch + retries
python core/agent_baseline.py fixtures/case08_open_redirect super  # one-shot fix, no test
```

Run a batch and summarise it:

```bash
PATCHPROOF_AGENT=core/agent_baseline.py PATCHPROOF_RESULTS=eval/my_results.jsonl PATCHPROOF_GRIDDIR=runs/my_grid \
  python core/run_grid.py run --repeats 5 --cases case01_sqli case08_open_redirect
python core/summarize.py
python web/build_site.py    # regenerates the docs/ site
```

Re-validate any oracle against a known-good and a known-naive fix:

```bash
python core/verifier.py fixtures/case08_open_redirect reference/case08_open_redirect/good    # VERIFIED
python core/verifier.py fixtures/case08_open_redirect reference/case08_open_redirect/naive   # NOT VERIFIED
```

## Repository layout

| Path | Contents |
|---|---|
| `core/` | agents, sandbox verifier, batch runner, summary script, Tavily helper |
| `fixtures/` | eight vulnerable apps, each with existing tests, a finding and a hidden oracle |
| `reference/` | a known-good and a known-naive fix for each oracle |
| `eval/` | raw per-run results and the generated summary |
| `web/` | the site generator |
| `demo_runs/`, `docs/` | curated example runs and the published site |

## Limits

- Small samples: five runs per cell and eight hand-built cases. These are measurements of this setup, not a general benchmark.
- The first experiments used the API's default temperature, where Super sometimes returned identical replies, so some repeats there are not independent. The main evaluation used temperature 0.7.
- Ultra was available when its runs were made but was no longer listed on the account when checked on Oct 13, 2026.
- We widened the case 07 finding after the first baseline run, because the oracle checked a `javascript:` URL issue the original finding did not mention. Both versions of that baseline are in `eval/`.
- Truncated means the model hit the 16,000-token output limit set by the test harness.

## License

MIT. See [LICENSE](LICENSE).
