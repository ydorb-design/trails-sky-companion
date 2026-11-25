#!/usr/bin/env python3
"""Find pointer chains from a module (e.g. main) to a target address in a gdbmem snapshot.

usage: ptrpath.py <snapdir> <main_base_hex> <main_size_hex> <target_hex> [maxoff=0x1000] [depth=5]

Indexes every 8-byte-aligned word that points into a snapshot mapping, then walks backwards
from the target: a word at S holding V with V <= T < V+maxoff makes S one hop above T.
Prints chains that start inside [main_base, main_base+main_size) in the data file's ptr form.
"""
import os
import sys

import numpy as np


def main():
    snap, mbase, msize, target = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), int(sys.argv[4], 16)
    maxoff = int(sys.argv[5], 0) if len(sys.argv) > 5 else 0x1000
    depth = int(sys.argv[6]) if len(sys.argv) > 6 else 5
    maps = sorted((int(f[:-4], 16), os.path.join(snap, f)) for f in os.listdir(snap) if f.endswith(".bin"))
    spans = [(b, b + os.path.getsize(p)) for b, p in maps]
    vals, srcs = [], []
    for b, p in maps:
        raw = np.fromfile(p, dtype="<u8")
        ok = np.zeros(len(raw), bool)
        for lo, hi in spans:
            ok |= (raw >= lo) & (raw < hi)
        idx = np.nonzero(ok)[0]
        vals.append(raw[idx]); srcs.append(b + idx.astype(np.uint64) * 8)
    vals = np.concatenate(vals); srcs = np.concatenate(srcs)
    order = np.argsort(vals); vals = vals[order]; srcs = srcs[order]
    print(f"{len(vals)} pointers indexed", file=sys.stderr)

    def parents(t):
        lo = np.searchsorted(vals, np.uint64(max(t - maxoff, 0)), "left")
        hi = np.searchsorted(vals, np.uint64(t), "right")
        return [(int(srcs[i]), t - int(vals[i])) for i in range(lo, hi)]

    frontier = [(target, [])]
    seen = {target}
    found = 0
    for d in range(depth):
        nxt = []
        for t, chain in frontier:
            for s, off in parents(t):
                c = [off] + chain
                if mbase <= s < mbase + msize:
                    hops = ", ".join(f'"{o:#x}"' for o in c)
                    print(f'depth {d+1}: ["main+{s - mbase:#x}", {hops}]')
                    found += 1
                elif s not in seen and len(nxt) < 200000:
                    seen.add(s); nxt.append((s, c))
        frontier = nxt
        print(f"depth {d+1}: frontier {len(frontier)}, found {found}", file=sys.stderr)
        if found >= 20:
            break


if __name__ == "__main__":
    main()
