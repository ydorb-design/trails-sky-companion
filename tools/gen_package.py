#!/usr/bin/env python3
"""Generate the companion package source tree in package/ (manifest, data file, artwork).

usage: tools/gen_package.py

Then build the installable zip with eden-duo-companions' tools/build_dualscreen_package.py
(see tools/build_package.sh).

v1 shows one page, "Party": every character whose record has a level (joined), in character
table order, with level, HP, EP and CP, plus mira. Data locations are documented in
design/DATA.md. The static art (background, card frames, gear badges, placeholder portraits)
is original artwork drawn by design/render.py, not game assets; the game's own portraits and
font come later.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "design"))
import render  # noqa: E402  (design/render.py)
from render import C, Page, font  # noqa: E402

TITLE_ID = "01007A2027548000"
BUILD16 = "5EA394E096752EE3"          # update 1.0.3 (v327680)
VERSION = "0.1.0"   # keep in step with tools/build_package.sh's argument
MIN_RUNTIME = 24                      # Peanuts Native 0.1.x carries runtime 24
PKG = os.path.join(ROOT, "package")
DS = os.path.join(PKG, "dualscreen")
IMG = os.path.join(DS, "img")

# Character table: [main+0x879628] + 0x1145A4 + id*0x39C0 is that character's HP.
CHAR_HP = 0x1145A4
CHAR_STRIDE = 0x39C0
SLOTS = 4                              # first four table entries (v1: joined = level > 0)
NAMES = ["Estelle", "Anelace", "Member 3", "Member 4"]   # ids 2+ not identified yet
COLOURS = ["estelle", "anelace", "enemy", "enemy"]

# Layout (canvas 1240x1080), same as design/field.png
CARD_W, CARD_H = 560, 350


def card_origin(i):
    return 40 + (i % 2) * 600, 268 + (i // 2) * 400


def rgba(col, a=255):
    r, g, b = C[col] if isinstance(col, str) else col
    return f"#{a:02X}{r:02X}{g:02X}{b:02X}"


# -- data file ------------------------------------------------------------------------------

def data_file():
    def field(off, count=SLOTS, typ="u32"):
        return {"type": typ, "ptr": ["main+0x879628", "0x0"], "offset": hex(CHAR_HP + off),
                "count": count, "stride": CHAR_STRIDE}
    return {
        "_game": "Trails in the Sky 2nd Chapter",
        "_build": "1.0.3 (v327680), build 5EA394E096752EE3D04DEBFCEA6BF9114277D0B4",
        "_layout": ("object O = [main+0x879628] (alias region). Character table at O+0x1145A4 "
                    "+ id*0x39C0 = HP; -8 level, -4 EXP, +4 max HP, +8/+0xC EP/max, "
                    "+0x10/+0x14 CP/max. Mira u32 at O+0x20B648. See design/DATA.md."),
        "points": {
            "lv": field(-0x08),
            "hp": field(0x00),
            "hpmax": field(0x04),
            "ep": field(0x08),
            "epmax": field(0x0C),
            "cp": field(0x10),
            "cpmax": field(0x14),
            "mira": {"type": "u32", "ptr": ["main+0x879628", "0x0"], "offset": "0x20b648"},
        },
    }


# -- artwork --------------------------------------------------------------------------------

def art():
    os.makedirs(IMG, exist_ok=True)
    # background: marble, title band, mira panel (text drawn by the runtime)
    p = Page()
    p.metal_band(0, 96, "Party")
    p.cream_panel(32, 122, 1176, 118)
    p.small_caps(60, 182, "Mira", 30, fill=C["gold"], outline=C["brown"])
    p.d.line((260, 140, 260, 222), fill=C["rule"], width=2)
    p.img.save(os.path.join(IMG, "bg_party.png"))

    # card frame: navy stat box with gear badge and HP/EP/CP labels, transparent elsewhere
    p = Page((CARD_W + 20, CARD_H + 30), transparent=True)
    p.navy_box(0, 172, CARD_W, 176)
    p.gear_badge(30, 178, 40, "")
    for k, label in enumerate(("HP", "EP", "CP")):
        p.d.text((30, 250 + k * 40), label, font=font("bold", 26), fill=(240, 244, 248),
                 anchor="lm", stroke_width=2, stroke_fill=C["num_outline"])
    p.img.save(os.path.join(IMG, "card.png"))

    # placeholder portraits (the game's own portraits come later)
    for i in range(SLOTS):
        p = Page((200, 200), transparent=True)
        p.portrait(100, 100, 92, COLOURS[i], NAMES[i][0])
        p.img.save(os.path.join(IMG, f"portrait_{i}.png"))


# -- manifest -------------------------------------------------------------------------------

def manifest():
    w = []
    w.append({"type": "image", "rect": [0, 0, 1240, 1080], "src": "file:img/bg_party.png"})
    w.append({"type": "value", "rect": [1180, 162, 0, 0], "bind": "mira", "align": "right",
              "text_scale": 5, "italic": True, "color": rgba("ink")})
    for i in range(SLOTS):
        x, y = card_origin(i)
        show = f"lv{i}"
        w.append({"type": "image", "rect": [x + CARD_W // 2 - 100, y - 4, 200, 200],
                  "src": f"file:img/portrait_{i}.png", "need_bind": show})
        w.append({"type": "image", "rect": [x, y, CARD_W + 20, CARD_H + 30],
                  "src": "file:img/card.png", "need_bind": show})
        w.append({"type": "value", "rect": [x + 30, y + 166, 0, 0], "bind": f"lv{i}",
                  "align": "center", "text_scale": 3, "italic": True,
                  "color": rgba("num_white"), "need_bind": show})
        w.append({"type": "label", "rect": [x + 82, y + 186, 0, 0], "text": NAMES[i],
                  "text_scale": 4, "color": rgba("num_white"), "need_bind": show})
        for k, (key, col, ncol) in enumerate((("hp", "hp_b", "num_white"),
                                              ("ep", "ep_b", "num_yellow"),
                                              ("cp", "cp_b", "num_yellow"))):
            ry = y + 250 + k * 40
            w.append({"type": "bar", "rect": [x + 74, ry + 6, 436, 10], "bind": f"{key}{i}",
                      "max_bind": f"{key}max{i}", "color": rgba(col), "bg": rgba("track"),
                      "frame": 0, "need_bind": show})
            w.append({"type": "value", "rect": [x + 510, ry - 22, 0, 0], "bind": f"{key}{i}",
                      "align": "right", "text_scale": 4, "italic": True, "color": rgba(ncol),
                      "need_bind": show})
    return {
        "format": 1,
        "title_id": TITLE_ID,
        "name": "Trails in the Sky 2nd Chapter dual screen",
        "min_runtime": MIN_RUNTIME,
        "canvas_w": 1240,
        "canvas_h": 1080,
        "background": rgba("marble_lo"),
        "_note": "Generated by tools/gen_package.py; edit that, not this file.",
        "pages": [{"id": "party", "widgets": w}],
    }


def package_json():
    return {"format": 1, "type": "dual-screen-mod", "title_id": TITLE_ID,
            "name": "Trails in the Sky 2nd Chapter dual screen", "version": VERSION,
            "min_runtime": MIN_RUNTIME}


def main():
    os.makedirs(DS, exist_ok=True)
    art()
    for path, obj in ((os.path.join(PKG, "package.json"), package_json()),
                      (os.path.join(DS, "manifest.json"), manifest()),
                      (os.path.join(DS, f"{BUILD16}.json"), data_file())):
        with open(path, "w") as f:
            json.dump(obj, f, indent=1)
            f.write("\n")
        print(path)


if __name__ == "__main__":
    main()
