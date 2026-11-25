#!/usr/bin/env python3
"""Read the command-battle slot array live (see design/DATA.md, "Battle slot array").

usage: battleread.py <main_base_hex> [slots=12]
"""
import struct
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from gdbmem import Stub  # noqa: E402


def main():
    mb = int(sys.argv[1], 16); n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    s = Stub()
    q = lambda a: struct.unpack("<Q", s.read(a, 8))[0]
    try:
        r = q(mb + 0x879470)
        for i in range(n):
            sp = q(r + 0xbb0 + i * 0x30)
            u = q(sp) if sp else 0
            if not u:
                print(i, "empty"); continue
            st = q(u + 0x1d00)
            if st:
                uid, lv, exp, hp, mx = struct.unpack("<5I", s.read(st, 20))
                print(i, f"enemy unit {u:#x} uid {uid:#x} lv {lv} hp {hp}/{mx}")
            else:
                ch = q(u + 0x3440)  # character record link; not reliable for every member
                try:
                    lv, exp, hp, mx = struct.unpack("<4I", s.read(ch + 4, 16))
                    print(i, f"party unit {u:#x} record {ch:#x} lv {lv} hp {hp}/{mx}")
                except (IOError, OSError):
                    print(i, f"party unit {u:#x} (record link {ch:#x} unreadable)")
        tgt = q(q(q(q(mb + 0x8791a0) + 0x1f08) + 0x92d0) + 0xfd68)
        print("target:", s.read(tgt, 32).split(b"\0")[0].decode("utf-8", "replace"))
    finally:
        s.resume()


if __name__ == "__main__":
    main()
