# Hybrid agent vs one-shot baseline

First 5 runs per cell, temperature 0.7, infrastructure errors excluded. The hybrid was designed after the results for all 11 cases were seen, so these cases are a development set, not an independent test.

## Overall (11 cases, 4 models)

- one-shot baseline: 183/220 (83%), 95% 78% to 88%, 35 false fixes, ~985 tokens/run
- hybrid: 183/220 (83%), 95% 78% to 88%, 37 false fixes, ~10570 tokens/run

## By case

| case | one-shot baseline | hybrid |
|---|---|---|
| case01_sqli | 20/20 (0 FF) | 20/20 (0 FF) |
| case02_path_traversal | 19/20 (0 FF) | 20/20 (0 FF) |
| case03_prefix_traversal | 18/20 (2 FF) | 19/20 (1 FF) |
| case04_orderby_injection | 20/20 (0 FF) | 20/20 (0 FF) |
| case05_command_injection | 20/20 (0 FF) | 20/20 (0 FF) |
| case06_unsafe_eval | 20/20 (0 FF) | 20/20 (0 FF) |
| case07_html_escape | 9/20 (11 FF) | 7/20 (13 FF) |
| case08_open_redirect | 0/20 (20 FF) | 0/20 (20 FF) |
| case09_like_search | 20/20 (0 FF) | 19/20 (1 FF) |
| case10_zip_extract | 18/20 (2 FF) | 18/20 (2 FF) |
| case11_header_injection | 19/20 (0 FF) | 20/20 (0 FF) |

## By model

| model | one-shot baseline | hybrid |
|---|---|---|
| lightning | 46/55 (9 FF) | 46/55 (9 FF) |
| nano | 44/55 (10 FF) | 47/55 (8 FF) |
| super | 44/55 (10 FF) | 43/55 (12 FF) |
| ultra | 49/55 (6 FF) | 47/55 (8 FF) |

## Does the tier label predict the hidden oracle?

| tier | runs | passed the oracle | rate |
|---|---|---|---|
| contested | 20 | 14 | 70% |
| unproven | 17 | 17 | 100% |
| verified | 183 | 152 | 83% |
