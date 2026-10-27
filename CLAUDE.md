# Assignment 1 — Basic Matrix Multiplication in Python, Java and C

You are the agent responsible for producing **Assignment 1** of the Big Data course (ULPGC, 2026-2027) for
Daniel Rodríguez Alonso: a complete, reproducible empirical study + a professional scientific report in English.

## Read first (in this order)
1. `context/assignment_brief.md` — what Assignment 1 must contain (source of truth: `context/BD_Individual_Assignments_2026_2027.pdf`)
2. `context/common_protocol.md` — mandatory experimental protocol for all assignments
3. `context/report_requirements.md` — mandatory report structure, submission contents, rubric, AI policy
4. `context/author_and_course.md` — author block, naming, reference machine

@context/working_rules.md

## Skills in this folder (use them)
| Skill | Use it for |
|---|---|
| `multilang-naive-matmul` | **Assignment-specific technical guide** (loop order, layouts, JIT, memory per language, tolerance, sizes) |
| `benchmark-protocol` | experiment plan, harness, `run_measured.py` (lock, warm-up, reps, RSS, timeouts), env capture |
| `results-analysis` | summary stats, growth exponent, plots, LaTeX tables, `numbers.tex` |
| `scientific-report` | writing and compiling `report/main.tex` (IEEE), references, AI disclosure |
| `report-review` | final rubric gate before declaring done |
| `reproducibility-package` | README, Makefile, git, materials zip |

## Status of this assignment
- Submission window was **Week 6 (12–16 Oct 2026)** — today is later than that, so this is **late/urgent**.
  First ask Daniel whether part of A1 already exists elsewhere (code, results, a draft) and reuse it if so.
- Assignments 2, 3 and 4 will reuse this assignment's **validated C (or Java) naive implementation**, the
  **input generator** and the **CSV schema**. Keep them clean and documented in `src/` and `scripts/`.

## Open decisions to ask Daniel at the start (one grouped question, recommended option first)
1. Existing material for A1? (none / path to reuse)
2. Budgets: max runtime per process run (rec. 600 s), total benchmarking time (rec. ≤ 3 h), memory budget (rec. 8 GB).
3. Size sequence (rec. 64 … 2048 incl. non-powers of two; Python until budget).
4. Optional extra experiments beyond the controlled comparison (rec.: none, or C `-O0/-O2/-O3` flags study if time allows).
5. GitHub username / repository name for this assignment (rec. `bigdata-assignment01-matmul-languages`).

## Required deliverables (this folder)
- `deliverables/Assignment01_RodriguezAlonso_Report.pdf` — title suggestion (adapt once results exist):
  *"Runtime and Memory Scaling of Naive Dense Matrix Multiplication in Python, Java and C"*
- `deliverables/Assignment01_RodriguezAlonso_Materials.zip` + local git repo ready to push.
- `docs/defensa_oral.md` (Spanish) for the oral explanation.

## Folder layout
`src/{c,java,python}/` · `tests/` · `scripts/` (gen_inputs, run_experiments) · `configs/` · `data/inputs/` ·
`results/{raw,summary}/` · `analysis/` · `report/` (main.tex, references.bib, figures/, generated/) · `docs/` ·
`deliverables/`
