#!/usr/bin/env python3
"""Generate the companion package source tree in package/ (manifest, data file, artwork).

usage: tools/gen_package.py

Then build the installable zip with eden-duo-companions' tools/build_dualscreen_package.py
(see tools/build_package.sh).

v1 shows one page, "Party": every character whose record has a level (joined), in character
table order, with level, HP, EP and CP, plus mira. Data locations are documented in
design/DATA.md. The static art (background, card frames, gear badges, portrait rings) is
original artwork drawn by design/render.py. The game's own pictures (busts, AT-bar icons) are
not shipped: the manifest names them as romfs: sources, read from the player's own game files
at run time (decoded from raw NVN XTX by the runtime).
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "design"))
import render  # noqa: E402  (design/render.py)
from render import C, Page, font  # noqa: E402

TITLE_ID = "01007A2027548000"
BUILD16 = "5EA394E096752EE3"          # update 1.0.3 (v327680)
VERSION = "0.5.0"   # keep in step with tools/build_package.sh's argument
MIN_RUNTIME = 24                      # Peanuts Native 0.1.x carries runtime 24
PKG = os.path.join(ROOT, "package")
DS = os.path.join(PKG, "dualscreen")
IMG = os.path.join(DS, "img")

# Character table: [main+0x879628] + 0x1145A4 + id*0x39C0 is that character's HP.
CHAR_HP = 0x1145A4
CHAR_STRIDE = 0x39C0
SLOTS = 4                              # first four table entries (v1: joined = level > 0)
# Each table entry holds its character id (u32 at HP-0xc). design/characters.json (made by
# tools/extract_chars.py from t_name/t_status) maps the id to the name the game shows and to
# its picture key; the pictures themselves are read from the player's romfs at run time.
CHARS = {int(k): v for k, v in
         json.load(open(os.path.join(ROOT, "design", "characters.json"))).items()}
PIC_IDS = 200                          # ids above this are one-off guests without pictures
ROMFS_IMG = "romfs:/asset/nx/image/"


def char_pictures(kind):
    """src_names list indexed by character id: kind "bust" (avfc) or "face" (at_c)."""
    out = []
    for cid in range(PIC_IDS):
        c = CHARS.get(cid)
        if c and c[kind]:
            out.append(f"{ROMFS_IMG}avfc{c['key'][1:]}.xtx" if kind == "bust"
                       else f"{ROMFS_IMG}at_{c['key']}.xtx")
        else:
            out.append("file:img/portrait_q.png" if kind == "bust" else "file:img/face_q.png")
    return out


CHAR_NAMES = {str(cid): c["name"] for cid, c in CHARS.items()}
# Every AT-bar icon key in the game (file names only, from the base romfs: at_<key>.xtx). A
# unit record's +0x40 names its key ("c5000", "m5201", "m5201_b").
AT_KEYS = [k for k in open(os.path.join(ROOT, "design", "at_icon_keys.txt")).read().split()]

# Battle slot array: [main+0x879470] + 0xba0 + slot*0x30 (see design/DATA.md). Party units fill
# the first slots and their +0x1d00 is 0, so an enemy chain through +0x1d00 fails (hides) there.
BATTLE_ROOT = "main+0x879470"
BATTLE_SLOTS = 12
ENEMY_ROWS = 7                         # rows that fit above the party strip
# Target panel name: the text is inline at [[main+0x8791a8]+0x238]+0x720, but a cstring point
# must end on a pointer to the text, so use the UI's own pointer to that buffer (found on boot 1,
# checked on boot 4): [[[main+0x8791a0]+0x1f08]+0x92d0]+0xfd68 -> text.
TARGET_PTR = ["main+0x8791a0", "0x1f08", "0x92d0", "0x0"]
TARGET_OFF = "0xfd68"
# Every battle actor (party or enemy) points at its static record at +0x1b0: the monster table
# record for an enemy, the character record for a party member. The record's display name
# pointer is at +0x198. (A party actor's +0x3440 link to its character-table entry is NOT
# usable: one boot showed it pointing back at the actor itself, so the party strip still uses
# the character table in table order; see design/DATA.md.)
UNIT_REC, REC_NAME, REC_ICON = "0x1b0", 0x198, 0x40

# Layout (canvas 1240x1080), same as design/field.png
CARD_W, CARD_H = 560, 350
ROW_W, ROW_H, ROW_DY, ROW_Y = 760, 84, 96, 122     # battle page enemy rows
PARTY_Y, PARTY_DY = 806, 68                         # battle page party strip
BRAVE_PARTY = (480, 181)                            # gear centres (number drawn on top)
BRAVE_BATTLE = (1150, 416)


def card_origin(i):
    return 40 + (i % 2) * 600, 268 + (i // 2) * 400


def rgba(col, a=255):
    r, g, b = C[col] if isinstance(col, str) else col
    return f"#{a:02X}{r:02X}{g:02X}{b:02X}"


# -- data file ------------------------------------------------------------------------------

def data_file():
    def enemy(off):
        # slot i -> S=[R+0xbb0+i*0x30] -> unit U=[S] -> stats [U+0x1d00] -> field
        return {"type": "u32", "count": BATTLE_SLOTS, "offset": hex(off),
                "ptr": [BATTLE_ROOT, {"offset": "0xbb0", "stride": "0x30", "index": "$i"},
                        "0x0", "0x1d00", "0x0"]}

    def unit(*hops, off, typ="u32"):
        # slot i -> S=[R+0xbb0+i*0x30] -> unit U=[S] -> hops...
        return {"type": typ, "count": BATTLE_SLOTS, "offset": hex(off),
                "ptr": [BATTLE_ROOT, {"offset": "0xbb0", "stride": "0x30", "index": "$i"},
                        "0x0", *hops]}

    def field(off, count=SLOTS, typ="u32"):
        return {"type": typ, "ptr": ["main+0x879628", "0x0"], "offset": hex(CHAR_HP + off),
                "count": count, "stride": CHAR_STRIDE}
    return {
        "_game": "Trails in the Sky 2nd Chapter",
        "_build": "1.0.3 (v327680), build 5EA394E096752EE3D04DEBFCEA6BF9114277D0B4",
        "_layout": ("object O = [main+0x879628] (alias region). Character table at O+0x1145A4 "
                    "+ id*0x39C0 = HP; -8 level, -4 EXP, +4 max HP, +8/+0xC EP/max, "
                    "+0x10/+0x14 CP/max. Mira u32 at O+0x20B648. Battle: R=[main+0x879470], slot i "
                    "S=[R+0xbb0+i*0x30], unit [S], enemy stats [unit+0x1d00] (+0xc HP, +0x10 "
                    "max, +4 level); [R+0xbb0]+0 (slot 0's unit) is non-zero only in a command battle. "
                    "Brave Gauge u32 at [R+0x6540]+0x4c. Unit name: [[unit+0x1b0]+0x198] -> text. "
                    "See design/DATA.md."),
        "points": {
            "cid": field(-0x0c),
            "lv": field(-0x08),
            "hp": field(0x00),
            "hpmax": field(0x04),
            "ep": field(0x08),
            "epmax": field(0x0C),
            "cp": field(0x10),
            "cpmax": field(0x14),
            "mira": {"type": "u32", "ptr": ["main+0x879628", "0x0"], "offset": "0x20b648"},
            # command battle (design/DATA.md "Battle slot array")
            # low half of slot 0's unit pointer: non-zero only while a command battle runs
            "bunit0": {"type": "u32", "ptr": [BATTLE_ROOT, "0xbb0", "0x0"], "offset": "0x0"},
            # Brave Gauge points (0..5), the field HUD gear's number
            "brave": {"type": "u32", "ptr": [BATTLE_ROOT, "0x6540", "0x0"], "offset": "0x4c"},
            "elv": enemy(0x4),
            "ehp": enemy(0xc),
            "ehpmax": enemy(0x10),
            # per slot: display name (enemy or party member)
            "uname": unit(UNIT_REC, "0x0", off=REC_NAME, typ="cstring"),
            # per slot: AT-bar icon key ("m5201"), mapped to a picture by sprite_map
            "uicon": unit(UNIT_REC, "0x0", off=REC_ICON, typ="cstring"),
            "target_name": {"type": "cstring", "ptr": TARGET_PTR, "offset": TARGET_OFF},
        },
    }


# -- artwork --------------------------------------------------------------------------------

def art():
    shutil.rmtree(IMG, ignore_errors=True)   # generated: start clean, no stale pictures
    os.makedirs(IMG)
    # background: marble, title band, mira panel (text drawn by the runtime)
    p = Page()
    p.metal_band(0, 96, "Party")
    p.cream_panel(32, 122, 1176, 118)
    p.small_caps(60, 182, "Mira", 30, fill=C["gold"], outline=C["brown"])
    p.d.line((260, 140, 260, 222), fill=C["rule"], width=2)
    p.small_caps(300, 182, "Brave", 30, fill=C["gold"], outline=C["brown"])
    p.gear_badge(BRAVE_PARTY[0], BRAVE_PARTY[1], 40, "")
    p.d.line((560, 140, 560, 222), fill=C["rule"], width=2)
    p.img.save(os.path.join(IMG, "bg_party.png"))

    # card frame: navy stat box with gear badge and HP/EP/CP labels, transparent elsewhere
    p = Page((CARD_W + 20, CARD_H + 30), transparent=True)
    p.navy_box(0, 172, CARD_W, 176)
    p.gear_badge(30, 178, 40, "")
    for k, label in enumerate(("HP", "EP", "CP")):
        p.d.text((30, 250 + k * 40), label, font=font("bold", 26), fill=(240, 244, 248),
                 anchor="lm", stroke_width=2, stroke_fill=C["num_outline"])
    p.img.save(os.path.join(IMG, "card.png"))

    # battle background: band, target panel (navy, like the mockup's turn-order column)
    p = Page()
    p.metal_band(0, 96, "Battle")
    p.navy_box(824, 126, 384, 220, slant=0)
    p.small_caps(848, 166, "Target", 26, fill=(255, 255, 255), outline=C["num_outline"])
    p.navy_box(824, 366, 384, 100, slant=0)
    p.small_caps(848, 416, "Brave", 26, fill=(255, 255, 255), outline=C["num_outline"])
    p.gear_badge(BRAVE_BATTLE[0], BRAVE_BATTLE[1], 38, "")
    p.navy_box(824, 486, 384, 290, slant=0)
    p.small_caps(848, 526, "Turn Order", 26, fill=(255, 255, 255), outline=C["num_outline"])
    p.d.text((848, 580), "not found yet", font=font("body", 26), fill=(150, 170, 186))
    p.img.save(os.path.join(IMG, "bg_battle.png"))

    # enemy row: cream panel with an empty nameplate (name and level drawn by the runtime)
    p = Page((ROW_W + 8, ROW_H + 8), transparent=True)
    p.cream_panel(2, 2, ROW_W, ROW_H)
    p.header_bar(136, 10, 400, "", h=34, size=22)
    p.img.save(os.path.join(IMG, "enemy_row.png"))

    # party strip row (battle page): navy box, HP/EP/CP labels
    p = Page((1180, 66), transparent=True)
    p.navy_box(0, 2, 1170, 62, slant=18)
    for x, label in ((290, "HP"), (660, "EP"), (890, "CP")):
        p.d.text((x, 33), label, font=font("bold", 24), fill=(240, 244, 248), anchor="lm",
                 stroke_width=2, stroke_fill=C["num_outline"])
    p.img.save(os.path.join(IMG, "party_row.png"))

    # portrait ring (the game's bust is drawn over it) and "?" pictures for an id without one
    p = Page((200, 200), transparent=True)
    p.portrait(100, 100, 92, "anelace", "")
    p.img.save(os.path.join(IMG, "portrait_ring.png"))
    p = Page((200, 200), transparent=True)
    p.portrait(100, 100, 92, "anelace", "?")
    p.img.save(os.path.join(IMG, "portrait_q.png"))
    p = Page((128, 64), transparent=True)
    p.d.text((64, 32), "?", font=font("serif", 44), fill=(255, 255, 255), anchor="mm",
             stroke_width=2, stroke_fill=(60, 40, 30))
    p.img.save(os.path.join(IMG, "face_q.png"))


# -- manifest -------------------------------------------------------------------------------

def tabs(current):
    """Two tap targets in the title band: switch between the pages by hand."""
    w = []
    for k, (pid, label) in enumerate((("party", "Party"), ("battle", "Battle"))):
        x = 760 + k * 230
        on = pid == current
        w.append({"type": "button", "rect": [x, 22, 210, 52], "text": label, "text_scale": 3,
                  "align": "center", "pill": True, "on_tap": f"go_{pid}",
                  "color": rgba("num_white") if on else rgba("ink"),
                  "bg": rgba("navy_a") if on else rgba("cream", 200)})
    return w


def brave_digit(cx, cy):
    return {"type": "value", "rect": [cx, cy - 16, 0, 0], "bind": "brave", "align": "center",
            "text_scale": 4, "italic": True, "color": rgba("num_white")}


BUSTS = char_pictures("bust")
FACES = char_pictures("face")


def party_page():
    w = [{"type": "image", "rect": [0, 0, 1240, 1080], "src": "file:img/bg_party.png"}]
    w += tabs("party")
    w.append({"type": "value", "rect": [1180, 162, 0, 0], "bind": "mira", "align": "right",
              "text_scale": 5, "italic": True, "color": rgba("ink")})
    w.append(brave_digit(*BRAVE_PARTY))
    for i in range(SLOTS):
        x, y = card_origin(i)
        show = f"lv{i}"
        w.append({"type": "image", "rect": [x + CARD_W // 2 - 100, y - 4, 200, 200],
                  "src": "file:img/portrait_ring.png", "need_bind": show})
        # the game's bust for this member's character id (under the card, which covers the
        # shoulders); "?" for an id without one
        w.append({"type": "image", "rect": [x + CARD_W // 2 - 115, y - 62, 230, 230],
                  "bind": f"cid{i}", "src_names": BUSTS, "need_bind": show})
        w.append({"type": "image", "rect": [x, y, CARD_W + 20, CARD_H + 30],
                  "src": "file:img/card.png", "need_bind": show})
        w.append({"type": "value", "rect": [x + 30, y + 166, 0, 0], "bind": f"lv{i}",
                  "align": "center", "text_scale": 3, "italic": True,
                  "color": rgba("num_white"), "need_bind": show})
        w.append({"type": "label", "rect": [x + 82, y + 186, 0, 0], "text_bind": f"cid{i}",
                  "text_map": CHAR_NAMES,
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
    return {"id": "party", "widgets": w}


def battle_page():
    w = [{"type": "image", "rect": [0, 0, 1240, 1080], "src": "file:img/bg_battle.png"}]
    w += tabs("battle")
    w.append(brave_digit(*BRAVE_BATTLE))
    # target panel
    w.append({"type": "label", "rect": [848, 230, 0, 0], "bind_text": "target_name",
              "text_scale": 4, "color": rgba("num_white"), "wrap_width": 340, "max_lines": 2})
    # enemy rows: one template per widget, repeated over the battle slots and packed so that
    # empty slots and party slots (whose enemy chain fails) leave no gap
    rep = {"repeat": BATTLE_SLOTS, "repeat_dy": ROW_DY, "pack": True,
           "hide_bind": "ehp{i}", "keep_min": 1}
    x0, y0 = 32, ROW_Y
    w.append(dict(rep, type="image", rect=[x0 - 2, y0 - 2, ROW_W + 8, ROW_H + 8],
                  src="file:img/enemy_row.png"))
    w.append(dict(rep, type="image", rect=[x0 + 12, y0 + 12, 112, 56], src_bind="uicon{i}"))
    w.append(dict(rep, type="label", rect=[x0 + 156, y0 + 14, 0, 0], bind_text="uname{i}",
                  text_scale=3, color=rgba("num_white"), wrap_width=270, max_lines=1))
    w.append(dict(rep, type="label", rect=[x0 + 446, y0 + 14, 0, 0], text="Lv",
                  text_scale=3, color=rgba("num_white")))
    w.append(dict(rep, type="value", rect=[x0 + 486, y0 + 14, 0, 0], bind="elv{i}",
                  text_scale=3, color=rgba("num_white")))
    # not italic: the sheared pixel font turned "/" into ":'" on the Thor
    w.append(dict(rep, type="value", rect=[x0 + ROW_W - 24, y0 + 16, 0, 0], bind="ehp{i}",
                  max_bind="ehpmax{i}", max_sep=" / ", align="right", text_scale=3,
                  color=rgba("ink")))
    w.append(dict(rep, type="bar", rect=[x0 + 136, y0 + 56, ROW_W - 160, 14], bind="ehp{i}",
                  max_bind="ehpmax{i}", color=rgba("en_b"), bg=rgba("track"), frame=0))
    # party strip (character table, same rule as the party page: joined = level > 0)
    for i in range(SLOTS):
        y = PARTY_Y + i * PARTY_DY
        show = f"lv{i}"
        w.append({"type": "image", "rect": [40, y, 1180, 66], "src": "file:img/party_row.png",
                  "need_bind": show})
        w.append({"type": "image", "rect": [52, y + 5, 112, 56], "bind": f"cid{i}",
                  "src_names": FACES, "need_bind": show})
        w.append({"type": "label", "rect": [172, y + 20, 0, 0], "text_bind": f"cid{i}",
                  "text_map": CHAR_NAMES,
                  "text_scale": 3, "color": rgba("num_white"), "need_bind": show,
                  "wrap_width": 110, "max_lines": 1})
        for key, x, wbar, col, ncol in (("hp", 340, 280, "hp_b", "num_white"),
                                        ("ep", 710, 140, "ep_b", "num_yellow"),
                                        ("cp", 940, 190, "cp_b", "num_yellow")):
            w.append({"type": "bar", "rect": [x, y + 44, wbar, 8], "bind": f"{key}{i}",
                      "max_bind": f"{key}max{i}", "color": rgba(col), "bg": rgba("track"),
                      "frame": 0, "need_bind": show})
            w.append({"type": "value", "rect": [x + wbar, y + 8, 0, 0], "bind": f"{key}{i}",
                      "align": "right", "text_scale": 3, "italic": True, "color": rgba(ncol),
                      "need_bind": show})
    return {"id": "battle", "widgets": w}


def manifest():
    return {
        "format": 1,
        "title_id": TITLE_ID,
        "name": "Trails in the Sky 2nd Chapter dual screen",
        "min_runtime": MIN_RUNTIME,
        "canvas_w": 1240,
        "canvas_h": 1080,
        "background": rgba("marble_lo"),
        "_note": "Generated by tools/gen_package.py; edit that, not this file.",
        "pages": [party_page(), battle_page()],
        # AT-bar icon key (a unit record's +0x40) -> the game's own picture
        "sprite_map": {k: f"{ROMFS_IMG}at_{k}.xtx" for k in AT_KEYS},
        "actions": {
            "go_party": {"kind": "page", "page": "party", "transition": "fade",
                         "duration_ms": 150},
            "go_battle": {"kind": "page", "page": "battle", "transition": "fade",
                          "duration_ms": 150},
        },
        # follow the game: battle page while a command battle runs, party page otherwise
        "derived": [{"name": "in_battle", "cmp": "ne", "a": "bunit0", "b": 0}],
        "page_binds": [{"point": "in_battle", "equals": 1,
                        "when_equal": {"page": "battle", "transition": "fade",
                                       "duration_ms": 200},
                        "when_not_equal": {"page": "party", "transition": "fade",
                                           "duration_ms": 200}}],
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
