# PatchProof results

First 5 runs per cell, temperature 0.7, infrastructure errors excluded. Small samples: treat differences of one or two runs as noise.

## Baseline vs loop agent (Super and Ultra, 5 cases)

| case | model | baseline verified | baseline false fixes | loop verified | loop false fixes |
|---|---|---|---|---|---|
| case01_sqli | super | 5/5 | 0 | 5/5 | 0 |
| case01_sqli | ultra | 5/5 | 0 | 5/5 | 0 |
| case03_prefix_traversal | super | 4/5 | 1 | 4/5 | 1 |
| case03_prefix_traversal | ultra | 4/5 | 1 | 5/5 | 0 |
| case05_command_injection | super | 5/5 | 0 | 3/5 | 0 |
| case05_command_injection | ultra | 5/5 | 0 | 5/5 | 0 |
| case07_html_escape | super | 3/5 | 2 | 2/5 | 3 |
| case07_html_escape | ultra | 5/5 | 0 | 3/5 | 0 |
| case08_open_redirect | super | 0/5 | 5 | 0/5 | 5 |
| case08_open_redirect | ultra | 0/5 | 5 | 1/5 | 4 |

| agent | verified | 95% interval | false fixes | avg tokens per run |
|---|---|---|---|---|
| baseline (one shot, no test) | 36/50 (72%) | 58% to 83% | 14 | 653 |
| loop agent | 33/50 (66%) | 52% to 78% | 13 | 6705 |

## Baseline on all 8 cases and 4 models (verified/runs, false fixes in brackets)

| case | lightning | nano | super | ultra |
|---|---|---|---|---|
| case01_sqli | 5/5 (0) | 5/5 (0) | 5/5 (0) | 5/5 (0) |
| case02_path_traversal | 5/5 (0) | 4/5 (0) | 5/5 (0) | 5/5 (0) |
| case03_prefix_traversal | 5/5 (0) | 5/5 (0) | 4/5 (1) | 4/5 (1) |
| case04_orderby_injection | 5/5 (0) | 5/5 (0) | 5/5 (0) | 5/5 (0) |
| case05_command_injection | 5/5 (0) | 5/5 (0) | 5/5 (0) | 5/5 (0) |
| case06_unsafe_eval | 5/5 (0) | 5/5 (0) | 5/5 (0) | 5/5 (0) |
| case07_html_escape | 1/5 (4) | 0/5 (5) | 3/5 (2) | 5/5 (0) |
| case08_open_redirect | 0/5 (5) | 0/5 (5) | 0/5 (5) | 0/5 (5) |
