#!/usr/bin/env python3
"""Draw the companion page mockups at the real canvas size (1240x1080), in the game's UI style.

usage: design/render.py            writes design/field.png and design/battle.png

Style taken from the game's own screens (camp menu, Load screen, dialogue, field HUD):
light marble background, cream parchment panels with silver corner brackets, dark brown header
bars with a teal accent, navy stat boxes with a bronze gear level badge, thin HP/EP/CP bars,
italic outlined numbers, small-caps serif titles, cyan glow for the current item.

In the real package the ornaments (frames, brackets, gear badge, bar art), the font and the
portraits come from the game's own files, decoded from the player's romfs at runtime; here they
are approximated with plain shapes. Values are the reference values from the test saves
(design/DATA.md).
"""
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1240, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/noto"

# Sampled from the game's screens (see design/DATA.md for where each value comes from).
C = {
    "marble_hi": (220, 218, 222), "marble_lo": (195, 195, 192), "ornament": (178, 178, 176),
    "cream": (226, 224, 215), "cream_edge": (178, 172, 158), "ink": (40, 36, 32),
    "ink_soft": (110, 104, 96), "rule": (196, 192, 182),
    "brown": (39, 34, 28), "brown_text": (236, 228, 206), "teal": (40, 140, 154),
    "navy_a": (43, 66, 83), "navy_b": (30, 58, 76), "navy_edge": (120, 150, 170),
    "track": (14, 26, 34),
    "hp_a": (232, 92, 40), "hp_b": (255, 153, 49),
    "ep_a": (40, 150, 220), "ep_b": (150, 215, 240),
    "cp_a": (110, 200, 50), "cp_b": (206, 255, 132),
    "en_a": (170, 30, 30), "en_b": (240, 90, 70),
    "num_white": (255, 255, 255), "num_yellow": (249, 255, 91), "num_outline": (20, 22, 26),
    "bronze": (140, 99, 50), "bronze_hi": (196, 150, 82), "bronze_dark": (65, 44, 22),
    "silver": (205, 210, 214), "silver_dark": (120, 128, 136),
    "metal_hi": (235, 237, 237), "metal_lo": (150, 170, 186), "metal_text_edge": (30, 50, 70),
    "glow": (16, 241, 252), "gold": (216, 179, 90),
    "estelle": (200, 100, 42), "anelace": (122, 90, 58), "enemy": (150, 60, 50),
}


def font(kind, size):
    name = {
        "serif": "NotoSerif-Bold.ttf", "num": "NotoSans-BoldItalic.ttf",
        "body": "NotoSans-Medium.ttf", "bold": "NotoSans-Bold.ttf",
    }[kind]
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Page:
    def __init__(self, size=(W, H), transparent=False):
        # transparent=True: an RGBA layer (package art drawn over by the runtime's widgets)
        self.w, self.h = size
        self.img = Image.new("RGBA" if transparent else "RGB", size, (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        if not transparent:
            self.marble()

    def over(self, layer):
        """Blend an RGBA layer onto the page (alpha-composite on transparent pages)."""
        if self.img.mode == "RGBA":
            self.img.alpha_composite(layer)
        else:
            self.img.paste(layer, (0, 0), layer)

    # -- backgrounds and ornaments ----------------------------------------------------------
    def marble(self):
        for y in range(self.h):
            self.d.line((0, y, self.w, y), fill=lerp(C["marble_hi"], C["marble_lo"], y / self.h))
        # faint clockwork emblem, like the menu background line art
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        cx, cy = 150, 640
        col = C["ornament"] + (150,)
        for r in (420, 360, 250, 150):
            ld.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=6)
        for k in range(36):
            a = k * math.tau / 36
            ld.line((cx + 360 * math.cos(a), cy + 360 * math.sin(a),
                     cx + 420 * math.cos(a), cy + 420 * math.sin(a)), fill=col, width=5)
        cx, cy = 1120, 980
        for r in (260, 200):
            ld.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=5)
        self.over(layer)

    def shadow(self, box, radius=10, offset=(0, 6), alpha=90, blur=10):
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        x0, y0, x1, y1 = box
        ImageDraw.Draw(layer).rounded_rectangle(
            (x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]),
            radius=radius, fill=(0, 0, 0, alpha))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        self.over(layer)

    def glow(self, box, radius=10):
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(box, radius=radius, outline=C["glow"] + (255,),
                                                width=8)
        layer = layer.filter(ImageFilter.GaussianBlur(6))
        self.over(layer)
        self.d.rounded_rectangle(box, radius=radius, outline=C["glow"], width=3)

    # -- panels ---------------------------------------------------------------------------
    def cream_panel(self, x, y, w, h):
        self.shadow((x, y, x + w, y + h), radius=6)
        self.d.rectangle((x, y, x + w, y + h), fill=C["cream"], outline=C["cream_edge"], width=2)
        self.d.line((x + 3, y + 3, x + w - 3, y + 3), fill=(244, 242, 236), width=2)
        # silver corner brackets with a small round boss, like the Load screen frames
        L = 26
        for cx, cy, sx, sy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1),
                               (x + w, y + h, -1, -1)):
            self.d.line((cx, cy + sy * 2, cx + sx * L, cy + sy * 2), fill=C["silver_dark"], width=4)
            self.d.line((cx + sx * 2, cy, cx + sx * 2, cy + sy * L), fill=C["silver_dark"], width=4)
            self.d.line((cx + sx * 3, cy + sy * 3, cx + sx * (L - 4), cy + sy * 3), fill=C["silver"],
                        width=2)
            self.d.ellipse((cx + sx * 7 - 5, cy + sy * 7 - 5, cx + sx * 7 + 5, cy + sy * 7 + 5),
                           fill=C["silver"], outline=C["silver_dark"], width=2)

    def header_bar(self, x, y, w, text, h=46, size=28):
        """Dark brown bar with a teal accent at the left, like 'Information' and nameplates."""
        self.d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=C["brown"],
                                 outline=(90, 78, 60), width=2)
        self.d.rounded_rectangle((x + 4, y + 4, x + 16, y + h - 4), radius=6, fill=C["teal"])
        self.d.text((x + 30, y + h // 2), text, font=font("body", size), fill=C["brown_text"],
                    anchor="lm")

    def metal_band(self, y, h, title, sub=None):
        """Title band styled like the camp-menu tabs: brushed silver-blue metal, navy trim."""
        self.shadow((0, y, W, y + h), radius=0, offset=(0, 4), alpha=70, blur=6)
        for i in range(h):
            t = i / h
            col = lerp(C["metal_hi"], C["metal_lo"], t if t < .55 else 1 - (t - .55))
            self.d.line((0, y + i, W, y + i), fill=col)
        self.d.line((0, y, W, y), fill=C["metal_text_edge"], width=3)
        self.d.line((0, y + h, W, y + h), fill=C["metal_text_edge"], width=3)
        self.small_caps(40, y + h // 2 - (10 if sub else 0), title, 46)
        if sub:
            self.d.text((42, y + h - 20), sub, font=font("body", 22), fill=C["metal_text_edge"],
                        anchor="ls")

    def small_caps(self, x, y, text, size, fill=(255, 255, 255), outline=None):
        """Serif small caps: capitals full size, the rest as smaller capitals (menu tab style)."""
        outline = outline or C["metal_text_edge"]
        big, small = font("serif", size), font("serif", int(size * .78))
        for word_i, word in enumerate(text.split(" ")):
            if word_i:
                x += big.getlength(" ")
            for ch in word:
                f = big if ch.isupper() or not ch.isalpha() else small
                ch = ch.upper()
                self.d.text((x, y), ch, font=f, fill=fill, anchor="ls" if False else "lm",
                            stroke_width=3, stroke_fill=outline)
                x += f.getlength(ch)
        return x

    # -- stat pieces ------------------------------------------------------------------------
    def number(self, x, y, text, size, color, anchor="rm"):
        self.d.text((x, y), text, font=font("num", size), fill=C[color], anchor=anchor,
                    stroke_width=max(2, size // 12), stroke_fill=C["num_outline"])

    def bar(self, x, y, w, h, frac, col):
        """Thin game bar: dark track, two-tone fill, light top edge."""
        self.d.rectangle((x, y, x + w, y + h), fill=C["track"])
        fw = int(w * max(0.0, min(1.0, frac)))
        a, b = C[col + "_a"], C[col + "_b"]
        for i in range(fw):
            self.d.line((x + i, y + 1, x + i, y + h - 1), fill=lerp(a, b, i / max(1, w)))
        if fw:
            self.d.line((x, y + 1, x + fw, y + 1), fill=lerp(b, (255, 255, 255), .5))

    def navy_box(self, x, y, w, h, slant=26):
        """Navy stat box with a slanted right edge, like the camp-menu party boxes."""
        self.shadow((x, y, x + w, y + h), radius=4)
        poly = [(x, y), (x + w, y), (x + w - slant, y + h), (x, y + h)]
        mask = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        grad = Image.new("RGBA", (self.w, self.h))
        gd = ImageDraw.Draw(grad)
        for i in range(h + 1):
            gd.line((x, y + i, x + w, y + i), fill=lerp(C["navy_a"], C["navy_b"], i / h))
        self.img.paste(grad, (0, 0), mask)
        self.d.line(poly + [poly[0]], fill=C["navy_edge"], width=2)

    def gear_badge(self, cx, cy, r, text):
        """Bronze gear with a dark centre and an italic number: the game's level badge."""
        teeth = 12
        pts = []
        for k in range(teeth * 2):
            a = k * math.pi / teeth
            rr = r if k % 2 == 0 else r * .82
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        self.d.polygon(pts, fill=C["bronze"], outline=C["bronze_dark"])
        self.d.ellipse((cx - r * .74, cy - r * .74, cx + r * .74, cy + r * .74), fill=C["bronze_hi"])
        self.d.ellipse((cx - r * .6, cy - r * .6, cx + r * .6, cy + r * .6), fill=C["bronze_dark"])
        self.number(cx, cy, text, int(r * .9), "num_white", anchor="mm")

    def portrait(self, cx, cy, r, col, letter, glow=False):
        """Round portrait with a silver ring (field HUD style). Real art comes from the game."""
        if glow:
            self.glow((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), radius=r + 8)
        self.d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), fill=C["silver_dark"])
        self.d.ellipse((cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3), fill=C["silver"])
        self.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C[col])
        self.d.ellipse((cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4),
                       outline=lerp(C[col], (255, 255, 255), .25), width=2)
        self.d.text((cx, cy), letter, font=font("serif", int(r * .9)), fill=(255, 255, 255),
                    anchor="mm", stroke_width=2, stroke_fill=(60, 40, 30))

    def stat_rows(self, x, y, w, rows, label_size=26, num_size=34, gap=40, bar_h=10):
        """HP/EP/CP rows: condensed label, thin bar under the number, italic outlined value."""
        for i, (label, cur, mx, col, ncol) in enumerate(rows):
            ry = y + i * gap
            self.d.text((x, ry), label, font=font("bold", label_size), fill=(240, 244, 248),
                        anchor="lm", stroke_width=2, stroke_fill=C["num_outline"])
            bx = x + label_size * 1.7
            self.bar(int(bx), ry + 6, int(w - (bx - x)), bar_h, cur / mx, col)
            self.number(x + w, ry - 4, str(cur), num_size, ncol)

    def save(self, name):
        path = os.path.join(HERE, name)
        self.img.save(path)
        print(path)


PARTY = [
    ("Estelle", "estelle", 25, (1607, 2035), (85, 85), (200, 200)),
    ("Anelace", "anelace", 25, (1544, 2090), (80, 80), (200, 200)),
]


def party_card(p, x, y, member):
    """One party slot: portrait above, navy stat box with gear badge below (camp-menu layout)."""
    w = 560
    if member is None:
        p.d.rectangle((x, y + 150, x + w, y + 340), outline=C["ornament"], width=3)
        p.d.text((x + w // 2, y + 245), "—", font=font("serif", 40), fill=C["ornament"],
                 anchor="mm")
        return
    name, col, lv, hp, ep, cp = member
    p.portrait(x + w // 2, y + 96, 92, col, name[0])
    p.navy_box(x, y + 172, w, 176)
    p.gear_badge(x + 30, y + 178, 40, str(lv))
    p.d.text((x + 82, y + 200), name, font=font("body", 34), fill=(255, 255, 255), anchor="lm",
             stroke_width=2, stroke_fill=C["num_outline"])
    p.stat_rows(x + 30, y + 250, w - 80, [
        ("HP", hp[0], hp[1], "hp", "num_white"),
        ("EP", ep[0], ep[1], "ep", "num_yellow"),
        ("CP", cp[0], cp[1], "cp", "num_yellow"),
    ])


def field_page():
    p = Page()
    p.metal_band(0, 96, "Balstar Channel")
    # Brave Gauge as an orange gear on the band, like the field HUD
    p.gear_badge(1170, 48, 38, "5")
    p.d.text((1118, 48), "BRAVE", font=font("serif", 20), fill=C["metal_text_edge"], anchor="rm")

    p.cream_panel(32, 122, 1176, 118)
    p.header_bar(52, 138, 260, "Objective")
    p.d.text((60, 206), "Explore the Balstar Channel", font=font("body", 30), fill=C["ink"],
             anchor="lm")
    p.d.line((860, 140, 860, 222), fill=C["rule"], width=2)
    p.small_caps(892, 180, "Mira", 26, fill=C["gold"], outline=C["brown"])
    p.d.text((1180, 182), "1000", font=font("num", 44), fill=C["ink"], anchor="rm")

    slots = PARTY + [None, None]
    for i, member in enumerate(slots):
        party_card(p, 40 + (i % 2) * 600, 268 + (i // 2) * 400, member)
    p.save("field.png")


def battle_page():
    p = Page()
    p.metal_band(0, 96, "Battle", sub="Balstar Channel")
    p.gear_badge(1170, 48, 38, "5")
    p.d.text((1118, 48), "BRAVE", font=font("serif", 20), fill=C["metal_text_edge"], anchor="rm")

    # enemies: cream rows like the Load screen, nameplate like the dialogue speaker tag
    # enemy names and HP are illustrative until the battle data is found
    enemies = [("Enemy 1", 812, 1130, "target"), ("Enemy 2", 1130, 1130, ""),
               ("Enemy 3", 1130, 1130, ""), ("Enemy 4", 0, 1130, "dead")]
    for i, (name, ehp, emax, state) in enumerate(enemies):
        frac = ehp / emax
        x, y, w, h = 32, 126 + i * 132, 760, 112
        p.cream_panel(x, y, w, h)
        if state == "target":
            p.glow((x - 2, y - 2, x + w + 2, y + h + 2), radius=4)
        p.header_bar(x + 18, y + 14, 250, name, h=40, size=24)
        p.number(x + w - 24, y + 36, str(ehp), 34, "num_white")
        p.bar(x + 24, y + 72, w - 48, 16, frac, "en")
        if state == "dead":
            veil = Image.new("RGBA", (w + 4, h + 4), C["marble_lo"] + (150,))
            p.img.paste(veil, (x - 2, y - 2), veil)

    # turn order: navy column of portraits, the one acting now glows
    p.navy_box(824, 126, 384, 652, slant=0)
    p.small_caps(848, 160, "Turn Order", 26, fill=(255, 255, 255), outline=C["num_outline"])
    turns = [("Estelle", "estelle", ""), ("Enemy 2", "enemy", ""),
             ("Anelace", "anelace", "HP +10%"), ("Enemy 1", "enemy", ""),
             ("Enemy 3", "enemy", ""), ("Estelle", "estelle", "Crit"),
             ("Enemy 2", "enemy", "")]
    for i, (name, col, bonus) in enumerate(turns):
        y = 214 + i * 80 + (14 if i else 0)
        r = 34 if i == 0 else 26
        p.portrait(880, y + 4, r, col, name[0], glow=(i == 0))
        p.d.text((934, y + 4), name, font=font("body", 30 if i == 0 else 26),
                 fill=(255, 255, 255), anchor="lm", stroke_width=2, stroke_fill=C["num_outline"])
        if bonus:
            bw = font("bold", 18).getlength(bonus) + 26
            p.d.rounded_rectangle((1188 - bw, y - 12, 1188, y + 18), radius=13, fill=C["brown"],
                                  outline=C["gold"], width=2)
            p.d.text((1188 - bw / 2, y + 3), bonus, font=font("bold", 18), fill=C["gold"],
                     anchor="mm")

    # party: field-HUD style rows
    live = [((1543, 2035), (85, 85), (200, 200)), ((1544, 2090), (80, 80), (200, 200))]
    for i, (member, (hp, ep, cp)) in enumerate(zip(PARTY, live)):
        y = 806 + i * 136
        name, col = member[0], member[1]
        p.navy_box(120, y + 8, 1088, 112)
        p.portrait(84, y + 64, 56, col, name[0])
        p.d.text((172, y + 36), name, font=font("body", 30), fill=(255, 255, 255), anchor="lm",
                 stroke_width=2, stroke_fill=C["num_outline"])
        p.stat_rows(172, y + 84, 330, [("HP", hp[0], hp[1], "hp", "num_white")], num_size=30)
        p.stat_rows(540, y + 84, 260, [("EP", ep[0], ep[1], "ep", "num_yellow")], num_size=30)
        p.stat_rows(838, y + 84, 300, [("CP", cp[0], cp[1], "cp", "num_yellow")], num_size=30)
    p.save("battle.png")


if __name__ == "__main__":
    field_page()
    battle_page()
