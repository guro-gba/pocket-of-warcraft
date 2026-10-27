"""Terrain textures and world objects (trees, buildings, tents...) drawn procedurally."""

import math
from core import RgbCanvas, hash2, hashf, mix, shade


def pick(colors, weights, r):
    acc = 0.0
    for c, w in zip(colors, weights):
        acc += w
        if r < acc:
            return c
    return colors[-1]


# ---------------------------------------------------------------------------------------------------------------------
# Terrains. tex(x, y, variant) returns an RGB color. Textures repeat every 16 pixels so tiles deduplicate well.
# ---------------------------------------------------------------------------------------------------------------------

class Terrain:
    def __init__(self, name, prio, tex, solid=False, variants=1, weights=None):
        self.name = name
        self.prio = prio
        self.tex = tex
        self.solid = solid
        self.variants = variants
        self.weights = weights or [1.0 / variants] * variants


def grass_tex(base, dark, light, flowers=None, seed=0):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        r = hashf(lx, ly, seed + v * 7)
        c = pick((base, dark, light), (0.72, 0.18, 0.10), r)
        # Small grass blades.
        b = hash2(lx // 4, ly // 4, seed + 31 + v) % 16
        bx, by = (b % 4), (b // 4)
        if lx % 4 == bx and (ly % 4 == by or ly % 4 == (by + 1) % 4):
            c = dark
        if lx % 4 == bx and ly % 4 == (by + 3) % 4:
            c = light
        if flowers and v == 2:
            fpos = [(3, 4), (11, 2), (7, 11), (13, 13)]
            for i, (fx, fy) in enumerate(fpos):
                if lx == fx and ly == fy:
                    c = flowers[i % len(flowers)]
                elif abs(lx - fx) + abs(ly - fy) == 1 and i % 2 == 0:
                    c = light
        return c
    return tex


def dirt_tex(base, dark, light, seed=1):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        r = hashf(lx, ly, seed + v)
        c = pick((base, dark, light), (0.7, 0.18, 0.12), r)
        pebbles = [(4, 5), (12, 10), (8, 14)] if v == 0 else [(2, 11), (10, 3)]
        for px, py in pebbles:
            if (lx, ly) == (px, py) or (lx, ly) == (px + 1, py):
                c = light
            if (lx, ly) == (px, py + 1) or (lx, ly) == (px + 1, py + 1):
                c = dark
        return c
    return tex


def cobble_tex(base, dark, light, mortar):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        row = ly // 5
        off = 4 if row % 2 else 0
        bx = (lx + off) % 8
        by = ly % 5
        if by == 4 or bx == 7:
            return mortar
        if by == 0 or bx == 0:
            return light
        if by == 3 or bx == 6:
            return dark
        return base
    return tex


def water_tex(base, dark, light):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        c = base
        if hashf(lx, ly, 77) < 0.25:
            c = dark
        # Wave crests.
        if ly in (3, 11) and ((lx + (4 if ly == 11 else 0)) % 16) in (2, 3, 4, 5):
            c = light
        if ly in (4, 12) and ((lx + (4 if ly == 12 else 0)) % 16) in (6, 7):
            c = light
        return c
    return tex


def snow_tex(base, dark, light):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        r = hashf(lx, ly, 55 + v)
        c = pick((base, dark, light), (0.75, 0.15, 0.1), r)
        if v == 1 and ((lx, ly) in ((5, 6), (6, 6), (12, 12), (13, 12))):
            c = dark
        return c
    return tex


def rock_tex(base, dark, light):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        r = hashf(lx, ly, 91 + v)
        c = pick((base, dark, light), (0.6, 0.25, 0.15), r)
        # Boulder outlines.
        cx, cy = (8, 8) if v == 0 else (6, 9)
        d = math.hypot(lx - cx + 0.5, (ly - cy + 0.5) * 1.3)
        if 5.5 < d < 6.6:
            c = dark
        elif 4.0 < d < 5.5 and ly < cy:
            c = light
        return c
    return tex


def cracked_tex(base, dark, light, seed=3):
    def tex(x, y, v):
        lx, ly = x & 15, y & 15
        r = hashf(lx, ly, seed + v)
        c = pick((base, dark, light), (0.7, 0.15, 0.15), r)
        if v == 1:
            if (lx, ly) in ((3, 3), (4, 4), (5, 4), (6, 5), (6, 6), (11, 9), (12, 10), (12, 11), (13, 12)):
                c = dark
        return c
    return tex


# ---------------------------------------------------------------------------------------------------------------------
# Object helpers.
# ---------------------------------------------------------------------------------------------------------------------

class Obj:
    """A world object. img is an RgbCanvas. Rows >= split go to the low layer (under sprites), rows above to the
    high layer (over sprites). solid: list of (x, y, w, h) rectangles in 8 pixels cells, relative to the image."""

    def __init__(self, img, split, solid):
        self.img = img
        self.split = split
        self.solid = solid


def blob_shade(colors, nx, ny, x, y, seed=0):
    """Shades a rounded volume lit from the top-left. colors: dark -> light list."""
    light = -(nx * 0.55 + ny * 0.85) + (hashf(x, y, seed) - 0.5) * 0.5
    n = len(colors)
    i = int((light + 1.0) / 2.0 * n)
    return colors[max(0, min(n - 1, i))]


def tree_round(leaves, trunk, seed=0, w=32, h=48, outline=None):
    img = RgbCanvas(w, h)
    cx = w // 2
    # Trunk.
    tw = 6
    for y in range(h - 20, h - 2):
        for x in range(cx - tw // 2, cx + tw // 2):
            c = trunk[1] if x < cx - 1 else trunk[2] if x == cx - 1 else trunk[0]
            img.set(x, y, c)
    for x in range(cx - tw // 2 - 2, cx + tw // 2 + 2):
        img.set(x, h - 2, trunk[0])
        img.set(x, h - 3, trunk[1] if x % 3 else trunk[0])
    # Canopy: cluster of circles.
    blobs = [(cx, 15, 14, 13), (cx - 7, 19, 8, 8), (cx + 7, 19, 8, 8), (cx, 8, 9, 8), (cx - 2, 24, 9, 7)]
    ol = outline or shade(leaves[0], 0.6)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny, bx=bx, by=by, rx=rx, ry=ry:
                    blob_shade(leaves, (x - cx) / 14.0, (y - 15) / 13.0, x, y, seed))
    # Leaf highlights.
    for i in range(14):
        hx = cx - 10 + hash2(i, 1, seed) % 20
        hy = 4 + hash2(i, 2, seed) % 20
        if img.get(hx, hy) is not None and img.get(hx, hy) != ol:
            img.set(hx, hy, leaves[-1])
            if img.get(hx + 1, hy + 1) not in (None, ol):
                img.set(hx + 1, hy + 1, leaves[1])
    return Obj(img, h - 16, [((w // 2 - 8) // 8, (h - 8) // 8, 2, 1)])


def tree_pine(leaves, trunk, snow=None, w=32, h=48, seed=0):
    img = RgbCanvas(w, h)
    cx = w // 2
    for y in range(h - 12, h - 2):
        for x in range(cx - 2, cx + 2):
            img.set(x, y, trunk[1] if x < cx else trunk[0])
    tiers = [(4, 14, 7), (12, 24, 11), (21, 36, 15)]
    ol = shade(leaves[0], 0.6)
    for top, bottom, half in tiers:
        for y in range(top, bottom):
            t = (y - top) / max(1, bottom - top - 1)
            hw = int(1 + t * half)
            for x in range(cx - hw - 1, cx + hw + 1):
                img.set(x, y, ol)
    for top, bottom, half in tiers:
        for y in range(top, bottom - 1):
            t = (y - top) / max(1, bottom - top - 1)
            hw = int(t * half)
            for x in range(cx - hw, cx + hw):
                side = (x - cx) / max(1, hw)
                k = 2 if side < -0.3 else (1 if side < 0.3 else 0)
                if hashf(x, y, seed) < 0.15:
                    k = max(0, k - 1)
                c = leaves[k]
                if snow and (y - top) < 3 + (hash2(x, top, seed) % 3) and abs(x - cx) < hw:
                    c = snow[0] if side < 0.2 else snow[1]
                elif snow and y == bottom - 2 and hash2(x, y, seed) % 3 == 0:
                    c = snow[1]
                img.set(x, y, c)
    img.set(cx - 1, 2, ol)
    img.set(cx, 2, ol)
    img.set(cx - 1, 3, snow[0] if snow else leaves[2])
    img.set(cx, 3, snow[0] if snow else leaves[1])
    return Obj(img, h - 16, [((w // 2 - 8) // 8, (h - 8) // 8, 2, 1)])


def tree_dead(wood, seed=0, w=32, h=48):
    img = RgbCanvas(w, h)
    cx = w // 2
    for y in range(h - 26, h - 2):
        for x in range(cx - 3, cx + 2):
            img.set(x, y, wood[1] if x < cx - 1 else wood[0])
    for x in range(cx - 5, cx + 4):
        img.set(x, h - 2, wood[0])
    branches = [((cx, h - 24), (cx - 11, h - 38)), ((cx, h - 22), (cx + 10, h - 36)), ((cx - 1, h - 26), (cx - 1, h - 44)),
                ((cx - 6, h - 31), (cx - 13, h - 33)), ((cx + 6, h - 30), (cx + 13, h - 41)),
                ((cx - 1, h - 38), (cx + 5, h - 45)), ((cx - 8, h - 35), (cx - 6, h - 43))]
    for (x0, y0), (x1, y1) in branches:
        img.line(x0, y0, x1, y1, wood[0])
        img.line(x0 + 1, y0, x1 + 1, y1, wood[1])
    img.outline(shade(wood[0], 0.45))
    return Obj(img, h - 16, [((w // 2 - 8) // 8, (h - 8) // 8, 2, 1)])


def tree_teldrassil(leaves, trunk, glow, w=32, h=56, seed=0):
    img = RgbCanvas(w, h)
    cx = w // 2
    for y in range(h - 26, h - 2):
        bend = int(math.sin(y * 0.3) * 1.5)
        for x in range(cx - 3 + bend, cx + 3 + bend):
            img.set(x, y, trunk[1] if x < cx + bend - 1 else trunk[0])
    for x in range(cx - 6, cx + 6):
        img.set(x, h - 2, trunk[1])
    blobs = [(cx, 16, 15, 12), (cx - 8, 22, 8, 7), (cx + 8, 22, 8, 7), (cx, 7, 10, 7)]
    ol = shade(leaves[0], 0.55)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny: blob_shade(leaves, (x - cx) / 15.0, (y - 16) / 12.0, x, y, seed))
    for i in range(8):
        gx = cx - 12 + hash2(i, 5, seed) % 24
        gy = 6 + hash2(i, 6, seed) % 18
        if img.get(gx, gy) not in (None, ol):
            img.set(gx, gy, glow)
    return Obj(img, h - 16, [((w // 2 - 8) // 8, (h - 8) // 8, 2, 1)])


def tree_savanna(leaves, trunk, w=32, h=40, seed=0):
    """Dry thorny tree of Durotar: crooked trunk and a flat crown."""
    img = RgbCanvas(w, h)
    cx = w // 2
    pts = [(cx, h - 2), (cx - 1, h - 10), (cx + 2, h - 18), (cx, h - 26)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for k in range(-1, 2):
            img.line(x0 + k, y0, x1 + k, y1, trunk[0] if k > -1 else trunk[1])
    img.line(cx + 1, h - 18, cx + 9, h - 24, trunk[0])
    img.line(cx - 1, h - 14, cx - 9, h - 22, trunk[0])
    ol = shade(leaves[0], 0.55)
    for bx, by, rx, ry in ((cx, h - 29, 14, 5), (cx - 8, h - 24, 6, 3), (cx + 9, h - 26, 6, 3)):
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in ((cx, h - 29, 14, 5), (cx - 8, h - 24, 6, 3), (cx + 9, h - 26, 6, 3)):
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny: blob_shade(leaves, nx, ny, x, y, seed))
    for i in range(6):
        sx = cx - 13 + hash2(i, 9, seed) % 26
        img.set(sx, h - 35 + hash2(i, 3) % 2, ol)
    return Obj(img, h - 16, [((w // 2 - 8) // 8, (h - 8) // 8, 2, 1)])


def rock(colors, w=16, h=16, seed=0):
    img = RgbCanvas(w, h)
    ol = shade(colors[0], 0.6)
    img.ellipse(w / 2, h / 2 + 2, w / 2 - 0.5, h / 2 - 2.5, ol)
    img.ellipse(w / 2, h / 2 + 2, w / 2 - 1.5, h / 2 - 3.5, lambda x, y, nx, ny: blob_shade(colors, nx, ny, x, y, seed))
    return Obj(img, 0, [(0, (h - 8) // 8, w // 8, 1)])


def boulder_big(colors, seed=0):
    img = RgbCanvas(32, 32)
    ol = shade(colors[0], 0.6)
    parts = [(16, 19, 14, 11), (9, 22, 8, 8), (24, 23, 7, 7)]
    for bx, by, rx, ry in parts:
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in parts:
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny, bx=bx, by=by: blob_shade(colors, (x - 16) / 14.0, (y - 19) / 11.0, x, y, seed))
    for i in range(5):
        x0 = 6 + hash2(i, 1, seed) % 20
        y0 = 14 + hash2(i, 2, seed) % 12
        img.line(x0, y0, x0 + 2, y0 + 2, ol)
    return Obj(img, 16, [(0, 2, 4, 2)])


def bush(leaves, berries=None, seed=0):
    img = RgbCanvas(16, 16)
    ol = shade(leaves[0], 0.6)
    for bx, by, rx, ry in ((8, 10, 7, 5), (5, 8, 4, 4), (11, 8, 4, 4)):
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in ((8, 10, 7, 5), (5, 8, 4, 4), (11, 8, 4, 4)):
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny: blob_shade(leaves, (x - 8) / 7.0, (y - 9) / 6.0, x, y, seed))
    if berries:
        for x, y in ((5, 8), (10, 11), (12, 7)):
            img.set(x, y, berries)
    return Obj(img, 0, [])


def building(w, wall_h, roof_h, wall, roof, trim, door, windows=True, timber=None, roof_style='shingle', seed=0):
    """Stormwind style house seen in 3/4 view: a roof (depth) above a front wall."""
    h = wall_h + roof_h
    img = RgbCanvas(w, h)
    ol = (30, 26, 30)
    # Roof.
    for y in range(roof_h):
        inset = max(0, 3 - y) if y < 3 else 0
        for x in range(inset, w - inset):
            k = 1 if (y // 4) % 2 == 0 else 2
            c = roof[k]
            if roof_style == 'shingle' and (x + (y // 4) * 3) % 6 == 0:
                c = roof[0]
            if y % 4 == 3:
                c = roof[0]
            if y < 2:
                c = roof[3] if len(roof) > 3 else roof[2]
            img.set(x, y, c)
        img.set(inset, y, ol)
        img.set(w - 1 - inset, y, ol)
    for x in range(w):
        img.set(x, roof_h - 1, ol)
        img.set(x, roof_h - 2, roof[0])
    # Wall.
    for y in range(roof_h, h):
        for x in range(1, w - 1):
            c = wall[1] if (y - roof_h) < 2 else wall[0]
            if timber and ((x - 1) % 16 in (0, 1) or y == roof_h + wall_h // 2):
                c = timber
            img.set(x, y, c)
        img.set(0, y, ol)
        img.set(w - 1, y, ol)
    for x in range(w):
        img.set(x, h - 1, wall[2])
    # Door.
    dw = 10
    dx = w // 2 - dw // 2
    for y in range(h - 16, h - 1):
        for x in range(dx, dx + dw):
            c = door[0] if (x - dx) % 3 else door[1]
            if y == h - 16 or x in (dx, dx + dw - 1):
                c = trim
            img.set(x, y, c)
    img.set(dx + dw - 3, h - 8, trim)
    # Windows.
    if windows:
        for wx in range(6, w - 10, 20):
            if abs(wx + 2 - w // 2) < 12:
                continue
            for y in range(roof_h + 5, roof_h + 12):
                for x in range(wx, wx + 6):
                    c = (90, 160, 210) if (y - roof_h - 5) < 3 else (60, 110, 170)
                    if x in (wx, wx + 5) or y in (roof_h + 5, roof_h + 11) or x == wx + 2:
                        c = trim
                    img.set(x, y, c)
    solid = [(0, 1, w // 8, (h - 8) // 8)]
    return Obj(img, roof_h, solid)


def tower(w, h, wall, roof, trim, seed=0):
    img = RgbCanvas(w, h)
    ol = (30, 26, 30)
    roof_h = w
    # Cone roof.
    for y in range(roof_h):
        hw = int((y + 1) / roof_h * (w / 2))
        for x in range(w // 2 - hw, w // 2 + hw):
            c = roof[1] if x < w // 2 else roof[2]
            if y % 4 == 3:
                c = roof[0]
            img.set(x, y, c)
        img.set(w // 2 - hw - 1, y, ol)
        img.set(w // 2 + hw, y, ol)
    for y in range(roof_h, h):
        for x in range(1, w - 1):
            c = wall[0]
            if (y // 4 + (x // 6)) % 5 == 0 and y % 4 == 0:
                c = wall[2]
            if x > w - 5:
                c = wall[2]
            img.set(x, y, c)
        img.set(0, y, ol)
        img.set(w - 1, y, ol)
    for y in range(roof_h + 6, roof_h + 16):
        for x in range(w // 2 - 2, w // 2 + 2):
            img.set(x, y, (40, 40, 60) if y > roof_h + 7 else trim)
    return img


def stone_wall_texture(img, x0, y0, w, h, stone):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            row = (y - y0) // 6
            bx = (x - x0 + (5 if row % 2 else 0)) % 10
            by = (y - y0) % 6
            c = stone[0]
            if by == 5 or bx == 9:
                c = stone[2]
            elif by == 0 or bx == 0:
                c = stone[1]
            img.set(x, y, c)


def abbey(stone, roof, trim):
    """Northshire Abbey: a large stone church with a bell tower and blue roofs."""
    w, h = 144, 112
    img = RgbCanvas(w, h)
    ol = (30, 26, 30)
    main_x, main_w, roof_h, wall_h = 24, 112, 52, 36
    top = h - wall_h - roof_h
    # Main roof.
    for y in range(roof_h):
        for x in range(main_x, main_x + main_w):
            c = roof[1] if (y // 5) % 2 else roof[2]
            if (x + (y // 5) * 4) % 8 == 0 or y % 5 == 4:
                c = roof[0]
            img.set(x, top + y, c)
        img.set(main_x, top + y, ol)
        img.set(main_x + main_w - 1, top + y, ol)
    for x in range(main_x, main_x + main_w):
        img.set(x, top, ol)
        img.set(x, top + 1, roof[3])
        img.set(x, top + roof_h - 1, ol)
    # Ridge crosses.
    for rx in (main_x + 30, main_x + main_w - 30):
        img.rect(rx - 1, top - 8, 3, 9, trim)
        img.rect(rx - 4, top - 5, 9, 3, trim)
    # Front wall.
    wy = top + roof_h
    stone_wall_texture(img, main_x, wy, main_w, wall_h, stone)
    for y in range(wy, h):
        img.set(main_x, y, ol)
        img.set(main_x + main_w - 1, y, ol)
    # Gable over door.
    gx = main_x + main_w // 2
    for y in range(20):
        hw = y + 2
        for x in range(gx - hw, gx + hw):
            img.set(x, wy - 20 + y + 8, stone[1] if abs(x - gx) < hw - 2 else ol)
    # Arched door.
    for y in range(wy + 8, h - 1):
        for x in range(gx - 9, gx + 9):
            d = abs(x - gx + 0.5)
            if y - (wy + 8) < 9 - d * 0.0 and (y - (wy + 8)) < (9 - math.sqrt(max(0, 81 - d * d))):
                continue
            c = (96, 60, 36) if (x - gx) % 4 else (70, 42, 26)
            if abs(x - gx + 0.5) > 8:
                c = trim
            img.set(x, y, c)
    # Stained glass windows.
    for wxp in (main_x + 14, main_x + 36, main_x + main_w - 42, main_x + main_w - 20):
        for y in range(wy + 6, wy + 22):
            for x in range(wxp, wxp + 7):
                c = [(220, 60, 60), (60, 120, 220), (240, 200, 60)][((x - wxp) + (y - wy) // 3) % 3]
                if x in (wxp, wxp + 6) or y == wy + 21 or (y == wy + 6):
                    c = ol
                img.set(x, y, c)
    for x in range(main_x, main_x + main_w):
        img.set(x, h - 1, stone[2])
    # Bell tower on the left.
    t = tower(28, h - 10, stone, roof, trim)
    img.blit(t, 0, 10)
    solid = [(0, (top + 8) // 8, w // 8, (h - top - 16) // 8)]
    return Obj(img, wy + 4, solid)


def anvilmar(rock_cols, stone, trim):
    """Dwarven hall carved into the mountain with a huge stone gate."""
    w, h = 128, 96
    img = RgbCanvas(w, h)
    ol = (30, 26, 30)
    # Mountain mass.
    img.ellipse(64, 70, 66, 64, lambda x, y, nx, ny: blob_shade(rock_cols, nx, ny, x, y, 4))
    for x in range(w):
        for y in range(h - 2, h):
            img.set(x, y, rock_cols[0])
    # Snow caps.
    for x in range(w):
        for y in range(h):
            c = img.get(x, y)
            if c is not None and img.get(x, y - 3) is None and y < 50:
                img.set(x, y, (236, 240, 250))
    # Gate frame.
    gx, gw, gy = 40, 48, 40
    stone_wall_texture(img, gx, gy, gw, h - gy, stone)
    for x in range(gx - 4, gx + gw + 4):
        for y in range(gy - 6, gy):
            img.set(x, y, trim if y == gy - 6 or y == gy - 1 else stone[1])
    # Door.
    for y in range(gy + 12, h - 1):
        for x in range(gx + 10, gx + gw - 10):
            c = (60, 40, 26) if (x - gx) % 5 else (40, 26, 16)
            if y in (gy + 20, gy + 34):
                c = (120, 120, 130)
            img.set(x, y, c)
    for x in range(gx + 10, gx + gw - 10):
        img.set(x, gy + 12, trim)
    # Dwarven face carving above the door.
    fx = gx + gw // 2
    img.rect(fx - 6, gy + 2, 12, 8, stone[1])
    img.rect(fx - 4, gy + 4, 2, 2, ol)
    img.rect(fx + 2, gy + 4, 2, 2, ol)
    img.rect(fx - 5, gy + 7, 10, 3, trim)
    # Braziers.
    for bx in (gx - 10, gx + gw + 6):
        img.rect(bx, h - 14, 6, 12, stone[2])
        img.rect(bx - 1, h - 16, 8, 3, trim)
        img.rect(bx + 1, h - 21, 4, 5, (255, 160, 40))
        img.rect(bx + 2, h - 23, 2, 3, (255, 230, 120))
    solid = [(0, 3, w // 8, (h - 32) // 8), (0, (h - 8) // 8, gx // 8 - 1, 1), ((gx + gw) // 8 + 1, (h - 8) // 8, (w - gx - gw) // 8 - 1, 1)]
    return Obj(img, h - 30, solid)


def cave_entrance(rock_cols, w=48, h=40, inner=(16, 12, 14)):
    img = RgbCanvas(w, h)
    img.ellipse(w / 2, h * 0.65, w / 2, h * 0.65, lambda x, y, nx, ny: blob_shade(rock_cols, nx, ny, x, y, 2))
    img.ellipse(w / 2, h - 4, w * 0.26, h * 0.42, inner)
    for x in range(w):
        img.set(x, h - 1, rock_cols[0] if img.get(x, h - 1) is not None else None)
    return Obj(img, h - 20, [(0, (h - 24) // 8, w // 8, 2)])


def mine_entrance(rock_cols, wood):
    o = cave_entrance(rock_cols, 48, 40)
    img = o.img
    img.rect(13, 14, 4, 26, wood[0])
    img.rect(31, 14, 4, 26, wood[0])
    img.rect(11, 12, 26, 4, wood[1])
    img.rect(17, 36, 14, 1, (120, 120, 130))
    img.rect(17, 38, 14, 1, (120, 120, 130))
    return o


def hut_round(wall, roof, trim, w=48, h=48, spikes=None, banner=None):
    """Round orc / troll hut with a conical hide roof."""
    img = RgbCanvas(w, h)
    ol = (30, 26, 30)
    cx = w // 2
    wall_top = h - 18
    for y in range(wall_top, h):
        for x in range(4, w - 4):
            c = wall[0] if (x // 4) % 2 else wall[1]
            img.set(x, y, c)
    # Conical roof.
    for y in range(4, wall_top + 3):
        t = (y - 4) / (wall_top - 1)
        hw = int(3 + t * (w / 2 - 2))
        for x in range(cx - hw, cx + hw):
            c = roof[1] if x < cx - hw // 3 else roof[2] if x > cx + hw // 3 else roof[0]
            if (y - x // 2) % 7 == 0:
                c = shade(roof[0], 0.8)
            img.set(x, y, c)
        img.set(cx - hw - 1, y, ol)
        img.set(cx + hw, y, ol)
    img.rect(cx - 2, 0, 1, 6, trim)
    img.rect(cx + 1, 1, 1, 5, trim)
    if spikes:
        for sx in range(6, w - 6, 8):
            sy = wall_top + 1
            img.line(sx, sy, sx - 3, sy - 6, spikes)
            img.line(sx + 1, sy, sx - 2, sy - 6, spikes)
    # Door.
    for y in range(h - 14, h):
        for x in range(cx - 5, cx + 5):
            img.set(x, y, (40, 26, 20) if abs(x - cx + 0.5) < 4 else trim)
    if banner:
        img.rect(cx + 8, h - 16, 6, 10, banner)
        img.rect(cx + 8, h - 18, 1, 16, (60, 40, 20))
    img.outline(ol)
    return Obj(img, wall_top + 2, [(1, (h - 24) // 8, w // 8 - 2, 3)])


def tent_tauren(hide, paint, poles):
    w, h = 48, 48
    img = RgbCanvas(w, h)
    cx = w // 2
    ol = (30, 26, 30)
    for y in range(6, h - 1):
        t = (y - 6) / (h - 8)
        hw = int(2 + t * 21)
        for x in range(cx - hw, cx + hw):
            c = hide[1] if x < cx - hw // 3 else (hide[2] if x > cx + hw // 3 else hide[0])
            band = (y - 6) % 12
            if band in (6, 7):
                c = paint[0] if ((x + y) // 3) % 2 else paint[1]
            img.set(x, y, c)
    # Poles.
    for dx in (-6, -2, 3, 7):
        img.line(cx, 8, cx + dx, 0, poles)
    # Door flap.
    for y in range(h - 16, h - 1):
        hw = (y - (h - 16)) // 2
        for x in range(cx - hw, cx + hw + 1):
            img.set(x, y, (50, 32, 20))
    img.outline(ol)
    return Obj(img, h - 22, [(1, 3, 4, 3)])


def totem(wood, paint, wings):
    w, h = 24, 56
    img = RgbCanvas(w, h)
    cx = w // 2
    for y in range(8, h - 1):
        for x in range(cx - 4, cx + 4):
            img.set(x, y, wood[0] if x < cx + 2 else wood[1])
        if y % 14 in (0, 1):
            for x in range(cx - 5, cx + 5):
                img.set(x, y, paint[0])
        if y % 14 == 6:
            img.set(cx - 2, y, paint[1])
            img.set(cx + 1, y, paint[1])
        if y % 14 == 10:
            img.rect(cx - 2, y, 4, 1, (30, 20, 20))
    # Wings on top.
    for i in range(10):
        img.line(cx, 10, cx - 4 - i, 2 + i // 2, wings[i % 2])
        img.line(cx, 10, cx + 3 + i, 2 + i // 2, wings[(i + 1) % 2])
    img.rect(cx - 3, 3, 6, 7, paint[0])
    img.rect(cx - 2, 5, 1, 1, (30, 20, 20))
    img.rect(cx + 1, 5, 1, 1, (30, 20, 20))
    img.outline((30, 26, 30))
    return Obj(img, h - 20, [(1, (h - 8) // 8, 1, 1)])


def tombstone(stone, kind=0):
    img = RgbCanvas(16, 16)
    ol = (30, 26, 30)
    if kind == 0:
        img.rect(4, 4, 8, 11, stone[0])
        img.rect(5, 3, 6, 1, stone[0])
        img.rect(4, 4, 2, 11, stone[1])
        img.rect(6, 7, 4, 1, stone[2])
        img.rect(6, 9, 4, 1, stone[2])
    elif kind == 1:
        img.rect(7, 2, 3, 13, stone[0])
        img.rect(4, 5, 9, 3, stone[0])
        img.rect(7, 2, 1, 13, stone[1])
    else:
        img.rect(3, 8, 10, 7, stone[0])
        img.rect(3, 8, 10, 2, stone[1])
        img.rect(5, 11, 6, 1, stone[2])
    img.rect(3, 15, 10, 1, (70, 60, 50))
    img.outline(ol)
    return Obj(img, 0, [(0, 1, 2, 1)] if kind != 2 else [])


def fence(wood, length=16, vertical=False):
    if not vertical:
        img = RgbCanvas(length, 16)
        for x in range(length):
            img.set(x, 7, wood[0])
            img.set(x, 8, wood[1])
            img.set(x, 11, wood[0])
            img.set(x, 12, wood[1])
        for px in range(1, length, 8):
            img.rect(px, 4, 3, 11, wood[0])
            img.rect(px + 2, 4, 1, 11, wood[1])
        img.outline((40, 30, 24))
        return Obj(img, 0, [(0, 1, length // 8, 1)])
    img = RgbCanvas(16, length)
    for y in range(length):
        img.set(6, y, wood[0])
        img.set(7, y, wood[1])
    for py in range(0, length, 8):
        img.rect(5, py, 4, 6, wood[0])
    img.outline((40, 30, 24))
    return Obj(img, 0, [(0, 0, 2, length // 8)])


def palisade(wood, length=16):
    img = RgbCanvas(length, 24)
    for px in range(0, length, 4):
        img.rect(px, 6, 3, 18, wood[0] if (px // 4) % 2 else wood[1])
        img.rect(px + 1, 3, 1, 3, wood[0])
    img.rect(0, 12, length, 2, (90, 60, 40))
    img.outline((30, 22, 18))
    return Obj(img, 8, [(0, 2, length // 8, 1)])


def campfire():
    img = RgbCanvas(16, 16)
    img.rect(2, 11, 12, 3, (110, 70, 40))
    img.rect(4, 10, 8, 1, (80, 50, 30))
    for (x, y, c) in ((7, 4, (255, 240, 140)), (6, 6, (255, 200, 60)), (9, 6, (255, 200, 60))):
        img.rect(x, y, 2, 4, c)
    img.rect(5, 8, 6, 3, (255, 120, 30))
    img.rect(7, 5, 2, 3, (255, 230, 120))
    for x in (1, 4, 8, 12, 14):
        img.set(x, 14, (120, 116, 110))
    img.outline((40, 30, 24))
    return Obj(img, 0, [(0, 1, 2, 1)])


def barrel(wood, metal):
    img = RgbCanvas(16, 16)
    img.ellipse(8, 9, 5, 6.5, lambda x, y, nx, ny: wood[1] if nx < -0.4 else wood[0])
    img.rect(3, 6, 10, 1, metal)
    img.rect(3, 12, 10, 1, metal)
    img.ellipse(8, 4, 4, 1.5, shade(wood[0], 0.7))
    img.outline((40, 30, 24))
    return Obj(img, 0, [(0, 1, 2, 1)])


def crate(wood):
    img = RgbCanvas(16, 16)
    img.rect(2, 3, 12, 12, wood[0])
    img.rect(2, 3, 12, 3, shade(wood[0], 1.15))
    img.line(3, 6, 12, 14, wood[1])
    img.line(12, 6, 3, 14, wood[1])
    img.outline((40, 30, 24))
    return Obj(img, 0, [(0, 1, 2, 1)])


def haystack(hay):
    img = RgbCanvas(24, 16)
    img.ellipse(12, 10, 11, 6, lambda x, y, nx, ny: blob_shade(hay, nx, ny, x, y, 6))
    for i in range(10):
        x = 3 + hash2(i, 4) % 18
        y = 6 + hash2(i, 5) % 7
        img.set(x, y, hay[0])
    img.outline(shade(hay[0], 0.5))
    return Obj(img, 0, [(0, 1, 3, 1)])


def well(stone, wood, water):
    img = RgbCanvas(24, 32)
    img.rect(3, 18, 18, 12, stone[0])
    stone_wall_texture(img, 3, 18, 18, 12, stone)
    img.ellipse(12, 18, 9, 3, stone[1])
    img.ellipse(12, 18, 7, 2, water)
    img.rect(4, 4, 2, 15, wood[0])
    img.rect(18, 4, 2, 15, wood[0])
    for y in range(0, 6):
        img.rect(2 + y // 2, y, 20 - y, 1, (150, 60, 50) if y % 2 else (120, 44, 38))
    img.outline((30, 26, 30))
    return Obj(img, 14, [(0, 2, 3, 2)])


def moonwell(stone, water, glow):
    img = RgbCanvas(40, 32)
    img.ellipse(20, 20, 19, 10, stone[0])
    img.ellipse(20, 19, 18, 8, stone[1])
    img.ellipse(20, 19, 14, 6, lambda x, y, nx, ny: glow if nx * nx + ny * ny < 0.25 else water)
    for px in (3, 36):
        img.rect(px - 1, 4, 3, 16, stone[1])
        img.rect(px - 2, 2, 5, 3, glow)
    img.outline((30, 26, 40))
    return Obj(img, 12, [(0, 1, 5, 3)])


def nightelf_house(wall, roof, trim):
    w, h = 64, 56
    img = RgbCanvas(w, h)
    ol = (30, 22, 40)
    # Curved leaf-like roof.
    for y in range(0, 34):
        t = y / 33.0
        hw = int(math.sin(t * math.pi * 0.62) * 32)
        for x in range(32 - hw, 32 + hw):
            c = roof[1] if x < 28 else roof[0] if x < 40 else roof[2]
            if (x - 32) % 8 == 0:
                c = roof[2]
            img.set(x, y, c)
    for x in range(2, 62):
        img.set(x, 33, trim)
    for y in range(34, h):
        for x in range(8, 56):
            c = wall[0] if (x // 6) % 2 else wall[1]
            img.set(x, y, c)
    # Round door.
    img.ellipse(32, h - 4, 7, 12, (40, 24, 60))
    img.rect(25, h - 1, 14, 1, trim)
    for wx in (14, 44):
        img.ellipse(wx + 3, 42, 3, 3, (170, 230, 255))
    img.outline(ol)
    return Obj(img, 34, [(1, 2, 6, 5)])


def aldrassil(trunk, leaves, glow, door):
    w, h = 112, 128
    img = RgbCanvas(w, h)
    cx = w // 2
    # Roots and trunk.
    for y in range(40, h):
        t = (y - 40) / (h - 40)
        hw = int(16 + t * t * 28)
        for x in range(cx - hw, cx + hw):
            rel = (x - cx) / hw
            c = trunk[1] if rel < -0.4 else trunk[2] if rel > 0.5 else trunk[0]
            if (x * 3 + y // 3) % 11 == 0:
                c = trunk[1]
            img.set(x, y, c)
    # Door into the trunk.
    for y in range(h - 26, h - 1):
        for x in range(cx - 9, cx + 9):
            if (y - (h - 26)) < 9 and abs(x - cx + 0.5) > math.sqrt(max(0, 81 - (9 - (y - (h - 26))) ** 2)):
                continue
            img.set(x, y, door)
    # Ramp ring.
    for x in range(cx - 30, cx + 30):
        img.set(x, h - 40 + int(abs(x - cx) * 0.2), (150, 120, 90))
    # Canopy.
    blobs = [(cx, 28, 54, 26), (cx - 34, 38, 20, 14), (cx + 34, 38, 20, 14), (cx, 12, 34, 12)]
    ol = shade(leaves[0], 0.55)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx + 1, ry + 1, ol)
    for bx, by, rx, ry in blobs:
        img.ellipse(bx, by, rx, ry, lambda x, y, nx, ny: blob_shade(leaves, (x - cx) / 54.0, (y - 28) / 26.0, x, y, 9))
    for i in range(30):
        gx = cx - 50 + hash2(i, 7) % 100
        gy = 4 + hash2(i, 8) % 44
        if img.get(gx, gy) not in (None, ol):
            img.set(gx, gy, glow)
    return Obj(img, 56, [(2, 7, 10, 7), (4, 14, 2, 2), (8, 14, 2, 2)])


def chapel_ruin(stone, roof, trim):
    o = building(80, 32, 32, stone, roof, trim, ((60, 40, 30), (40, 26, 20)), windows=True, roof_style='plain')
    img = o.img
    # Broken roof hole.
    img.ellipse(56, 12, 10, 7, None)
    for y in range(4, 20):
        for x in range(46, 67):
            if img.get(x, y) is None and (x + y) % 2 == 0:
                pass
    img.ellipse(56, 12, 9, 6, (40, 34, 40))
    # Steeple.
    t = tower(16, 40, stone, roof, trim)
    big = RgbCanvas(80, 96)
    big.blit(t, 10, 0)
    big.blit(img, 0, 32)
    return Obj(big, 32 + 32, [(0, 5, 10, 7)])


def crypt(stone, door):
    w, h = 48, 40
    img = RgbCanvas(w, h)
    stone_wall_texture(img, 2, 12, w - 4, h - 12, stone)
    for y in range(0, 12):
        hw = int((y + 1) / 12 * (w / 2 - 1))
        for x in range(w // 2 - hw, w // 2 + hw):
            img.set(x, y, stone[1] if y % 3 else stone[2])
    for y in range(h - 18, h):
        for x in range(w // 2 - 7, w // 2 + 7):
            img.set(x, y, door)
    img.outline((26, 22, 28))
    return Obj(img, 16, [(0, 2, 6, 3)])


def tent_scarlet(cloth, stripe, pole):
    w, h = 48, 40
    img = RgbCanvas(w, h)
    for y in range(4, h - 1):
        t = (y - 4) / (h - 5)
        hw = int(4 + t * 20)
        for x in range(24 - hw, 24 + hw):
            c = cloth[0] if x < 24 else cloth[1]
            if ((x - 24) // 4) % 2 == 0 and y < h - 10:
                c = stripe
            img.set(x, y, c)
    img.rect(23, 0, 2, 6, pole)
    img.rect(25, 0, 6, 4, stripe)
    for y in range(h - 14, h - 1):
        hw = (y - (h - 14)) // 2
        img.rect(24 - hw, y, hw * 2, 1, (60, 30, 30))
    img.outline((30, 26, 30))
    return Obj(img, h - 20, [(0, 2, 6, 2)])


def frostmane_hut(wall, snow, bones):
    o = hut_round(wall, [shade(wall[0], 0.9), shade(wall[0], 0.75), shade(wall[0], 1.05)], bones, 40, 40, spikes=bones)
    img = o.img
    for x in range(img.w):
        for y in range(img.h):
            if img.get(x, y) not in (None, (30, 26, 30)) and img.get(x, y - 2) is None and y < 26:
                img.set(x, y, snow)
    return o


def quilboar_hut(bramble, thorn):
    w, h = 48, 40
    img = RgbCanvas(w, h)
    img.ellipse(24, 26, 22, 16, lambda x, y, nx, ny: blob_shade(bramble, nx, ny, x, y, 11))
    for i in range(26):
        x = 4 + hash2(i, 1, 5) % 40
        y = 10 + hash2(i, 2, 5) % 24
        if img.get(x, y) is not None:
            img.line(x, y, x + (hash2(i, 3) % 5) - 2, y - 3, thorn)
    img.ellipse(24, 38, 6, 8, (30, 20, 14))
    img.outline((26, 20, 16))
    return Obj(img, h - 16, [(0, 2, 6, 3)])


def signpost(wood):
    img = RgbCanvas(16, 24)
    img.rect(7, 6, 2, 18, wood[1])
    img.rect(1, 6, 14, 5, wood[0])
    img.rect(2, 8, 10, 1, wood[1])
    img.outline((40, 30, 24))
    return Obj(img, 8, [(0, 2, 2, 1)])


def banner_pole(cloth, emblem, pole):
    img = RgbCanvas(16, 40)
    img.rect(7, 2, 2, 38, pole)
    img.rect(9, 4, 6, 16, cloth)
    img.rect(10, 9, 4, 4, emblem)
    img.rect(9, 20, 2, 2, cloth)
    img.rect(13, 20, 2, 2, cloth)
    img.outline((30, 26, 30))
    return Obj(img, 24, [(0, 4, 2, 1)])


def vine_rows(vine, grape, post, w=64):
    img = RgbCanvas(w, 16)
    for x in range(w):
        img.set(x, 6, post)
    for px in range(0, w, 16):
        img.rect(px + 1, 3, 2, 13, post)
    for x in range(w):
        for y in range(7, 13):
            if hashf(x, y, 21) < 0.65:
                img.set(x, y, vine[0] if hashf(x, y, 22) < 0.6 else vine[1])
    for i in range(w // 6):
        x = hash2(i, 1, 23) % w
        img.set(x, 11, grape)
        img.set(x, 12, grape)
    img.outline((30, 40, 26))
    return Obj(img, 0, [(0, 1, w // 8, 1)])


def ice_crystals(ice):
    img = RgbCanvas(16, 16)
    for (x, h) in ((3, 8), (7, 12), (11, 7)):
        img.rect(x, 15 - h, 3, h, ice[0])
        img.rect(x, 15 - h, 1, h, ice[1])
        img.set(x + 1, 14 - h, ice[1])
    img.outline((40, 60, 90))
    return Obj(img, 0, [(0, 1, 2, 1)])


def bones_pile(bone):
    img = RgbCanvas(16, 16)
    img.line(2, 12, 12, 9, bone)
    img.line(4, 9, 13, 13, bone)
    img.ellipse(10, 9, 3, 2.5, bone)
    img.set(9, 9, (30, 26, 30))
    img.set(11, 9, (30, 26, 30))
    img.outline((60, 52, 44))
    return Obj(img, 0, [])


def iron_fence(iron, length=16):
    img = RgbCanvas(length, 16)
    for x in range(length):
        img.set(x, 7, iron)
        img.set(x, 13, iron)
    for px in range(1, length, 4):
        img.rect(px, 3, 1, 12, iron)
        img.set(px, 2, (140, 140, 150))
    return Obj(img, 0, [(0, 1, length // 8, 1)])


def grass_tuft(colors):
    img = RgbCanvas(16, 16)
    for i, x in enumerate((4, 6, 8, 10, 12)):
        h = 4 + (i * 3) % 5
        img.line(x, 15, x + (i % 3) - 1, 15 - h, colors[i % len(colors)])
    return Obj(img, 0, [])
