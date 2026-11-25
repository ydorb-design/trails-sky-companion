#!/usr/bin/env python3
"""Compare gdbmem.py snapshots: find addresses whose value matches a sequence across snapshots.

usage:
  memdiff.py <snapA> <valA> <snapB> <valB> [<snapC> <valC> ...] [--types u16,u32,...]

Each snapshot directory is paired with the value the game showed when it was taken
(e.g. HP 1510 in snapA, 1406 in snapB). Prints every address that held exactly those values,
for each candidate encoding (default: u16 u32 s32 u64 f32 f64; all naturally aligned).

Needs numpy.
"""
import json
import os
import sys

import numpy as np

DTYPES = {
    "u16": np.dtype("<u2"), "u32": np.dtype("<u4"), "s32": np.dtype("<i4"),
    "u64": np.dtype("<u8"), "f32": np.dtype("<f4"), "f64": np.dtype("<f8"),
}


def load(snapdir):
    with open(os.path.join(snapdir, "index.json")) as f:
        index = json.load(f)
    return {m["start"]: os.path.join(snapdir, m["file"]) for m in index}


def main(argv):
    args = argv[1:]
    types = list(DTYPES)
    if "--types" in args:
        i = args.index("--types")
        types = args[i + 1].split(",")
        del args[i:i + 2]
    if len(args) < 4 or len(args) % 2:
        print(__doc__)
        return 2
    pairs = [(load(args[i]), float(args[i + 1])) for i in range(0, len(args), 2)]
    common = set(pairs[0][0])
    for snap, _ in pairs[1:]:
        common &= set(snap)
    hits = 0
    for start in sorted(common):
        sizes = {os.path.getsize(snap[start]) for snap, _ in pairs}
        if len(sizes) != 1:
            continue
        for t in types:
            dt = DTYPES[t]
            mask = None
            for snap, want in pairs:
                arr = np.memmap(snap[start], dtype=dt, mode="r")
                m = arr == dt.type(want)
                mask = m if mask is None else (mask & m)
                if not mask.any():
                    break
            if mask is None or not mask.any():
                continue
            for idx in np.flatnonzero(mask)[:200]:
                print(f"{t:>4} {start + int(idx) * dt.itemsize:#014x}")
                hits += 1
    print(f"{hits} hit(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
