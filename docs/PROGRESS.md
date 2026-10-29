# Progress / handoff — Assignment 01

## UPDATE 2026-10-29 11:01 (session 2 stopped by Daniel)
Session 2 (2026-10-29 10:46–11:01, fresh boot, loadavg ≈ 0.5–1.3) added to `results/raw/size_sweep.csv`:
Python n=768 runs 4–5 (now k=5, mixed sessions), C/Java/Python n=1024 (k=5 each), Python n=1536 run 1 of 3.
The 2nd Python n=1536 run was killed after ~76 s (no row written — nothing to clean). Log: `results/logs/session2_benchmark.log`.
Also done: Daniel confirmed the AI statement and the GitHub URL (docs/DECISIONS.md); `analysis/make_all.py` now
detects measurement sessions (>1 h gap) → `results/summary/sessions.csv` + macros `Session*`, `Mixed*` (report must
state which sizes come from which session).

**PENDING** (≈ 35–40 min machine time): Python n=1536 ×2, C/Java n=1536, C/Java/Python n=2048, C flags study.
Resume with ONE command (from the folder root; run in background, it takes the machine-wide lock per config):
```bash
bash scripts/resume_benchmarks.sh 2>&1 | tee -a results/logs/resume_benchmark.log
```
Then: `make analysis`, write Abstract/Results/Discussion/Conclusions in `report/main.tex` (mention the 2–3
measurement sessions and their load in Methodology), fill `%%RESULTADOS%%` in `docs/defensa_oral.md`,
`make report`, report-review, `make package`, commit + tag `v1.0-submission`.

---
## Previous handoff (2026-10-27)

**Stopped:** 2026-10-27 23:02 UTC (laptop clock), on Daniel's request. All my benchmark processes were killed
(driver, run_measured.py, the running Python program). Assignment 2's processes were not touched.

## Phase status (working_rules.md)
| Phase | Status |
|---|---|
| 0 Orientation | DONE — `results/environment.md`, `docs/DECISIONS.md` (all decisions recorded), venv + `requirements-lock.txt`, git repo |
| 1 Plan | DONE — `docs/experiment_plan.md` (RQ, H1–H3, sizes, budgets, per-language W/P rules justified by the pilot) |
| 2 Implement | DONE — `src/c` (kernel `matmul_naive.c/.h`, `matrix_io.c/.h`, `bench_naive.c`), `src/java/MatMulNaive.java`, `src/python/matmul_naive.py`, `tests/test_correctness.py` (ALL TESTS PASSED, incl. bit-identity C/Java/Python and gcc -O0/-O3/-O3 -march=native variants), `scripts/gen_inputs.py`, `scripts/run_experiments.py`, `scripts/run_all_benchmarks.sh`, `configs/experiment.json`, Makefile filled |
| 3 Pilot | DONE — `results/raw/pilot_size_sweep.csv` (C 2.0 s, Java 5.3 s at n=1024; Python ~9 s at n=512) |
| 4 Benchmark | PARTIAL (see below) |
| 5 Analysis | Script DONE and tested on partial data: `analysis/make_all.py` (+ summarize/growth_fit/plot_style). Must be re-run on final data |
| 6 Report | PARTIAL — `report/main.tex`: title, keywords, Introduction, Background, Methodology, Reproducibility, AI statement written; placeholders `%%ABSTRACT%%`, `%%RESULTS%%`, `%%DISCUSSION%%`, `%%CONCLUSIONS%%` remain. `report/references.bib` = 15 verified entries (Crossref/official URLs). Compiles. |
| 7 Review & package | NOT STARTED — `docs/defensa_oral.md` drafted (Spanish) with placeholder `%%RESULTADOS%%`; `docs/review_checklist.md` and deliverables not built |

## Benchmark state (`results/raw/`)
- `rss_baseline.csv` — COMPLETE (n=1, C/Java/Python, 5 processes each).
- `size_sweep.csv` — completed configurations (k measured samples, all status ok):
  C n = 64…768 (k=5 each); Java n = 64…768 (k=5 each); Python n = 64…512 (k=5), **n=768 k=3 of 5**
  (4th process interrupted by the stop; no row was written for it — nothing to clean).
- PENDING: Python n=768 (2 more process runs); C, Java, Python at n = 1024, 1536, 2048 (Python 1536 P=3,
  2048 single attempt, expected timeout at 600 s).
- `c_flags.csv` — NOT STARTED (optional separate experiment, -O0/-O2/-O3/-O3 -march=native at n=256,512,1024).
- Note: high machine load during the sweep (loadavg 2–6: browser + other agents); Python n=384 shows elevated
  times (70–115 ns/madd vs ~60 at 512). Keep all rows; report it as variability with the load average.
- Machine time used so far ≈ 15 min of the 90-min budget (plus pilot ≈ 1.5 min).

## Resume (from the folder root)
```bash
cd /home/daniel/Documentos/Universidad/4Year/Big_Data/Teoria/Assigments/Assignment01_Basic_MatMul_Languages
# 1) finish Python n=768 (2 more process runs; same command as the existing rows)
for i in 1 2; do .venv/bin/python .claude/skills/benchmark-protocol/scripts/run_measured.py --out results/raw/size_sweep.csv \
  --warmup 0 --reps 1 --timeout 600 --label assignment=A1 experiment=size_sweep method=naive_ijk language=python n=768 \
  dtype=float64 representation=dense threads=1 seed=42 --env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  -- .venv/bin/python src/python/matmul_naive.py --a data/inputs/A_n768_s42.bin --b data/inputs/B_n768_s42.bin \
  --n 768 --warmup 0 --reps 1 --min-sample-time 0.2; done
# 2) remaining sizes (driver skips nothing automatically: pass only the pending sizes), then the C flags study
.venv/bin/python scripts/run_experiments.py --experiment size_sweep --sizes 1024 1536 2048 2>&1 | tee -a results/logs/size_sweep.log
.venv/bin/python scripts/run_experiments.py --experiment c_flags 2>&1 | tee results/logs/c_flags.log
PATH="$PWD/.venv/bin:$PATH" bash .claude/skills/benchmark-protocol/scripts/capture_env.sh results/environment_after.md
# 3) analysis + report
make analysis      # regenerates results/summary, report/figures, report/generated/numbers.tex
#    then write Abstract/Results/Discussion/Conclusions in report/main.tex using the \macros of numbers.tex,
#    insert tables: \input{generated/table_runtime|table_growth|table_memory|table_limits|table_correctness|table_cflags}
#    and figures runtime_vs_n, ns_per_madd, memory_rss, java_warmup; fill %%RESULTADOS%% in docs/defensa_oral.md
make report && git add -A && git commit -m "..." && make package
```
Run step 2 in the background (≈ 50–60 min machine time + lock waits); stop rule: if Python times out at 2048
that is an expected result (recorded as `timeout`, never given a time).
If the pending sizes are run in a different session/day, mention the second session in the report (Methodology).

## Files changed but not finished
- `report/main.tex` (placeholders listed above), `docs/defensa_oral.md` (`%%RESULTADOS%%`),
  `report/generated/*` and `report/figures/*` (built from partial data — regenerate).

## Open questions for Daniel (also in `docs/OPEN_QUESTIONS.md`)
1. Confirm the "Use of Generative AI" statement (Claude Code, Anthropic, model Claude Opus 5.5).
2. Confirm GitHub URL `https://github.com/danirodriguezz/bigdata-assignment01-matmul-languages` (username taken
   from `~/.gitconfig`), create the repo and push (commands in README §8).
3. Late submission (window 12–16 Oct passed): check with the instructor.
