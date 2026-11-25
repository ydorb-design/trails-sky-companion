#!/usr/bin/env python3
"""Minimal GDB remote (RSP) client for Eden Duo's gdbstub: memory map, snapshots, reads.

Connecting pauses emulation and the stub has no detach, so every command ends by sending
`c` (continue) -- otherwise the game stays frozen.

Enable the stub in the *test* profile only (tools/reset_test_profile.sh makes one):
  sdl2-config.ini: use_gdbstub=true, gdbstub_port=6543

usage:
  gdbmem.py info                      process layout and module bases
  gdbmem.py mappings                  every mapping (address range, permissions, state)
  gdbmem.py snap <outdir>             dump every readable+writable mapping to <outdir>
  gdbmem.py base <nso>                load address of a module (e.g. the dumped `main`)
  gdbmem.py objsnap <main> <out> [lo hi]   just the game-state object, for quick diffs
  gdbmem.py read <hexaddr> <len>      hex dump

Snapshots are one raw file per mapping (<start>.bin) plus index.json.
"""
import json
import os
import re
import socket
import sys

HOST = os.environ.get("GDB_HOST", "127.0.0.1")
PORT = int(os.environ.get("GDB_PORT", "6543"))
CHUNK = 0x100000  # try big reads first; fall back to what the stub accepts


class Stub:
    def __init__(self, host=HOST, port=PORT):
        self.s = socket.create_connection((host, port), timeout=60)
        self.buf = bytearray()
        self.noack = False
        self._ack_mode_handshake()

    # -- framing ---------------------------------------------------------------------------
    def _send(self, payload: str):
        cs = sum(payload.encode()) & 0xFF
        self.s.sendall(f"${payload}#{cs:02x}".encode())
        if not self.noack:
            self._expect_ack()

    def _expect_ack(self):
        while True:
            c = self._recv_byte()
            if c == b"+":
                return
            if c == b"-":
                raise IOError("stub NAKed a packet")

    def _fill(self):
        data = self.s.recv(1 << 22)
        if not data:
            raise IOError("stub closed the connection")
        self.buf += data

    def _recv_byte(self):
        if not self.buf:
            self._fill()
        c = self.buf[:1]
        del self.buf[:1]
        return bytes(c)

    def _recv_packet(self) -> str:
        # Scan the buffer in bulk: per-byte slicing made big reads quadratic.
        while True:
            start = self.buf.find(b"$")
            if start >= 0:
                end = self.buf.find(b"#", start)
                if end >= 0 and len(self.buf) >= end + 3:
                    payload = bytes(self.buf[start + 1:end])
                    del self.buf[:end + 3]  # '#' plus two checksum digits
                    break
            self._fill()
        if not self.noack:
            self.s.sendall(b"+")
        return payload.decode("latin-1")

    def cmd(self, payload: str) -> str:
        self._send(payload)
        return self._recv_packet()

    def _ack_mode_handshake(self):
        self.s.sendall(b"+")
        self.cmd("qSupported:multiprocess+")
        if self.cmd("QStartNoAckMode") == "OK":
            self.noack = True

    # -- operations ------------------------------------------------------------------------
    def monitor(self, text: str) -> str:
        reply = self.cmd("qRcmd," + text.encode().hex())
        return bytes.fromhex(reply).decode("utf-8", "replace") if reply and reply[0] != "E" else reply

    def read(self, addr: int, size: int) -> bytes:
        # An error reply is exactly "Exx"; data can legitimately start with the hex digit E,
        # so judge by length, not by the first character.
        out = bytearray()
        chunk = CHUNK
        while size > 0:
            n = min(size, chunk)
            reply = self.cmd(f"m{addr:x},{n:x}")
            if len(reply) != 2 * n:
                if chunk > 0x1000:
                    chunk //= 4  # retry this spot smaller; next call starts big again
                    continue
                raise IOError(f"read failed at {addr:#x}+{n:#x}: {reply[:20]!r}")
            out += bytes.fromhex(reply)
            addr += n
            size -= n
        return bytes(out)

    def resume(self):
        # `c` gets no reply until the next stop; send it and close.
        payload = "c"
        cs = sum(payload.encode()) & 0xFF
        self.s.sendall(f"${payload}#{cs:02x}".encode())
        self.s.close()


MAP_RE = re.compile(r"(0x[0-9a-f]+) - (0x[0-9a-f]+) (\S+) (\S+)")


def parse_mappings(text: str):
    maps = []
    for line in text.splitlines():
        m = MAP_RE.search(line)
        if m:
            lo, hi, perm, state = int(m[1], 16), int(m[2], 16), m[3], m[4]
            maps.append({"start": lo, "end": hi + 1, "perm": perm, "state": state})
    return maps


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    op = argv[1]
    stub = Stub()
    try:
        if op == "info":
            print(stub.monitor("info"))
        elif op == "mappings":
            print(stub.monitor("mappings"))
        elif op == "base":
            # `monitor info` lists no modules in this build, so find the module by its text
            # segment: the r-x Code mapping whose size is the NSO's text size, page-rounded.
            import struct
            with open(argv[2], "rb") as f:
                hdr = f.read(0x40)
            text_size = struct.unpack_from("<I", hdr, 0x18)[0]
            want = (text_size + 0xFFF) & ~0xFFF
            hits = [m for m in parse_mappings(stub.monitor("mappings"))
                    if m["state"] == "Code" and "x" in m["perm"] and m["end"] - m["start"] == want]
            if len(hits) != 1:
                print(f"expected one r-x mapping of {want:#x} bytes, found {len(hits)}",
                      file=sys.stderr)
                return 1
            print(f"{hits[0]['start']:#x}")
        elif op == "objsnap":
            # objsnap <main_base> <out.bin> [lo hi]: the game-state object window only (~22 MB),
            # [main+0x879628]+lo .. +hi. Much faster than a full snap for before/after diffs.
            import struct
            base = int(argv[2], 16)
            lo = int(argv[4], 0) if len(argv) > 4 else 0
            hi = int(argv[5], 0) if len(argv) > 5 else 0xC60000
            root = struct.unpack("<Q", stub.read(base + 0x879628, 8))[0]
            data = stub.read(root + lo, hi - lo)
            with open(argv[3], "wb") as f:
                f.write(data)
            print(f"object {root:#x}+{lo:#x}..{hi:#x} -> {argv[3]}")
        elif op == "read":
            addr, n = int(argv[2], 16), int(argv[3], 0)
            data = stub.read(addr, n)
            for off in range(0, len(data), 16):
                row = data[off:off + 16]
                print(f"{addr + off:012x}: {row.hex(' ')}")
        elif op == "snap":
            outdir = argv[2]
            os.makedirs(outdir, exist_ok=True)
            maps = [m for m in parse_mappings(stub.monitor("mappings"))
                    if "R" in m["perm"].upper() and "W" in m["perm"].upper()]
            total = 0
            index = []
            for m in maps:
                size = m["end"] - m["start"]
                try:
                    data = stub.read(m["start"], size)
                except IOError as e:
                    print(f"skip {m['start']:#x} ({size:#x}): {e}", file=sys.stderr)
                    continue
                name = f"{m['start']:012x}.bin"
                with open(os.path.join(outdir, name), "wb") as f:
                    f.write(data)
                index.append({**m, "file": name})
                total += size
            with open(os.path.join(outdir, "index.json"), "w") as f:
                json.dump(index, f, indent=1)
            print(f"snapshot: {len(index)} mappings, {total >> 20} MiB -> {outdir}")
        else:
            print(__doc__)
            return 2
    finally:
        stub.resume()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
