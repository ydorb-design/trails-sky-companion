#!/usr/bin/env python3
"""Build design/characters.json (character id -> display name and picture key) from a romfs dump.

usage: tools/extract_chars.py [romfs_dir=~/trails-files/romfs-base/romfs]

The game's party-member table in memory stores each member's character id (u32 at HP-0xc, see
design/DATA.md). t_name.tbl maps a character id to its party model ("chr5000p"); t_status.tbl
maps that model to the name the game shows in battle (+0x198) and its picture key (+0x40,
"c5000": the AT-bar face is at_<key>.xtx, the bust avfc<key minus the leading c>.xtx). Only the
mapping is kept (no game art); the package reads the pictures from the player's own romfs.
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def tbl_sections(b):
    """#TBL file -> {section name: [(entry offset), ...]}."""
    assert b[:4] == b"#TBL", "not a #TBL file"
    out = {}
    for i in range(struct.unpack_from("<I", b, 4)[0]):
        o = 8 + i * 0x50
        name = b[o:o + 0x40].split(b"\0")[0].decode()
        off, esz, cnt = struct.unpack_from("<III", b, o + 0x44)
        out.setdefault(name, [off + k * esz for k in range(cnt)])
    return out


def cstr(b, at):
    off = struct.unpack_from("<Q", b, at)[0]
    if not 0 < off < len(b):
        return ""
    return b[off:b.find(b"\0", off)].decode("utf-8", "replace")


def map_key(m):
    """'mp0010_05' -> 1000005, 'mp6011' -> 601100 (same formula as the package's map_key expr)."""
    if len(m) not in (6, 9) or not m.startswith("mp") or not m[2:6].isdigit():
        return None
    if len(m) == 9 and not (m[6] == "_" and m[7:9].isdigit()):
        return None
    return int(m[2:6]) * 100 + (int(m[7:9]) if len(m) == 9 else 0)


def main():
    romfs = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/trails-files/romfs-base/romfs")
    names = open(os.path.join(romfs, "table_en", "t_name.tbl"), "rb").read()
    status = open(os.path.join(romfs, "table_en", "t_status.tbl"), "rb").read()
    by_model = {}
    for e in tbl_sections(status)["StatusParam"]:
        model = cstr(status, e)
        if model.startswith("chr") and model.endswith("p") and model not in by_model:
            by_model[model] = {"name": cstr(status, e + 0x198), "key": cstr(status, e + 0x40)}
    chars = {}
    for e in tbl_sections(names)["NameTableData"]:
        cid = struct.unpack_from("<Q", names, e)[0]
        model = cstr(names, e + 0x40)         # party model, "npc" for non-party entries
        if cid == 0xFFFF or model not in by_model or str(cid) in chars:
            continue
        chars[str(cid)] = dict(by_model[model], model=model)
    # which of the game's pictures exist for each (the package only names those)
    images = set(os.listdir(os.path.join(romfs, "asset", "nx", "image")))
    for c in chars.values():
        c["face"] = f"at_{c['key']}.xtx" in images           # AT-bar face, 128x64
        c["bust"] = f"avfc{c['key'][1:]}.xtx" in images      # bust, 256x256
    # place names by map: the game keeps the current map's name ("mp6011", "mp0010_05") in its
    # state object; the package turns its characters into a number (map_key) and looks it up
    places = {}
    pl = open(os.path.join(romfs, "table_en", "t_place.tbl"), "rb").read()
    for e in tbl_sections(pl)["PlaceTableData"]:
        k, name = map_key(cstr(pl, e + 0x8)), cstr(pl, e + 0x60)
        if k is not None and name and str(k) not in places:   # table order: region first
            places[str(k)] = name
    with open(os.path.join(ROOT, "design", "places.json"), "w") as f:
        json.dump(places, f, indent=1, ensure_ascii=False)
    print("places", len(places))
    out = os.path.join(ROOT, "design", "characters.json")
    with open(out, "w") as f:
        json.dump(dict(sorted(chars.items(), key=lambda kv: int(kv[0]))), f, indent=1,
                  ensure_ascii=False)
    print(out, len(chars), "characters")


if __name__ == "__main__":
    main()
