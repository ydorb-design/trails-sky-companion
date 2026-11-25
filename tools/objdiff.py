#!/usr/bin/env python3
"""Compare the game-state object across snapshots by offset, so different boots line up.

The object's address changes every boot (ASLR), but fields keep their offset from it. Each
snapshot directory <snap> needs a <snap>.main file next to it ("main base: 0x..."), written
when the snapshot was taken (tools/gdbmem.py base).

usage:
  objdiff.py [--root main+0x879628] [--window -0x200000:0x1400000] [--types u32,u16,...] \
             <snapA> <valA> <snapB> <valB> [...]

Prints offsets (from the object) where every snapshot holds its value. A value of "*" accepts
anything in that snapshot, "!=N" anything but N.
"""
import json
import os
import re
import sys

import numpy as np

DTYPES = {"u8": "<u1", "u16": "<u2", "u32": "<u4", "s32": "<i4", "u64": "<u8", "f32": "<f4"}


class Snap:
    def __init__(self, path, root_off):
        self.path = path
        with open(os.path.join(path, "index.json")) as f:
            self.index = json.load(f)
        with open(path.rstrip("/") + ".main") as f:
            self.main = int(re.search(r"0x[0-9a-fA-F]+", f.read())[0], 16)
        self.root = int(np.frombuffer(self.read(self.main + root_off, 8), "<u8")[0])

    def read(self, addr, size):
        for m in self.index:
            if m["start"] <= addr and addr + size <= m["end"]:
                with open(os.path.join(self.path, m["file"]), "rb") as f:
                    f.seek(addr - m["start"])
                    return f.read(size)
        raise KeyError(f"{addr:#x}+{size:#x} not in snapshot {self.path}")

    def window(self, lo, hi):
        """Object bytes [root+lo, root+hi), clipped to the mapping that holds the root."""
        m = next(m for m in self.index if m["start"] <= self.root < m["end"])
        a0 = max(self.root + lo, m["start"])
        a1 = min(self.root + hi, m["end"])
        with open(os.path.join(self.path, m["file"]), "rb") as f:
            f.seek(a0 - m["start"])
            return a0 - self.root, f.read(a1 - a0)


def matcher(arr, spec, dt):
    if spec == "*":
        return np.ones(arr.shape, bool)
    if spec.startswith("!="):
        return arr != np.dtype(dt).type(float(spec[2:]))
    return arr == np.dtype(dt).type(float(spec))


def main(argv):
    args = argv[1:]
    opts = {"--root": "main+0x879628", "--window": "-0x200000:0x1400000",
            "--types": "u32,u16"}
    for k in list(opts):
        if k in args:
            i = args.index(k)
            opts[k] = args[i + 1]
            del args[i:i + 2]
    if len(args) < 2 or len(args) % 2:
        print(__doc__)
        return 2
    root_off = int(opts["--root"].split("+")[1], 16)
    lo, hi = (int(x, 0) for x in opts["--window"].split(":"))
    snaps = [(Snap(os.path.expanduser(args[i]), root_off), args[i + 1])
             for i in range(0, len(args), 2)]
    for s, _ in snaps:
        print(f"{s.path}: main {s.main:#x}, object {s.root:#x}", file=sys.stderr)
    wins = [(s.window(lo, hi), spec) for s, spec in snaps]
    start = max(w[0][0] for w in wins)
    end = min(w[0][0] + len(w[0][1]) for w in wins)
    hits = 0
    for t in opts["--types"].split(","):
        dt = np.dtype(DTYPES[t])
        mask = None
        for (w0, data), spec in wins:
            arr = np.frombuffer(data[start - w0:end - w0], dt, count=(end - start) // dt.itemsize)
            m = matcher(arr, spec, dt)
            mask = m if mask is None else mask & m
        for i in np.flatnonzero(mask)[:300]:
            print(f"{t:>4} object{start + int(i) * dt.itemsize:+#x}")
            hits += 1
    print(f"{hits} hit(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
