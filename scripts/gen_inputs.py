#!/usr/bin/env python3
"""Generate the shared input matrices used by every implementation (C, Java, Python).

For each size n and seed s it writes
    data/inputs/A_n{n}_s{s}.bin   and   data/inputs/B_n{n}_s{s}.bin
as raw little-endian IEEE-754 float64 values in row-major order (8*n*n bytes each, no header),
plus a JSON sidecar data/inputs/inputs_n{n}_s{s}.json with the metadata, and it (re)writes
data/inputs/checksums.sha256 (sha256sum format) for every .bin file present.

Generator: NumPy PCG64 via numpy.random.default_rng(seed); A is drawn first, then B, both
uniform on [-1, 1).  The value range keeps every partial sum far below the float64 overflow
threshold (|c_ij| <= n), so overflow is impossible for the tested sizes.

Usage
    python3 scripts/gen_inputs.py --config configs/experiment.json      # all sizes in the config
    python3 scripts/gen_inputs.py --n 512 --seed 42                      # a single size
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "inputs"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def generate(n, seed, out_dir=OUT_DIR, force=False):
    """Write A and B for (n, seed); skip if the files exist and match the sidecar checksums."""
    out_dir.mkdir(parents=True, exist_ok=True)
    a_path = out_dir / f"A_n{n}_s{seed}.bin"
    b_path = out_dir / f"B_n{n}_s{seed}.bin"
    meta_path = out_dir / f"inputs_n{n}_s{seed}.json"
    if not force and a_path.exists() and b_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta["sha256"] == {a_path.name: sha256(a_path), b_path.name: sha256(b_path)}:
            return meta
    rng = np.random.default_rng(seed)
    a = rng.uniform(-1.0, 1.0, size=(n, n))
    b = rng.uniform(-1.0, 1.0, size=(n, n))
    a.astype("<f8").tofile(a_path)
    b.astype("<f8").tofile(b_path)
    meta = {
        "n": n, "seed": seed, "dtype": "float64", "byte_order": "little-endian",
        "layout": "row-major, no header", "generator": f"numpy {np.__version__} default_rng (PCG64)",
        "distribution": "uniform[-1, 1)", "draw_order": "A then B from the same generator",
        "sha256": {a_path.name: sha256(a_path), b_path.name: sha256(b_path)},
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def write_checksums(out_dir=OUT_DIR):
    lines = [f"{sha256(p)}  {p.name}" for p in sorted(out_dir.glob("*.bin"))]
    (out_dir / "checksums.sha256").write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="experiment JSON with 'sizes' (list) and 'seed'")
    ap.add_argument("--n", type=int, nargs="*", default=[])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force", action="store_true", help="regenerate even if files exist")
    args = ap.parse_args()

    sizes, seed = list(args.n), args.seed
    if args.config:
        cfg = json.loads(Path(args.config).read_text())
        sizes += cfg["inputs"]["sizes"]
        seed = cfg["inputs"]["seed"]
    if not sizes:
        ap.error("give --config or --n")
    for n in sorted(set(sizes)):
        meta = generate(n, seed, force=args.force)
        print(f"n={n} seed={seed}: {', '.join(meta['sha256'])}")
    write_checksums()
    print(f"checksums -> {OUT_DIR / 'checksums.sha256'}")


if __name__ == "__main__":
    main()
