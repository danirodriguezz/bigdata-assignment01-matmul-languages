# Review checklist — Assignment 01 (report-review skill)

Reviewed 2026-10-29 on `report/main.pdf` (7 pages, IEEE two-column) and the materials in this folder.
✅ = satisfied (where to find it) · ⚠️ = satisfied with a caveat / needs Daniel · ❌ = not satisfied.

## A. Mandatory structure
| Item | Status | Evidence |
|---|---|---|
| Title page: name, assignment number, research title | ✅ | title block of `report/main.tex` |
| Abstract: question, method, main result with variability, scope | ✅ | Abstract (exponents with 95 % CI, ratios, k, scope sentence) |
| Introduction: one RQ, factor, outcomes, labelled hypotheses | ✅ | §I (RQ, H1–H3) |
| Background: every technique cited | ✅ | §II (golub2013, drepper2007, lam1991, goto2008, georges2007, jep306, pep659, pydocsys, higham2002, hoefler2015, mytkowicz2009) |
| Methodology: implementations, inputs, environment, correctness, protocol, budgets | ✅ | §III A–F, Table I; sessions and C flags study described |
| Results: labelled tables/figures, units, k, variability, failures | ✅ | §IV, Tables II–VII, Figs. 1–4; Python n=2048 timeout reported without a time |
| Discussion: RQ answer, verdict per hypothesis, evidence-backed explanations, limitations | ✅ | §V A–D; cache/layout explanations explicitly marked as not verified |
| Conclusions scoped; open questions | ✅ | §VI |
| References (IEEE) + Reproducibility Materials + Use of Generative AI | ✅ | end of paper |

## B. Assignment-specific requirements (`context/assignment_brief.md`)
| Requirement | Status | Where |
|---|---|---|
| Triple loop in Python, Java and C, O(n³) | ✅ | §III-A, `src/` |
| Comparable loop order and numeric type; storage layouts described | ✅ | §III-A (ijk, float64, three layouts) |
| No optimised library call in kernels | ✅ | §III-A; NumPy only for inputs/reference |
| Increasing feasible size sequence, all three compared where runs complete | ✅ | Table III (n = 64…2048) |
| C compiler + flags, JVM + warm-up settings, Python version; fixed settings | ✅ | §III-A "Fixed settings", §III-E, Table I |
| Time: repeated measurements, median and variability | ✅ | Table III (median, IQR, k) |
| Memory: named metric and tool per implementation | ✅ | §III-E, Table VI, Fig. 3 |
| Correctness: tests, reference, tolerance | ✅ | §III-D, Table II |
| Limits: largest feasible size, timeouts | ✅ | Table V |
| Growth vs cubic model, constants and system effects | ✅ | Table IV, Fig. 2, §V-C |
| Language-specific optimisations kept separate | ✅ | C flags study: separate table/section, labelled as separate |
| No universal "language X is faster" claim | ✅ | Abstract/Conclusions scoped to machine/toolchains/settings |

## C. Experimental design & correctness
| Item | Status | Note |
|---|---|---|
| Same inputs; seed, generator, range, type documented | ✅ | §III-B, `data/inputs/checksums.sha256` |
| Environment documented | ✅ | Table I, `results/environment.md`, `environment_after.md` (common lines identical) |
| Timing boundary stated, not mixed | ✅ | kernel boundary everywhere |
| Warm-ups excluded; ≥ 5 reps or justified; median + IQR | ⚠️ | k = 5 everywhere except Python n = 1536 (k = 3) and n = 2048 (1 attempt) — justified by the budget and stated as limitation (iv) |
| Memory in every configuration, named metric/tool, not mixed | ✅ | peak RSS (GNU time) for every run; language metrics stated as not comparable |
| Correctness tests with justified tolerance, reported | ✅ | Table II |
| Largest completed vs attempted, budgets, no invented times | ✅ | Table V; Python 2048 row has empty `time_s` |

## D. Integrity
Spot-check of numbers in the PDF recomputed directly from `results/raw/*.csv` (independent script, not
`make_all.py`) — all match:
1. C n=1536 median 9.90 s ✅ 2. Java n=1536 24.6 s ✅ 3. Python n=1536 280 s ✅ 4. C n=2048 38.8 s ✅
5. Java n=2048 64.0 s ✅ 6. Python n=1024 77.8 s ✅ 7. C ns/madd n=64 0.714 ✅, n=2048 4.51 ✅
8. Java/C n=1536 2.48 ✅ 9. Python/C n=1536 28.2 ✅ 10. Python n=2048 status timeout, wall 600.0 s ✅
11. Peak RSS n=1536: 55.8 / 142.4 / 283.4 MiB ✅ 12. RSS baselines 1.9 / 48.2 / 12.5 MiB ✅
13. C flags n=1024: -O0 4.32 s, -O2 1.57 s, -O3 1.50 s, native 1.51 s ✅ 14. 364 raw rows ✅

| Item | Status | Note |
|---|---|---|
| No placeholders (`%%`, TODO, ??) in .tex or PDF text | ✅ | grep on `main.tex` and `pdftotext` output |
| Every reference verified | ✅ | 15 entries verified in the previous session (DOI/publisher/official URL); gccopt claim on `-fassociative-math` re-checked on 2026-10-29 against the GCC 13.3 manual |
| AI disclosure present and confirmed by Daniel | ✅ | confirmed 2026-10-29 (`docs/DECISIONS.md`) |
| No universality claims | ✅ | |

## E. Communication
| Item | Status | Note |
|---|---|---|
| Figures: axes with units, legends, captions with statistic/k, colour-blind palette, referenced | ✅ | legends moved so they no longer hide data; Java warm-up axis now plain numbers |
| English, defined abbreviations | ✅ | RQ, IQR, RSS, JIT, TLB, FMA defined at first use |
| 5–8 pages; log clean | ✅ | 7 pages; no errors/undefined refs; two overfull boxes of ~1 pt (invisible) |

## F. Reproducibility package
| Item | Status | Note |
|---|---|---|
| README with exact commands, versions, hardware, expected runtime | ✅ | updated with measured times and sessions |
| `make analysis report` regenerates everything from raw data | ✅ | tested from scratch (summary/, generated/, figures/ deleted first) |
| Raw CSVs + schema; input generation + checksums | ✅ | `results/README.md`, `scripts/gen_inputs.py` |
| Reused materials identified | ✅ | none (first assignment) |
| Deliverables (PDF + zip) built; zip excludes .venv, build, .bin | ✅ | `make package` (git archive of HEAD) |
| Git repo, everything committed, remote | ⚠️ | committed and tagged locally; **Daniel must push** (`git push && git push origin v1.0-submission`) |

## G. Oral defence
| Item | Status |
|---|---|
| `docs/defensa_oral.md` (Spanish): RQ, fairness, key results, limitations, live run, Q&A, code walkthrough | ✅ |

## Items for Daniel
1. Push the commit and the tag `v1.0-submission` to GitHub (commands in README §8).
2. Late submission (window 12–16 Oct passed): check with the instructor.
3. Read the PDF once fully and the oral-defence script; the cache/TLB and Java-layout explanations are conjectures — present them as such.
