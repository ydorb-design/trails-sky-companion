#!/usr/bin/env python3
"""Draw the companion page mockups at the real canvas size (1240x1080).

usage: design/render.py            writes design/field.png and design/battle.png

Only the primitives the companion runtime has: rectangles (optionally rounded), text labels,
numeric values and bars. Values are the reference values from the test saves (design/DATA.md).
Portraits are placeholder discs; the real portraits get decoded from the player's romfs later.
"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/noto"

C = {
    "bg": "#0d1626", "panel": "#16233a", "panel_hi": "#1d2e4b", "edge": "#3a5378",
    "gold": "#d8b35a", "text": "#eef2f8", "muted": "#9fb0c8", "faint": "#4a5f80",
    "hp": "#f08a2c", "ep": "#3fb3e6", "cp": "#8fd14a", "enemy": "#d9534f",
    "track": "#0a111d", "track_edge": "#2a3a55", "lv": "#5a2a12",
    "estelle": "#c8642a", "anelace": "#7a5a3a",
}


def font(size, bold=False):
    name = "NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


class Page:
    def __init__(self):
        self.img = Image.new("RGB", (W, H), C["bg"])
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x, y, w, h, fill=None, outline=None, r=0, width=2):
        self.d.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=r, fill=fill,
                                 outline=outline, width=width)

    def text(self, x, y, s, size, color="text", bold=False, anchor="la"):
        self.d.text((x, y), s, font=font(size, bold), fill=C.get(color, color), anchor=anchor)

    def bar(self, x, y, w, h, frac, color):
        self.rect(x, y, w, h, fill=C["track"], outline=C["track_edge"], r=h // 2, width=1)
        if frac > 0:
            self.rect(x, y, max(h, int(w * frac)), h, fill=C[color], r=h // 2)

    def disc(self, cx, cy, r, color, letter, size):
        self.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C[color], outline=C["gold"], width=4)
        self.text(cx, cy, letter, size, bold=True, anchor="mm")

    def save(self, name):
        path = os.path.join(HERE, name)
        self.img.save(path)
        print(path)


def strip(p, title, subtitle, chips, objective_mark=False):
    p.rect(0, 0, W, 120, fill=C["panel"])
    p.rect(0, 117, W, 3, fill=C["gold"])
    p.text(32, 14, title, 40, bold=True)
    x = 32
    if objective_mark:
        p.text(x, 66, "!", 26, color="hp", bold=True)
        x += 24
    p.text(x, 66, subtitle, 26, color="muted")
    right = W - 32
    for label, value in reversed(chips):
        w = 200
        p.rect(right - w, 22, w, 76, fill=C["panel_hi"], outline=C["edge"], r=12)
        p.text(right - w + 20, 60, label, 20, color="gold", bold=True, anchor="lm")
        p.text(right - 20, 60, value, 34, bold=True, anchor="rm")
        right -= w + 18


def stat_row(p, x, y, w, key, frac, color, value, vmax=None, vw=230, ksize=24, vsize=30):
    p.text(x, y + 11, key, ksize, color="muted", bold=True, anchor="lm")
    bx = x + ksize * 2 + 8
    bw = w - (bx - x) - vw - 10
    p.bar(bx, y, bw, 22, frac, color)
    vx = x + w
    if vmax is not None:
        p.text(vx, y + 11, f" / {vmax}", 22, color="muted", anchor="rm")
        vx -= font(22).getlength(f" / {vmax}")
    p.text(vx, y + 11, str(value), vsize, bold=True, anchor="rm")


PARTY = [
    ("Estelle", "estelle", 25, (1607, 2035), (85, 85), (200, 200)),
    ("Anelace", "anelace", 25, (1544, 2090), (80, 80), (200, 200)),
]


def field_page():
    p = Page()
    strip(p, "Balstar Channel", "Explore the Balstar Channel",
          [("BRAVE", "5"), ("MIRA", "1000")], objective_mark=True)
    for i in range(4):
        y = 152 + i * 220
        if i >= len(PARTY):
            p.rect(32, y, 1176, 200, outline=C["track_edge"], r=16)
            p.text(W // 2, y + 100, f"party slot {i + 1}", 28, color="faint", anchor="mm")
            continue
        name, col, lv, hp, ep, cp = PARTY[i]
        p.rect(32, y, 1176, 200, fill=C["panel"], outline=C["edge"], r=16)
        p.disc(132, y + 100, 80, col, name[0], 64)
        p.d.ellipse((164, y + 128, 228, y + 192), fill=C["lv"], outline=C["gold"], width=3)
        p.text(196, y + 160, str(lv), 26, bold=True, anchor="mm")
        p.text(252, y + 18, name, 38, bold=True)
        for j, (k, v, c) in enumerate((("HP", hp, "hp"), ("EP", ep, "ep"), ("CP", cp, "cp"))):
            stat_row(p, 252, y + 80 + j * 40, 930, k, v[0] / v[1], c, v[0], v[1])
    p.text(32, H - 34, "Field page: party at a glance. Tap a card for that character's status "
           "(later).", 20, color="faint")
    p.save("field.png")


def battle_page():
    p = Page()
    strip(p, "Battle — Balstar Channel", "4 enemies", [("BRAVE", "5")])
    p.text(32, 140, "ENEMIES", 24, color="gold", bold=True)
    enemies = [("Enemy 1", 0.72, False), ("Enemy 2", 1.0, False), ("Enemy 3", 1.0, False),
               ("Enemy 4", 0.0, True)]
    for i, (name, frac, dead) in enumerate(enemies):
        y = 176 + i * 120
        p.rect(32, y, 760, 104, fill=C["panel"], outline=C["edge"], r=12)
        p.text(54, y + 12, name, 30, color="faint" if dead else "text", bold=True)
        p.text(770, y + 30, "0 / —" if dead else "— / —", 28, color="faint" if dead else "text",
               bold=True, anchor="rm")
        p.bar(54, y + 66, 716, 20, frac, "enemy")

    p.text(824, 140, "TURN ORDER", 24, color="gold", bold=True)
    p.rect(824, 176, 384, 600, fill=C["panel"], outline=C["edge"], r=12)
    turns = [("Estelle", "estelle", "", True), ("Enemy 2", "enemy", "", False),
             ("Anelace", "anelace", "HP +10%", False), ("Enemy 1", "enemy", "", False),
             ("Enemy 3", "enemy", "", False), ("Estelle", "estelle", "CRIT", False),
             ("Enemy 2", "enemy", "", False), ("Anelace", "anelace", "", False)]
    for i, (name, col, bonus, now) in enumerate(turns):
        y = 192 + i * 72
        p.rect(840, y, 352, 62, fill=C["panel_hi"], outline=C["gold"] if now else None,
               r=10, width=3)
        p.d.ellipse((854, y + 11, 894, y + 51), fill=C[col])
        p.text(908, y + 31, name, 26, bold=True, anchor="lm")
        if bonus:
            p.text(1180, y + 31, bonus, 20, color="gold", bold=True, anchor="rm")

    live = [(1543, 2035), (85, 85), (200, 200)], [(1544, 2090), (80, 80), (200, 200)]
    for i, ((name, col, *_), vals) in enumerate(zip(PARTY, live)):
        y = 808 + i * 132
        p.rect(32, y, 1176, 120, fill=C["panel"], outline=C["edge"], r=12)
        p.disc(76, y + 60, 44, col, name[0], 38)
        p.text(140, y + 8, name, 28, bold=True)
        for j, ((v, vmax), (k, c)) in enumerate(zip(vals, (("HP", "hp"), ("EP", "ep"),
                                                             ("CP", "cp")))):
            stat_row(p, 140 + j * 352, y + 66, 330, k, v / vmax, c, v, vw=96, ksize=20,
                     vsize=24)
    p.save("battle.png")


if __name__ == "__main__":
    field_page()
    battle_page()
