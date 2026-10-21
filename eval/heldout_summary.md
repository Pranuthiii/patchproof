# Held-out results (cases 09 to 11)

First 10 runs per cell, temperature 0.7, infrastructure errors excluded. The attack library was written after we had seen the oracles for cases 01 to 08, so only these three cases are an independent test.

## Primary question: seeded loop vs plain loop on cases 09 and 10 combined

- one-shot baseline: 76/80 (95%), 95% 88% to 98%, 4 false fixes, ~1339 tokens/run
- plain loop: 67/80 (84%), 95% 74% to 90%, 2 false fixes, ~13211 tokens/run
- seeded loop: 40/80 (50%), 95% 39% to 61%, 1 false fixes, ~21112 tokens/run

**Pre-registered rule:** The seeded loop verified fewer, and the 95% intervals do not overlap.

## Control: case 11 (a class the library does not cover)

- one-shot baseline: 39/40 (98%), 95% 87% to 100%, 0 false fixes, ~941 tokens/run
- plain loop: 26/40 (65%), 95% 50% to 78%, 1 false fixes, ~17314 tokens/run
- seeded loop: 23/40 (58%), 95% 42% to 71%, 0 false fixes, ~19283 tokens/run

## By case

| case | one-shot baseline | plain loop | seeded loop |
|---|---|---|---|
| case09_like_search | 40/40 (0 FF) | 39/40 (0 FF) | 26/40 (0 FF) |
| case10_zip_extract | 36/40 (4 FF) | 28/40 (2 FF) | 14/40 (1 FF) |
| case11_header_injection | 39/40 (0 FF) | 26/40 (1 FF) | 23/40 (0 FF) |

## By model (all three cases)

| model | one-shot baseline | plain loop | seeded loop |
|---|---|---|---|
| lightning | 30/30 (0 FF) | 21/30 (1 FF) | 0/30 (0 FF) |
| nano | 30/30 (0 FF) | 19/30 (1 FF) | 17/30 (0 FF) |
| super | 25/30 (4 FF) | 26/30 (0 FF) | 19/30 (1 FF) |
| ultra | 30/30 (0 FF) | 27/30 (1 FF) | 27/30 (0 FF) |
