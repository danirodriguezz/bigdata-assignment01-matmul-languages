# Open questions / items for Daniel — Assignment 01

| # | Item | Default taken by the agent | Action needed from Daniel |
|---|---|---|---|
| 1 | "Use of Generative AI" statement (report + README) | Drafted: Claude Code (Anthropic), model Claude Opus 5.5; planning, code, tests, analysis scripts, LaTeX drafting, language | ✅ Confirmed by Daniel (2026-10-29) |
| 2 | GitHub repository | Name `bigdata-assignment01-matmul-languages`; no remote added (push is blocked for the agent) | ✅ URL confirmed (2026-10-29): `git@github.com:danirodriguezz/bigdata-assignment01-matmul-languages.git` — Daniel adds the remote and pushes (README §8) |
| 3 | Late submission (window 12–16 Oct 2026 passed) | Work done anyway | Check with the instructor whether late submission is accepted |
| 4 | Hardware counters (`perf`, paranoid = 4) | Not used; stated as a limitation | None (optional: `sudo sysctl -w kernel.perf_event_paranoid=1` to add cache-miss evidence) |
| 5 | Concurrent agents on the same laptop | Benchmarks serialised by the lock, but un-locked work of other agents (compilation, tests) may run concurrently; `loadavg_1m` recorded per row | None — stated as a limitation |
