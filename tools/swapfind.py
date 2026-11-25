#!/usr/bin/env python3
"""Find neighbouring values that swapped places between two snapshots (e.g. a party reorder).

usage: swapfind.py <snapA> <snapB> [--max 255] [--types u8,u16,u32]

Reports addresses where (x, y) in A became (y, x) in B, x != y, both <= max. Snapshots come
from tools/gdbmem.py snap; mappings are matched by start address and size.
"""
import json
import os
import sys

import numpy as np

DT = {"u8": "<u1", "u16": "<u2", "u32": "<u4"}


def main(argv):
    args = argv[1:]
    vmax, types = 255, ["u8", "u16", "u32"]
    if "--max" in args:
        i = args.index("--max"); vmax = int(args[i + 1], 0); del args[i:i + 2]
    if "--types" in args:
        i = args.index("--types"); types = args[i + 1].split(","); del args[i:i + 2]
    if len(args) != 2:
        print(__doc__)
        return 2
    a, b = (os.path.expanduser(x) for x in args)
    ia = {m["start"]: m for m in json.load(open(os.path.join(a, "index.json")))}
    ib = {m["start"]: m for m in json.load(open(os.path.join(b, "index.json")))}
    hits = 0
    for start, ma in sorted(ia.items()):
        mb = ib.get(start)
        if not mb or mb["end"] != ma["end"]:
            continue
        ra = np.fromfile(os.path.join(a, ma["file"]), np.uint8)
        rb = np.fromfile(os.path.join(b, mb["file"]), np.uint8)
        if not (ra != rb).any():
            continue
        for t in types:
            dt = np.dtype(DT[t])
            n = len(ra) // dt.itemsize
            A, B = ra[:n * dt.itemsize].view(dt), rb[:n * dt.itemsize].view(dt)
            m = ((A[:-1] != A[1:]) & (B[:-1] == A[1:]) & (B[1:] == A[:-1])
                 & (A[:-1] <= vmax) & (A[1:] <= vmax))
            for i in np.flatnonzero(m)[:50]:
                print(f"{t:>4} {start + int(i) * dt.itemsize:#014x}: "
                      f"{A[i:i + 4].tolist()} -> {B[i:i + 4].tolist()}")
                hits += 1
    print(f"{hits} hit(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
