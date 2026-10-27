"""Weapons, spell effects, UI pieces, the title screen and the character creation background."""

import math
from core import Canvas, RgbCanvas, hashf, hash2, mix, shade
import characters as C
import font as F

# ---------------------------------------------------------------------------------------------------------------------
# Weapons (16x16, pointing up, grip near the bottom center).
# ---------------------------------------------------------------------------------------------------------------------

WEAPON_PALETTE = [(0, 0, 0), (24, 18, 22), (230, 234, 240), (170, 176, 188), (110, 114, 128), (150, 104, 60),
                  (100, 66, 36), (250, 210, 80), (180, 130, 40), (90, 180, 255), (200, 110, 255), (90, 190, 70),
                  (240, 236, 220), (220, 50, 40), (250, 250, 250), (160, 255, 200)]
WEAPONS = ['sword', 'hammer', 'bow', 'dagger', 'staff_priest', 'staff_mage', 'staff_warlock', 'staff_druid', 'mace']


def weapon(kind):
    c = Canvas(16, 16)
    if kind == 'sword':
        c.rect(7, 1, 2, 10, 2)
        c.rect(8, 1, 1, 10, 3)
        c.set(7, 0, 2)
        c.rect(5, 11, 6, 1, 7)
        c.rect(7, 12, 2, 3, 6)
        c.rect(7, 15, 2, 1, 7)
    elif kind == 'hammer':
        c.rect(7, 4, 2, 12, 5)
        c.rect(4, 1, 8, 5, 3)
        c.rect(4, 1, 8, 1, 2)
        c.rect(4, 5, 8, 1, 4)
        c.rect(7, 2, 2, 2, 7)
    elif kind == 'bow':
        for y in range(1, 15):
            x = 5 + int(round(3 * math.sin((y - 1) / 13 * math.pi)))
            c.set(x, y, 5)
            c.set(x + 1, y, 6)
        c.vline(5, 1, 14, 14)
        c.rect(8, 7, 2, 2, 7)
    elif kind == 'dagger':
        c.rect(7, 5, 2, 6, 2)
        c.rect(8, 5, 1, 6, 3)
        c.set(7, 4, 2)
        c.rect(5, 11, 6, 1, 4)
        c.rect(7, 12, 2, 3, 13)
    elif kind.startswith('staff'):
        wood = 5 if kind != 'staff_warlock' else 4
        c.rect(7, 4, 2, 12, wood)
        c.rect(8, 4, 1, 12, 6 if wood == 5 else 1)
        if kind == 'staff_priest':
            c.rect(6, 0, 4, 5, 7)
            c.rect(7, 1, 2, 3, 14)
        elif kind == 'staff_mage':
            c.rect(6, 1, 4, 4, 10)
            c.rect(6, 1, 1, 1, 14)
            c.rect(5, 4, 6, 1, 8)
        elif kind == 'staff_warlock':
            c.rect(5, 0, 6, 5, 12)
            c.rect(6, 2, 1, 1, 15)
            c.rect(9, 2, 1, 1, 15)
            c.rect(7, 4, 2, 1, 1)
        else:
            c.rect(5, 0, 2, 3, 11)
            c.rect(9, 0, 2, 3, 11)
            c.rect(6, 2, 4, 3, 5)
            c.set(7, 0, 15)
    elif kind == 'mace':
        c.rect(7, 6, 2, 10, 5)
        c.rect(5, 1, 6, 6, 3)
        c.rect(5, 1, 6, 1, 2)
        c.set(4, 3, 4)
        c.set(11, 3, 4)
        c.set(7, 0, 4)
        c.rect(6, 3, 4, 2, 9)
    c.outline(1)
    return c


# ---------------------------------------------------------------------------------------------------------------------
# Spell effects (16x16). Shared palette.
# ---------------------------------------------------------------------------------------------------------------------

FX_PALETTE = [(0, 0, 0), (40, 20, 30), (255, 140, 30), (255, 230, 90), (220, 50, 30), (40, 110, 230),
              (140, 210, 255), (255, 255, 255), (170, 80, 230), (80, 30, 120), (90, 210, 70), (190, 255, 140),
              (150, 104, 60), (150, 150, 160), (250, 210, 80), (255, 150, 220)]
FX = ['fireball', 'fireball2', 'frostbolt', 'frostbolt2', 'shadowbolt', 'shadowbolt2', 'smite', 'smite2',
      'lightning', 'lightning2', 'wrath', 'wrath2', 'arrow_h', 'arrow_v', 'hit', 'hit2', 'heal', 'heal2',
      'shield', 'sparkle']


def orb(c, core, mid, outer, r, trail, phase):
    for i in range(4):
        x = 4 - i * 2 + phase
        c.ellipse(x + 6, 8 + (i % 2) * (1 if phase else -1), 2.5 - i * 0.5, 2.0 - i * 0.4, trail)
    c.ellipse(9, 8, r + 1, r + 1, outer)
    c.ellipse(9, 8, r, r, mid)
    c.ellipse(9.5, 7.5, r - 1.5, r - 1.5, core)


def fx(kind):
    c = Canvas(16, 16)
    p = 1 if kind.endswith('2') else 0
    if kind.startswith('fireball'):
        orb(c, 3, 2, 4, 3.5, 4, p)
    elif kind.startswith('frostbolt'):
        orb(c, 7, 6, 5, 3.5, 6, p)
        c.set(6, 4 + p, 7)
        c.set(12, 11 - p, 7)
    elif kind.startswith('shadowbolt'):
        orb(c, 8, 9, 1, 3.5, 9, p)
        c.set(10, 7, 15)
    elif kind.startswith('smite'):
        for a in range(8):
            ang = a * math.pi / 4 + p * math.pi / 8
            r = 6 if a % 2 == 0 else 4
            c.line(8, 8, int(8 + math.cos(ang) * r), int(8 + math.sin(ang) * r), 3)
        c.ellipse(8, 8, 2.5, 2.5, 7)
    elif kind.startswith('lightning'):
        pts = [(2, 8), (5, 5), (7, 10), (10, 4), (12, 9), (15, 7)] if not p else \
              [(1, 7), (4, 10), (7, 5), (9, 11), (12, 6), (15, 8)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line(x0, y0, x1, y1, 7)
            c.line(x0, y0 + 1, x1, y1 + 1, 6)
        c.outline(5)
    elif kind.startswith('wrath'):
        orb(c, 11, 10, 1, 3.0, 10, p)
        c.set(9, 3, 11)
        c.set(13, 12, 11)
    elif kind == 'arrow_h':
        c.hline(2, 12, 8, 12)
        c.rect(12, 7, 2, 3, 13)
        c.set(14, 8, 13)
        c.rect(1, 6, 2, 1, 7)
        c.rect(1, 10, 2, 1, 7)
        c.outline(1)
    elif kind == 'arrow_v':
        c.vline(8, 3, 13, 12)
        c.rect(7, 1, 3, 2, 13)
        c.set(8, 0, 13)
        c.rect(6, 13, 1, 2, 7)
        c.rect(10, 13, 1, 2, 7)
        c.outline(1)
    elif kind.startswith('hit'):
        r = 6 if p else 4
        for a in range(8):
            ang = a * math.pi / 4 + (math.pi / 8 if p else 0)
            rr = r if a % 2 == 0 else r - 2
            c.line(8, 8, int(8 + math.cos(ang) * rr), int(8 + math.sin(ang) * rr), 7 if a % 2 else 3)
        c.ellipse(8, 8, 1.5, 1.5, 7)
    elif kind.startswith('heal'):
        for (x, y) in ((4, 10), (11, 6), (7, 3), (12, 12)):
            y -= p * 2
            c.set(x, y, 11)
            c.set(x - 1, y, 10)
            c.set(x + 1, y, 10)
            c.set(x, y - 1, 10)
            c.set(x, y + 1, 10)
            c.set(x, y, 7)
    elif kind == 'shield':
        for a in range(32):
            ang = a / 32 * 2 * math.pi
            c.set(int(8 + math.cos(ang) * 7), int(8 + math.sin(ang) * 7), 14)
            c.set(int(8 + math.cos(ang) * 6), int(8 + math.sin(ang) * 6), 3)
    elif kind == 'sparkle':
        c.vline(8, 2, 14, 3)
        c.hline(2, 14, 8, 3)
        c.rect(7, 7, 3, 3, 7)
        c.set(5, 5, 14)
        c.set(11, 11, 14)
        c.set(5, 11, 14)
        c.set(11, 5, 14)
    return c


def ring(color_outer, color_inner, radius, size=32):
    c = Canvas(size, size)
    for a in range(96):
        ang = a / 96 * 2 * math.pi
        for dr, col in ((0, color_outer), (-1, color_inner)):
            c.set(int(size / 2 + math.cos(ang) * (radius + dr)), int(size / 2 + math.sin(ang) * (radius + dr) * 0.6), col)
    return c


def big_fx():
    """32x32 frames: frost nova ring (3), level up burst (3), holy column (2)."""
    frames = []
    for r in (6, 10, 14):
        f = ring(6, 7, r)
        for i in range(6):
            ang = i * math.pi / 3
            f.set(int(16 + math.cos(ang) * r), int(16 + math.sin(ang) * r * 0.6) - 1, 7)
        frames.append(f)
    for k in range(3):
        f = Canvas(32, 32)
        for a in range(12):
            ang = a * math.pi / 6 + k * 0.2
            r0, r1 = 3 + k * 3, 7 + k * 4
            f.line(int(16 + math.cos(ang) * r0), int(16 + math.sin(ang) * r0), int(16 + math.cos(ang) * r1),
                   int(16 + math.sin(ang) * r1), 14 if a % 2 else 3)
        frames.append(f)
    for k in range(2):
        f = Canvas(32, 32)
        for y in range(32):
            for x in range(10 + k, 22 - k):
                if hashf(x, y + k * 7, 3) < 0.35:
                    f.set(x, y, 3 if hashf(x, y, 5) < 0.5 else 7)
        frames.append(f)
    return frames


# ---------------------------------------------------------------------------------------------------------------------
# UI pieces (8x8 bars, 16x16 icons...). Shared palette.
# ---------------------------------------------------------------------------------------------------------------------

UI_PALETTE = [(0, 0, 0), (16, 12, 16), (60, 52, 50), (60, 200, 60), (30, 110, 30), (50, 110, 230), (30, 60, 140),
              (220, 50, 40), (120, 24, 20), (250, 220, 60), (150, 120, 20), (170, 90, 230), (90, 40, 140),
              (250, 250, 240), (210, 170, 70), (120, 100, 60)]
BAR_COLORS = {'hp': (3, 4), 'mana': (5, 6), 'rage': (7, 8), 'energy': (9, 10), 'xp': (11, 12), 'enemy': (7, 8)}
BARS = ['hp', 'mana', 'rage', 'energy', 'xp']


def bar_frames():
    frames = []
    for name in BARS:
        light, dark = BAR_COLORS[name]
        for fill in range(9):
            c = Canvas(8, 8)
            c.rect(0, 1, 8, 6, 2)
            c.rect(0, 1, fill, 5, light)
            c.rect(0, 5, fill, 1, dark)
            if fill:
                c.rect(0, 2, fill, 1, 13 if name != 'xp' else 11)
                c.rect(0, 2, fill, 1, light)
            c.hline(0, 7, 0, 1)
            c.hline(0, 7, 7, 1)
            frames.append(c)
    # Bar caps.
    for side in (0, 1):
        c = Canvas(8, 8)
        x = 7 if side == 0 else 0
        c.vline(x, 0, 7, 1)
        c.vline(x + (1 if side == 0 else -1), 1, 6, 14)
        frames.append(c)
    return frames


def quest_marks():
    frames = []
    for kind in ('!', '?', '?grey'):
        c = Canvas(8, 16)
        col, dark = (9, 10) if kind != '?grey' else (2, 1)
        if kind == '!':
            c.rect(3, 1, 3, 9, col)
            c.rect(5, 1, 1, 9, dark)
            c.rect(3, 12, 3, 3, col)
        else:
            c.rect(2, 1, 5, 2, col)
            c.rect(5, 3, 2, 3, col)
            c.rect(3, 6, 3, 2, col)
            c.rect(3, 8, 2, 2, col)
            c.rect(3, 12, 2, 3, col)
            c.rect(6, 3, 1, 3, dark)
        c.outline(1)
        frames.append(c)
    return frames


def target_ring():
    frames = []
    for col in (7, 9, 3):
        c = Canvas(32, 16)
        for a in range(64):
            ang = a / 64 * 2 * math.pi
            c.set(int(16 + math.cos(ang) * 11), int(8 + math.sin(ang) * 4.5), col)
        frames.append(c)
    return frames


def cursor():
    c = Canvas(32, 32)
    for (x, y, dx, dy) in ((4, 4, 1, 1), (27, 4, -1, 1), (4, 27, 1, -1), (27, 27, -1, -1)):
        for i in range(5):
            c.set(x + dx * i, y, 9)
            c.set(x, y + dy * i, 9)
            c.set(x + dx * i, y + dy, 14)
            c.set(x + dx, y + dy * i, 14)
    return c


CLASS_ORDER = ['warrior', 'paladin', 'hunter', 'rogue', 'priest', 'shaman', 'mage', 'warlock', 'druid']
# Classic class colors (used for icon backgrounds).
CLASS_TINTS = {'warrior': (199, 156, 110), 'paladin': (245, 140, 186), 'hunter': (171, 212, 115),
               'rogue': (255, 245, 105), 'priest': (240, 240, 240), 'shaman': (0, 112, 222),
               'mage': (105, 204, 240), 'warlock': (148, 130, 201), 'druid': (255, 125, 10)}


def class_icon(cls):
    """Returns an RgbCanvas 16x16 icon."""
    img = RgbCanvas(16, 16)
    tint = CLASS_TINTS[cls]
    img.rect(0, 0, 16, 16, lambda x, y: shade(tint, 0.35 + 0.3 * (1 - y / 16)))
    w = weapon({'warrior': 'sword', 'paladin': 'hammer', 'hunter': 'bow', 'rogue': 'dagger', 'priest': 'staff_priest',
                'shaman': 'mace', 'mage': 'staff_mage', 'warlock': 'staff_warlock', 'druid': 'staff_druid'}[cls])
    if cls == 'warrior':
        # Sword over a shield.
        img.ellipse(8, 9, 5, 5.5, (150, 40, 30))
        img.ellipse(8, 9, 3, 3.5, (200, 170, 60))
    if cls == 'mage':
        img.ellipse(11, 5, 3, 3, (255, 140, 30))
        img.ellipse(11, 5, 1.5, 1.5, (255, 240, 120))
    if cls == 'shaman':
        img.line(12, 1, 9, 7, (255, 255, 160))
        img.line(9, 7, 13, 8, (255, 255, 160))
        img.line(13, 8, 10, 14, (255, 255, 160))
    img.blit_indexed(w, 0, 0, WEAPON_PALETTE)
    for i in range(16):
        img.set(i, 0, (250, 220, 120))
        img.set(i, 15, (90, 70, 30))
        img.set(0, i, (250, 220, 120))
        img.set(15, i, (90, 70, 30))
    return img


def race_icon(race):
    """16x16 portrait using the race's front head art and its palette."""
    img = RgbCanvas(16, 16)
    pal = C.palette(race, C.CLASS_COLORS['warrior'])
    horde = race in ('orc', 'undead', 'tauren', 'troll')
    bg = (120, 30, 24) if horde else (30, 50, 120)
    img.rect(0, 0, 16, 16, lambda x, y: shade(bg, 0.7 + 0.5 * (1 - y / 16)))
    head = Canvas(16, 16)
    rows = C.HEADS[race]['front']
    top = max(1, (16 - len(rows)) // 2 + 1)
    head.ascii(8 - len(rows[0]) // 2, top, rows, C.MAP)
    head.outline(C.O)
    img.blit_indexed(head, 0, 0, pal)
    for i in range(16):
        img.set(i, 0, (250, 220, 120))
        img.set(i, 15, (90, 70, 30))
        img.set(0, i, (250, 220, 120))
        img.set(15, i, (90, 70, 30))
    return img


def to_indexed(images, max_colors=15):
    """Converts several RgbCanvas to indexed Canvas sharing one 16 colors palette (median-ish reduction)."""
    counts = {}
    for img in images:
        for row in img.px:
            for c in row:
                if c is not None:
                    k = (int(c[0]) >> 3, int(c[1]) >> 3, int(c[2]) >> 3)
                    counts[k] = counts.get(k, 0) + 1
    colors = sorted(counts, key=lambda k: -counts[k])
    # Greedy merge until the palette fits.
    while len(colors) > max_colors:
        best = None
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                a, b = colors[i], colors[j]
                d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
                if best is None or d < best[0]:
                    best = (d, i, j)
        _, i, j = best
        colors.pop(j)
    pal = [(0, 0, 0)] + [(k[0] << 3, k[1] << 3, k[2] << 3) for k in colors]
    out = []
    for img in images:
        c = Canvas(img.w, img.h)
        for y in range(img.h):
            for x in range(img.w):
                p = img.px[y][x]
                if p is None:
                    continue
                k = (int(p[0]) >> 3, int(p[1]) >> 3, int(p[2]) >> 3)
                best, bi = None, 1
                for i, q in enumerate(colors):
                    d = (q[0] - k[0]) ** 2 + (q[1] - k[1]) ** 2 + (q[2] - k[2]) ** 2
                    if best is None or d < best:
                        best, bi = d, i + 1
                c.px[y][x] = bi
        out.append(c)
    return out, pal


def crest(horde):
    img = RgbCanvas(32, 32)
    if not horde:
        # Alliance: blue shield with a golden lion-ish emblem.
        for y in range(2, 30):
            hw = 13 if y < 18 else int(13 - (y - 18) * 1.1)
            for x in range(16 - hw, 16 + hw):
                img.set(x, y, (40, 70, 170) if x < 16 else (30, 54, 140))
        for y in range(2, 30):
            hw = 13 if y < 18 else int(13 - (y - 18) * 1.1)
            img.set(16 - hw - 1, y, (240, 200, 80))
            img.set(16 + hw, y, (240, 200, 80))
        img.rect(3, 1, 26, 2, (240, 200, 80))
        gold = (250, 214, 90)
        dark_gold = (190, 130, 40)
        # Lion head: spiky mane, lighter face, eyes and muzzle.
        for a in range(14):
            ang = a / 14 * 2 * math.pi
            img.line(16, 15, int(round(16 + math.cos(ang) * 10)), int(round(15 + math.sin(ang) * 10)), dark_gold)
        img.ellipse(16, 15, 8, 8, dark_gold)
        img.ellipse(16, 15, 6.5, 7, gold)
        img.ellipse(16, 18, 3.5, 3, (255, 236, 150))
        img.rect(12, 13, 2, 2, (40, 30, 30))
        img.rect(19, 13, 2, 2, (40, 30, 30))
        img.rect(15, 17, 3, 2, (60, 30, 20))
        img.rect(16, 19, 1, 2, (60, 30, 20))
    else:
        # Horde: spiked iron ring on a red field with a dark tusked emblem.
        iron = (40, 34, 34)
        for a in range(10):
            ang = a / 10 * 2 * math.pi - math.pi / 2
            x0, y0 = 16 + math.cos(ang) * 11, 16 + math.sin(ang) * 11
            x1, y1 = 16 + math.cos(ang) * 15.5, 16 + math.sin(ang) * 15.5
            img.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), iron)
        img.ellipse(16, 16, 13, 13, iron)
        img.ellipse(16, 16, 11, 11, (180, 30, 24))
        # Snarling orc face with tusks.
        img.ellipse(16, 17, 7.5, 8, iron)
        img.rect(11, 10, 11, 3, iron)
        img.rect(12, 14, 3, 2, (255, 210, 60))
        img.rect(18, 14, 3, 2, (255, 210, 60))
        img.rect(13, 21, 7, 1, (120, 20, 16))
        for x0, x1 in ((12, 10), (20, 22)):
            img.line(x0, 22, x1, 16, (240, 232, 210))
            img.line(x0 + (1 if x0 < 16 else -1), 22, x1 + (1 if x0 < 16 else -1), 17, (240, 232, 210))
    return img


# ---------------------------------------------------------------------------------------------------------------------
# Big text for logos: scaled font glyphs with a gold bevel.
# ---------------------------------------------------------------------------------------------------------------------

def draw_logo_text(img, text, x, y, scale, top, bottom, outline=(30, 16, 8), spacing=1):
    cx = x
    for ch in text:
        rows = F.G[ch]
        gw = max(len(r) for r in rows)
        for gy, row in enumerate(rows):
            for gx, p in enumerate(row):
                if p != '#':
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        py = gy * scale + sy
                        t = py / (7 * scale)
                        col = mix(top, bottom, t)
                        if sy == 0 and (gy == 0 or rows[gy - 1][gx:gx + 1] != '#'):
                            col = shade(top, 1.25)
                        img.set(cx + gx * scale + sx, y + py, col)
        cx += (gw + spacing) * scale
    img.outline(outline)
    return cx


def text_width(text, scale, spacing=1):
    return sum((max(len(r) for r in F.G[ch]) + spacing) * scale for ch in text) - spacing * scale


def title_bg():
    W_, H_ = 256, 256
    img = RgbCanvas(W_, H_)
    # Night sky.
    for y in range(H_):
        col = mix((10, 14, 40), (60, 40, 90), min(1.0, y / 120))
        for x in range(W_):
            c = col
            if hashf(x, y, 9) < 0.006 and y < 100:
                c = (250, 250, 230)
            img.px[y][x] = c
    # Moon.
    img.ellipse(120, 100, 22, 22, (240, 236, 210))
    img.ellipse(127, 95, 20, 20, mix((10, 14, 40), (60, 40, 90), 95 / 120))
    # Mountains.
    for x in range(W_):
        h1 = 96 + int(14 * math.sin(x * 0.045) + 8 * math.sin(x * 0.13 + 1))
        h2 = 116 + int(8 * math.sin(x * 0.07 + 2) + 5 * math.sin(x * 0.21))
        for y in range(h1, H_):
            img.px[y][x] = (40, 34, 70) if y < h1 + 3 and (x // 3) % 2 else (30, 26, 56)
        for y in range(h2, H_):
            img.px[y][x] = (22, 30, 40)
    # Alliance castle (left) and Horde fortress (right).
    for (bx, by, bw, bh) in ((10, 104, 12, 30), (24, 96, 14, 38), (40, 108, 10, 26)):
        img.rect(bx, by, bw, bh, (60, 64, 90))
        img.rect(bx - 1, by - 8, bw + 2, 8, (40, 60, 140))
        for k in range(0, bw, 4):
            img.rect(bx + k, by + 8, 2, 3, (250, 220, 120))
    for (bx, by, bw, bh) in ((206, 106, 16, 28), (224, 98, 14, 36)):
        img.rect(bx, by, bw, bh, (70, 40, 34))
        for k in range(0, bw, 4):
            img.line(bx + k, by, bx + k + 2, by - 7, (200, 190, 170))
        img.rect(bx + 4, by + 10, 4, 4, (255, 140, 40))
    # Ground glow.
    for y in range(134, 160):
        for x in range(W_):
            img.px[y][x] = mix((22, 30, 40), (12, 12, 20), (y - 134) / 26)
    # Logo.
    gold_top, gold_bottom = (255, 236, 140), (190, 110, 20)
    w1 = text_width('POCKET', 3)
    draw_logo_text(img, 'POCKET', 120 - w1 // 2, 18, 3, gold_top, gold_bottom)
    w2 = text_width('of', 2)
    draw_logo_text(img, 'of', 120 - w2 // 2, 44, 2, (240, 240, 250), (150, 150, 170))
    w3 = text_width('WARCRAFT', 4)
    draw_logo_text(img, 'WARCRAFT', 120 - w3 // 2, 60, 4, gold_top, gold_bottom)
    # Crests next to the logo.
    img.blit(crest(False), 14, 22)
    img.blit(crest(True), 194, 14)
    return img


def charselect_bg():
    W_, H_ = 256, 256
    img = RgbCanvas(W_, H_)
    for y in range(H_):
        for x in range(W_):
            # Dark stone hall.
            t = y / 160
            base = mix((26, 24, 34), (54, 46, 52), t)
            if (y // 12) % 2 == 0:
                bx = x % 24
            else:
                bx = (x + 12) % 24
            if y % 12 == 0 or bx == 0:
                base = shade(base, 0.7)
            elif hashf(x, y, 3) < 0.08:
                base = shade(base, 1.15)
            img.px[y][x] = base
    # Side panels.
    for (px, col) in ((2, (24, 40, 96)), (182, (100, 24, 20))):
        for y in range(4, 112):
            for x in range(px, px + 56):
                img.px[y][x] = shade(col, 0.8 + 0.3 * (1 - (y - 4) / 112))
        for x in range(px, px + 56):
            img.px[4][x] = (230, 190, 80)
            img.px[111][x] = (130, 96, 40)
        for y in range(4, 112):
            img.px[y][px] = (230, 190, 80)
            img.px[y][px + 55] = (130, 96, 40)
    # Center pedestal.
    img.ellipse(120, 102, 30, 8, (90, 84, 96))
    img.ellipse(120, 100, 28, 7, (130, 124, 136))
    img.ellipse(120, 100, 22, 5, (160, 154, 166))
    # Glow behind the hero.
    for y in range(26, 100):
        for x in range(90, 150):
            d = math.hypot((x - 120) / 30.0, (y - 66) / 40.0)
            if d < 1.0 and hashf(x, y, 8) < (1 - d) * 0.5:
                img.px[y][x] = mix(img.px[y][x], (110, 100, 70), 0.35)
    # Bottom bar for the classes.
    for y in range(114, 160):
        for x in range(W_):
            img.px[y][x] = mix((20, 16, 20), (36, 30, 34), (y - 114) / 46)
    for x in range(W_):
        img.px[114][x] = (230, 190, 80)
    return img


def panel_bg():
    """UI panel bg: a WoW style dialog box at the bottom of the screen (used for dialogs and the quest log)."""
    img = RgbCanvas(256, 256)

    def box(x0, y0, w, h):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c = (16, 18, 40)
                if y in (y0, y0 + h - 1) or x in (x0, x0 + w - 1):
                    c = (240, 200, 90)
                elif y in (y0 + 1, y0 + h - 2) or x in (x0 + 1, x0 + w - 2):
                    c = (120, 86, 30)
                elif y in (y0 + 2, y0 + h - 3) or x in (x0 + 2, x0 + w - 3):
                    c = (8, 8, 20)
                img.px[y][x] = c

    box(0, 104, 240, 56)    # dialog box (visible at the bottom of the screen)
    return img
