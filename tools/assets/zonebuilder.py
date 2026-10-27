"""Builds a zone: terrain grid + objects -> ground / low / high 8bpp big maps sharing one tileset, plus collision."""

import math
from core import RgbCanvas, BgBuilder, Rng, hashf, hash2, emit_map, emit_bytes, shade

CELL = 8


class ZoneBuilder:
    def __init__(self, name, w_cells, h_cells, terrains, base, seed):
        self.name = name
        self.w = w_cells
        self.h = h_cells
        self.terrains = terrains
        self.grid = [[base] * w_cells for _ in range(h_cells)]
        self.objects = []                       # (obj, px, py)
        self.occupied = [[False] * w_cells for _ in range(h_cells)]
        self.solid = [[0] * w_cells for _ in range(h_cells)]
        self.rng = Rng(seed)
        self.seed = seed
        self.spawns = []
        self.npcs = []
        self.areas = []
        self.start = (0, 0)
        self.grave = (0, 0)
        self.edge_colors = {}

    # -----------------------------------------------------------------------------------------------------------------
    # Terrain painting (cells).
    # -----------------------------------------------------------------------------------------------------------------

    def set_t(self, x, y, t):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.grid[y][x] = t

    def get_t(self, x, y):
        x = max(0, min(self.w - 1, x))
        y = max(0, min(self.h - 1, y))
        return self.grid[y][x]

    def rect(self, t, x, y, w, h):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set_t(xx, yy, t)

    def ellipse(self, t, cx, cy, rx, ry, noise=0.0):
        for y in range(int(cy - ry - 2), int(cy + ry + 3)):
            for x in range(int(cx - rx - 2), int(cx + rx + 3)):
                nx = (x + 0.5 - cx) / rx
                ny = (y + 0.5 - cy) / ry
                d = nx * nx + ny * ny
                if d <= 1.0 + (hashf(x, y, self.seed + 5) - 0.5) * noise:
                    self.set_t(x, y, t)

    def path(self, t, points, width):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for i in range(steps + 1):
                k = i / steps
                cx = x0 + (x1 - x0) * k
                cy = y0 + (y1 - y0) * k
                r = width / 2.0
                for y in range(int(cy - r - 1), int(cy + r + 2)):
                    for x in range(int(cx - r - 1), int(cx + r + 2)):
                        if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                            self.set_t(x, y, t)

    def border(self, t, thickness, noise=3):
        for y in range(self.h):
            for x in range(self.w):
                d = min(x, y, self.w - 1 - x, self.h - 1 - y)
                n = int(hashf(x // 3, y // 3, self.seed + 9) * noise)
                if d < thickness + n:
                    self.grid[y][x] = t

    # -----------------------------------------------------------------------------------------------------------------
    # Objects.
    # -----------------------------------------------------------------------------------------------------------------

    def reserve(self, cx, cy, cw, ch):
        """Keeps an area clear of randomly scattered objects."""
        for y in range(cy, cy + ch):
            for x in range(cx, cx + cw):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.occupied[y][x] = True

    def free(self, cx, cy, cw, ch, allow=None):
        for y in range(cy, cy + ch):
            for x in range(cx, cx + cw):
                if x < 0 or y < 0 or x >= self.w or y >= self.h:
                    return False
                if self.occupied[y][x]:
                    return False
                t = self.terrains[self.grid[y][x]]
                if allow is not None:
                    if self.grid[y][x] not in allow:
                        return False
                elif t.solid:
                    return False
        return True

    def place(self, obj, cx, cy, force=True, allow=None, margin=0):
        """Places an object with its top-left at cell (cx, cy). Returns False if it doesn't fit."""
        cw = (obj.img.w + 7) // 8
        ch = (obj.img.h + 7) // 8
        # Only the bottom part (the footprint) needs free terrain; canopies can overlap.
        foot_h = max(1, (obj.img.h - obj.split + 7) // 8) if obj.split else ch
        fy = cy + ch - foot_h
        if not force and not self.free(cx - margin, fy - margin, cw + 2 * margin, foot_h + 2 * margin, allow):
            return False
        self.objects.append((obj, cx * 8, cy * 8))
        for y in range(fy, cy + ch):
            for x in range(cx, cx + cw):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.occupied[y][x] = True
        for sx, sy, sw, sh in obj.solid:
            for y in range(cy + sy, cy + sy + sh):
                for x in range(cx + sx, cx + sx + sw):
                    if 0 <= x < self.w and 0 <= y < self.h:
                        self.solid[y][x] = 1
        return True

    def scatter(self, make, x, y, w, h, count, tries=40, allow=None, margin=0):
        placed = 0
        for i in range(count * tries):
            if placed >= count:
                break
            obj = make(self.rng) if callable(make) else make
            cw = (obj.img.w + 7) // 8
            ch = (obj.img.h + 7) // 8
            px = x + self.rng.rand(max(1, w - cw + 1))
            py = y + self.rng.rand(max(1, h - ch + 1))
            if self.place(obj, px, py, force=False, allow=allow, margin=margin):
                placed += 1
        return placed

    def forest_edge(self, make, thickness, spacing=(4, 3), skip=None):
        """Fills the zone border with trees on a regular grid (keeps tile count low)."""
        sx, sy = spacing
        for gy in range(-4, self.h, sy):
            for gx in range(-2, self.w, sx):
                ox = (sx // 2) if ((gy // sy) % 2) else 0
                cx = gx + ox
                cy = gy
                obj = make(self.rng)
                cw = (obj.img.w + 7) // 8
                ch = (obj.img.h + 7) // 8
                bx, by = cx + cw // 2, cy + ch - 1
                d = min(bx, by, self.w - 1 - bx, self.h - 1 - by)
                n = int(hashf(bx // 4, by // 4, self.seed + 13) * 4)
                if d < thickness + n and not (skip and skip(bx, by)):
                    self.place(obj, cx, cy)
                    # Everything inside the forest wall is blocked.
                    for yy in range(by - 1, by + 1):
                        for xx in range(cx, cx + cw):
                            if 0 <= xx < self.w and 0 <= yy < self.h:
                                self.solid[yy][xx] = 1

    def block_border(self, thickness):
        for y in range(self.h):
            for x in range(self.w):
                if min(x, y, self.w - 1 - x, self.h - 1 - y) < thickness:
                    self.solid[y][x] = 1

    # -----------------------------------------------------------------------------------------------------------------
    # Gameplay markers (pixel coordinates).
    # -----------------------------------------------------------------------------------------------------------------

    def spawn(self, enemy, cx, cy, w, h, count):
        n = 0
        for i in range(count * 50):
            if n >= count:
                break
            x = cx + self.rng.rand(w)
            y = cy + self.rng.rand(h)
            ok = True
            for yy in range(y - 1, y + 1):
                for xx in range(x - 1, x + 2):
                    if not (0 <= xx < self.w and 0 <= yy < self.h) or self.solid[yy][xx] or \
                            self.terrains[self.grid[yy][xx]].solid:
                        ok = False
            for e, sx, sy in self.spawns:
                if abs(sx - x * 8) < 36 and abs(sy - y * 8) < 36:
                    ok = False
            if ok:
                self.spawns.append((enemy, x * 8 + 4, y * 8 + 6))
                n += 1

    def npc(self, npc_id, cx, cy, direction=0):
        self.npcs.append((npc_id, cx * 8 + 4, cy * 8 + 6, direction))
        self.solid[cy][cx] = 1

    def area(self, name, cx, cy, cw, ch):
        self.areas.append((name, cx * 8, cy * 8, cw * 8, ch * 8))

    # -----------------------------------------------------------------------------------------------------------------
    # Rendering.
    # -----------------------------------------------------------------------------------------------------------------

    def variant(self, t, mx, my):
        ter = self.terrains[t]
        if ter.variants == 1:
            return 0
        r = hashf(mx, my, self.seed + 77)
        acc = 0.0
        for i, w in enumerate(ter.weights):
            acc += w
            if r < acc:
                return i
        return ter.variants - 1

    def render_ground(self):
        W, H = self.w * 8, self.h * 8
        canvas = RgbCanvas(W, H)
        cache = {}
        dirs = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
        for cy in range(self.h):
            for cx in range(self.w):
                t = self.grid[cy][cx]
                ter = self.terrains[t]
                v = self.variant(t, cx // 2, cy // 2)
                neigh = []
                for dx, dy in dirs:
                    u = self.get_t(cx + dx, cy + dy)
                    neigh.append(u if self.terrains[u].prio > ter.prio else None)
                # Lower priority neighbours only matter for edge shading.
                low = tuple(self.get_t(cx + dx, cy + dy) != t and self.terrains[self.get_t(cx + dx, cy + dy)].prio < ter.prio
                            for dx, dy in dirs)
                key = (t, v, cx & 1, cy & 1, tuple(neigh), low)
                block = cache.get(key)
                if block is None:
                    block = self._cell_block(t, v, cx, cy, neigh, low, dirs)
                    cache[key] = block
                for ly in range(8):
                    row = canvas.px[cy * 8 + ly]
                    row[cx * 8:cx * 8 + 8] = block[ly]
        return canvas

    def _cell_block(self, t, v, cx, cy, neigh, low, dirs):
        ter = self.terrains[t]
        block = []
        for ly in range(8):
            row = []
            for lx in range(8):
                gx = cx * 8 + lx
                gy = cy * 8 + ly
                best = None
                best_prio = ter.prio
                edge = False
                for k, (dx, dy) in enumerate(dirs):
                    u = neigh[k]
                    if u is None:
                        continue
                    ddx = lx if dx < 0 else (7 - lx if dx > 0 else 0)
                    ddy = ly if dy < 0 else (7 - ly if dy > 0 else 0)
                    if dx != 0 and dy != 0:
                        d = math.hypot(ddx + 0.5, ddy + 0.5)
                    else:
                        d = (ddx if dx != 0 else ddy) + 0.5
                    thr = 2.2 + hashf(lx + (cx & 1) * 8, ly + (cy & 1) * 8, k + 101) * 2.2
                    up = self.terrains[u]
                    if d < thr and up.prio > best_prio:
                        best = u
                        best_prio = up.prio
                    elif d < thr + 1.0:
                        edge = True
                if best is not None:
                    row.append(self.terrains[best].tex(gx, gy, 0))
                else:
                    c = ter.tex(gx, gy, v)
                    if edge and t in self.edge_colors:
                        c = self.edge_colors[t]
                    row.append(c)
            block.append(row)
        return block

    def render(self):
        W, H = self.w * 8, self.h * 8
        ground = self.render_ground()
        low = RgbCanvas(W, H)
        high = RgbCanvas(W, H)
        # Painter's order: objects with a lower base are drawn later (in front).
        for obj, px, py in sorted(self.objects, key=lambda o: o[2] + o[0].img.h):
            img = obj.img
            for y in range(img.h):
                target = low if y >= obj.split else high
                row = img.px[y]
                ty = py + y
                if ty < 0 or ty >= H:
                    continue
                trow = target.px[ty]
                for x in range(img.w):
                    c = row[x]
                    tx = px + x
                    if c is not None and 0 <= tx < W:
                        trow[tx] = c
        return ground, low, high

    def collision(self):
        out = []
        for y in range(self.h):
            for x in range(self.w):
                s = 1 if (self.solid[y][x] or self.terrains[self.grid[y][x]].solid) else 0
                out.append(s)
        return out

    def emit(self, prefix):
        ground, low, high = self.render()
        bb = BgBuilder()
        g = bb.map_cells(ground)
        l = bb.map_cells(low)
        h = bb.map_cells(high)
        out = bb.emit_tiles_palette(prefix)
        out += emit_map(prefix + '_ground', g, self.w, self.h)
        out += emit_map(prefix + '_low', l, self.w, self.h)
        out += emit_map(prefix + '_high', h, self.w, self.h)
        for layer in ('ground', 'low', 'high'):
            out += 'inline constexpr bn::regular_bg_item %s_%s_item(%s_tiles, %s_palette, %s_%s_map);\n' % (
                prefix, layer, prefix, prefix, prefix, layer)
        out += '\n' + emit_bytes(prefix + '_collision', self.collision())
        stats = (len(bb.tiles), len(bb.colors))
        return out, stats, (ground, low, high)
