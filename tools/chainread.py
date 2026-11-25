#!/usr/bin/env python3
"""Resolve a data-file style pointer chain live over the gdbstub and dump what it lands on.

usage: chainread.py <main_base_hex> <len> <hop0> [hop1 ...]
  hop0 is "main+0x..."; each later hop dereferences the previous address then adds the hop.
  Prints each intermediate address, then a hex dump of <len> bytes at the final address.
"""
import struct
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from gdbmem import Stub  # noqa: E402


def main():
    base = int(sys.argv[1], 16); n = int(sys.argv[2], 0); hops = sys.argv[3:]
    s = Stub()
    try:
        addr = base + int(hops[0].split("+")[1], 16)
        print("hop0", hex(addr))
        for h in hops[1:]:
            p = struct.unpack("<Q", s.read(addr, 8))[0]
            addr = p + int(h, 16)
            print("->", hex(p), "+", h, "=", hex(addr))
        b = s.read(addr, n)
    finally:
        s.resume()
    for i in range(0, n, 16):
        row = b[i:i + 16]
        print(f"{addr + i:012x}: {row.hex(' ')}")


if __name__ == "__main__":
    main()
