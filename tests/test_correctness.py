#!/usr/bin/env python3
"""Correctness tests for the three naive implementations (C, Java, Python).

Each implementation is run as a black box through its command-line interface (the same programs
that are benchmarked), writing its result matrix with --out-c. Cases:
  * known products with exact answers: 1x1, 2x2 and a non-symmetric 3x3 (integers, exact in float64);
  * identity (A·I = A and I·B = B, exact) and zero matrix (A·0 = 0, exact), n = 7;
  * random uniform[-1, 1) inputs, n in {7, 64, 100}, compared with NumPy (reference only, 1 thread)
    with the element-wise tolerance  |c_ij - c_ref_ij| <= 2·n·u·(|A||B|)_ij,  u = 2^-53
    (each of the two results satisfies the classical dot-product bound γ_n·(|A||B|)_ij with
    γ_n = n·u/(1 - n·u) ≈ n·u, so their difference is bounded by ≈ 2·n·u·(|A||B|)_ij);
  * bit-identity of the three implementations (same ijk evaluation order) and equal checksums;
  * the optional gcc flag variants (-O0, -O3, -O3 -march=native), if built, pass the same checks;
  * the Python result holds n*n distinct float objects (assumption of pyobj_deep_size_bytes).
A JSON summary with the maximum observed errors is written to results/raw/correctness_tests.json.

Usage:  .venv/bin/python tests/test_correctness.py      (exit code 0 = all tests passed)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")       # NumPy reference single-threaded
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))
import matmul_naive as pyimpl  # noqa: E402

PYTHON = sys.executable
CMDS = {
    "c": [str(ROOT / "build" / "c" / "matmul_naive_c")],
    "java": ["java", "-cp", str(ROOT / "build" / "java"), "MatMulNaive"],
    "python": [PYTHON, str(ROOT / "src" / "python" / "matmul_naive.py")],
}
# optional gcc flag variants (separate c_flags experiment); tested when they have been built
for _v in ("O0", "O3", "O3_native"):
    _bin = ROOT / "build" / "c" / f"matmul_naive_c_{_v}"
    if _bin.exists():
        CMDS[f"c_{_v}"] = [str(_bin)]
U = 2.0 ** -53
failures = []
report = {"unit_roundoff": U, "tolerance_rule": "|c - c_ref| <= 2*n*u*(|A||B|)_ij vs NumPy; exact across own implementations",
          "cases": []}


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def run_impl(lang, a, b, tmp):
    n = a.shape[0]
    pa, pb, pc = (Path(tmp) / f"{x}.bin" for x in "ABC")
    a.astype("<f8").tofile(pa)
    b.astype("<f8").tofile(pb)
    cmd = CMDS[lang] + ["--a", str(pa), "--b", str(pb), "--n", str(n), "--warmup", "0", "--reps", "1",
                        "--out-c", str(pc)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    rec = json.loads(out.strip().splitlines()[-1])
    c = np.fromfile(pc, dtype="<f8").reshape(n, n)
    return c, rec


def case(name, a, b, expected=None, exact=True):
    print(f"[{name}] n={a.shape[0]}")
    n = a.shape[0]
    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        for lang in CMDS:
            results[lang] = run_impl(lang, a, b, tmp)
    entry = {"case": name, "n": n}
    for lang, (c, rec) in results.items():
        check(abs(rec["checksum"] - float(np.sum(c.ravel()))) <= 1e-12 * max(1.0, np.abs(c).sum()),
              f"{lang}: printed checksum consistent with written C")
        if expected is not None and exact:
            check(np.array_equal(c, expected), f"{lang}: exact expected result")
        else:
            ref = a @ b                                  # NumPy reference (not a student method)
            bound = 2 * n * U * (np.abs(a) @ np.abs(b))
            err = np.abs(c - ref)
            check(bool(np.all(err <= bound)), f"{lang}: within 2·n·u·(|A||B|) of NumPy")
            denom = np.where(np.abs(ref) > 0, np.abs(ref), 1.0)
            entry[f"{lang}_max_abs_err_vs_numpy"] = float(err.max())
            entry[f"{lang}_max_rel_err_vs_numpy"] = float((err / denom).max())
            entry[f"{lang}_max_err_over_bound"] = float((err / bound).max())
    c_ref = results["c"][0]
    for lang in [x for x in CMDS if x != "c"]:
        same = np.array_equal(results[lang][0].view(np.uint64), c_ref.view(np.uint64))
        check(same, f"{lang} bit-identical to c")
        entry[f"{lang}_bit_identical_to_c"] = bool(same)
        check(results[lang][1]["checksum"] == results["c"][1]["checksum"], f"{lang} checksum == c checksum")
    report["cases"].append(entry)


def main():
    rng = np.random.default_rng(2026)
    case("known_1x1", np.array([[3.0]]), np.array([[-2.0]]), expected=np.array([[-6.0]]))
    case("known_2x2", np.array([[1.0, 2.0], [3.0, 4.0]]), np.array([[5.0, 6.0], [7.0, 8.0]]),
         expected=np.array([[19.0, 22.0], [43.0, 50.0]]))
    a3 = np.array([[1.0, 2.0, 0.0], [0.0, 1.0, 3.0], [4.0, 0.0, 1.0]])
    b3 = np.array([[2.0, 0.0, 1.0], [1.0, 3.0, 0.0], [0.0, 1.0, 2.0]])
    case("known_3x3_nonsymmetric", a3, b3,
         expected=np.array([[4.0, 6.0, 1.0], [1.0, 6.0, 6.0], [8.0, 1.0, 6.0]]))
    r7 = rng.uniform(-1, 1, (7, 7))
    eye, zero = np.eye(7), np.zeros((7, 7))
    case("identity_right_A_I", r7, eye, expected=r7)
    case("identity_left_I_B", eye, r7, expected=r7)
    case("zero_A_0", r7, zero, expected=zero)
    for n in (7, 64, 100):
        case(f"random_uniform_n{n}", rng.uniform(-1, 1, (n, n)), rng.uniform(-1, 1, (n, n)), exact=False)

    print("[python object layout] distinct float objects in C")
    m = [[0.0] * 7 for _ in range(7)]
    pyimpl.multiply(r7.tolist(), r7.tolist(), m, 7)
    ids = {id(v) for row in m for v in row}
    check(len(ids) == 49, "python: 49 distinct float objects in a 7x7 result")
    a_list = r7.tolist()
    check(len({id(v) for row in a_list for v in row}) == 49, "python: tolist() rows hold distinct floats")

    out = ROOT / "results" / "raw" / "correctness_tests.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    report["numpy_version"] = np.__version__
    report["passed"] = not failures
    report["failures"] = failures
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\n{'ALL TESTS PASSED' if not failures else f'{len(failures)} FAILURE(S)'} -> {out}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
