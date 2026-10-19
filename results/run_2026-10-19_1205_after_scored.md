# Scored: run_2026-10-19_1205_after.json

Produced by `score_run.py::score`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. matching query completes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 1 (revised). … and picks an acceptable match | 4 of 5 | PASS | FAIL | PASS | PASS | PASS | MET (4/5) |
| 2. impossible query stops early | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. selected item is the one passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. fit card is a caption and varies | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. filters are respected | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Why each FAIL failed, and other checks:**

- 1 (revised), try 2 (`retro band shirt`): picked lst_024 Vintage Polo Shirt — Forest Green, wanted one of ['lst_006', 'lst_033']
- 4(b): all 5 fit cards differ — no identical pair
