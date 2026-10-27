# Assignment 1 — Basic Matrix Multiplication in Different Languages

Source: *BD_Individual_Assignments_2026_2027.pdf*, page 4 (transcribed). Submission window: **Week 6, 12–16 October 2026**.

## Research objective
Compare a basic dense matrix multiplication algorithm implemented in **Python, Java and C**. Investigate how
**matrix size affects runtime and memory** under the documented execution conditions.

## Required implementations and comparisons
- Implement the straightforward **triple-loop algorithm in all three languages**. Each implementation must use
  O(n³) arithmetic work for n × n inputs.
- Use a **comparable loop order and numeric type**. **Describe each storage layout** and any unavoidable
  language-specific differences. **Do not replace the required loops with an optimised matrix multiplication
  library call.**
- Test a feasible increasing sequence of matrix sizes using the common protocol. For each size, compare all three
  implementations wherever runs complete within the declared budget.
- Document the **compiler and optimisation flags for C**, **JVM and warm-up settings for Java**, and **Python
  implementation and version**. Explain which settings remain fixed.

## Required evidence
| Measure | What to report |
|---|---|
| Time | Repeated measurements, median and variability for every tested configuration |
| Memory | Named memory metric and measurement tool for each implementation |
| Correctness | Test cases, reference results and any numerical tolerance |
| Limits | Largest tested feasible size and any timeouts or memory failures |

## Analysis expected
Explain the observed growth and discuss interpreter, runtime and memory-layout effects where your evidence supports
them. **Compare the trend with the cubic algorithmic model** while recognising constants and system effects.

Scope conclusions to the tested implementations, settings, inputs and hardware. **Avoid a general claim that one
programming language is universally faster.** Language-specific optimisations can form additional experiments, but
must remain **separate from the controlled basic comparison**.

## Submission
Research report (PDF), code and reproducibility materials (see `report_requirements.md`).
