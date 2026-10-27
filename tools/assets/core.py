"""Core helpers: pixel canvases, palettes, tile conversion and C++ emission.

Everything here is plain Python (no third party modules) so the ROM can be built anywhere Butano builds.
"""

import math
import zlib
import struct


# ---------------------------------------------------------------------------------------------------------------------
# Deterministic pseudo random numbers (so the generated ROM is identical on every build).
# ---------------------------------------------------------------------------------------------------------------------

def hash2(x, y, seed=0):
    h = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0xFFFFFFFF


def hashf(x, y, seed=0):
    return hash2(x, y, seed) / 4294967296.0


class Rng:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF or 1

    def next(self):
        x = self.state
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        self.state = x & 0xFFFFFFFF
        return self.state

    def rand(self, n):
        return self.next() % n

    def chance(self, p):
        return (self.next() % 10000) < p * 10000

    def range(self, a, b):
        return a + self.rand(b - a + 1)


# ---------------------------------------------------------------------------------------------------------------------
# Canvas: a 2D array of palette indices (index 0 is transparent).
# ---------------------------------------------------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, fill=0):
        self.w = w
        self.h = h
        self.px = [[fill] * w for _ in range(h)]

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return 0

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c, fn=None):
        """Filled ellipse. fn(x, y, nx, ny) may return a color per pixel (nx, ny normalized offsets)."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                nx = (x + 0.5 - cx) / max(rx, 0.01)
                ny = (y + 0.5 - cy) / max(ry, 0.01)
                if nx * nx + ny * ny <= 1.0:
                    self.set(x, y, fn(x, y, nx, ny) if fn else c)

    def blit(self, src, x, y, flip=False, transparent=0):
        for sy in range(src.h):
            for sx in range(src.w):
                c = src.px[sy][src.w - 1 - sx if flip else sx]
                if c != transparent:
                    self.set(x + sx, y + sy, c)

    def ascii(self, x, y, rows, mapping, flip=False):
        """Draws ASCII art. mapping maps characters to palette indices; '.' and ' ' are skipped."""
        for j, row in enumerate(rows):
            w = len(row)
            for i, ch in enumerate(row):
                if ch in '. ':
                    continue
                xx = x + (w - 1 - i if flip else i)
                self.set(xx, y + j, mapping[ch])

    def outline(self, color, diagonal=False, skip=()):
        """Adds an outline of the given color around every non transparent pixel."""
        out = self.copy()
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if diagonal:
            dirs += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] == 0:
                    for dx, dy in dirs:
                        n = self.get(x + dx, y + dy)
                        if n != 0 and n != color and n not in skip:
                            out.px[y][x] = color
                            break
        self.px = out.px

    def replace(self, a, b):
        for row in self.px:
            for i, c in enumerate(row):
                if c == a:
                    row[i] = b

    def flipped(self):
        c = Canvas(self.w, self.h)
        c.px = [row[::-1] for row in self.px]
        return c

    def crop(self, x, y, w, h):
        c = Canvas(w, h)
        for j in range(h):
            for i in range(w):
                c.px[j][i] = self.get(x + i, y + j)
        return c

    def shifted(self, dx, dy):
        c = Canvas(self.w, self.h)
        c.blit(self, dx, dy)
        return c


# ---------------------------------------------------------------------------------------------------------------------
# RGB canvas (used for 8bpp backgrounds that are quantized to a 256 colors palette later).
# ---------------------------------------------------------------------------------------------------------------------

def rgb5(c):
    """Converts an 8 bits per channel color to the GBA 5 bits per channel grid (kept as 8 bits values)."""
    r, g, b = c
    return (int(r) >> 3, int(g) >> 3, int(b) >> 3)


def mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def shade(c, f):
    return (max(0, min(255, c[0] * f)), max(0, min(255, c[1] * f)), max(0, min(255, c[2] * f)))


class RgbCanvas:
    """Pixels are None (transparent) or (r, g, b) tuples."""

    def __init__(self, w, h, fill=None):
        self.w = w
        self.h = h
        self.px = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.px[y][x] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c(xx, yy) if callable(c) else c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                nx = (x + 0.5 - cx) / max(rx, 0.01)
                ny = (y + 0.5 - cy) / max(ry, 0.01)
                if nx * nx + ny * ny <= 1.0:
                    self.set(x, y, c(x, y, nx, ny) if callable(c) else c)

    def line(self, x0, y0, x1, y1, c):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            self.set(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), c)

    def blit(self, src, x, y):
        for sy in range(src.h):
            row = src.px[sy]
            for sx in range(src.w):
                c = row[sx]
                if c is not None:
                    self.set(x + sx, y + sy, c)

    def blit_indexed(self, src, x, y, palette, flip=False):
        for sy in range(src.h):
            for sx in range(src.w):
                c = src.px[sy][src.w - 1 - sx if flip else sx]
                if c != 0:
                    self.set(x + sx, y + sy, palette[c])

    def outline(self, color):
        out = [row[:] for row in self.px]
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is None:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = self.get(x + dx, y + dy)
                        if n is not None and n != color:
                            out[y][x] = color
                            break
        self.px = out


def write_png(path, canvas, palette=None, scale=1):
    """Debug helper: writes an RgbCanvas (or an indexed Canvas + palette) as PNG."""
    w, h = canvas.w * scale, canvas.h * scale
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            c = canvas.px[y // scale][x // scale]
            if palette is not None:
                c = None if c == 0 else palette[c]
            if c is None:
                raw += bytes((255, 0, 255))
            else:
                raw += bytes((int(c[0]) & 255, int(c[1]) & 255, int(c[2]) & 255))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)

    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(data)


# ---------------------------------------------------------------------------------------------------------------------
# Tiles conversion.
# ---------------------------------------------------------------------------------------------------------------------

def tile_words_4bpp(canvas, tx, ty):
    """Returns the 8 32 bits words of the 4bpp 8x8 tile at (tx, ty) (in pixels)."""
    words = []
    for y in range(8):
        w = 0
        for x in range(8):
            w |= (canvas.get(tx + x, ty + y) & 0xF) << (4 * x)
        words.append(w)
    return words


def tile_bytes_8bpp(idx_rows):
    """idx_rows: 8 rows of 8 palette indices. Returns 16 32 bits words (two bn::tile)."""
    words = []
    for row in idx_rows:
        words.append(row[0] | (row[1] << 8) | (row[2] << 16) | (row[3] << 24))
        words.append(row[4] | (row[5] << 8) | (row[6] << 16) | (row[7] << 24))
    return words


def sprite_frames_tiles(frames):
    """Converts a list of indexed Canvas (all same size, multiple of 8) to a flat 4bpp words list (1D mapping)."""
    words = []
    for f in frames:
        for ty in range(0, f.h, 8):
            for tx in range(0, f.w, 8):
                words += tile_words_4bpp(f, tx, ty)
    return words


def bn_color(c):
    r, g, b = rgb5(c)
    return 'bn::color(%d, %d, %d)' % (r, g, b)


def emit_words(words, per_line=8):
    lines = []
    for i in range(0, len(words), per_line):
        lines.append('    ' + ', '.join('0x%08X' % w for w in words[i:i + per_line]) + ',')
    return '\n'.join(lines)


def emit_tiles_array(name, words):
    count = len(words) // 8
    return 'alignas(4) inline constexpr bn::tile %s[%d] = {\n%s\n};\n' % (
        name, count, ',\n'.join('    {{%s}}' % ', '.join('0x%08X' % w for w in words[i:i + 8])
                               for i in range(0, len(words), 8)))


def emit_colors_array(name, colors):
    return 'inline constexpr bn::color %s[%d] = {\n%s\n};\n' % (
        name, len(colors), ',\n'.join('    ' + bn_color(c) for c in colors))


SHAPE_SIZES = {
    (8, 8): 'bn::sprite_shape_size(bn::sprite_shape::SQUARE, bn::sprite_size::SMALL)',
    (16, 16): 'bn::sprite_shape_size(bn::sprite_shape::SQUARE, bn::sprite_size::NORMAL)',
    (32, 32): 'bn::sprite_shape_size(bn::sprite_shape::SQUARE, bn::sprite_size::BIG)',
    (64, 64): 'bn::sprite_shape_size(bn::sprite_shape::SQUARE, bn::sprite_size::HUGE)',
    (16, 8): 'bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::SMALL)',
    (32, 8): 'bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::NORMAL)',
    (32, 16): 'bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::BIG)',
    (64, 32): 'bn::sprite_shape_size(bn::sprite_shape::WIDE, bn::sprite_size::HUGE)',
    (8, 16): 'bn::sprite_shape_size(bn::sprite_shape::TALL, bn::sprite_size::SMALL)',
    (8, 32): 'bn::sprite_shape_size(bn::sprite_shape::TALL, bn::sprite_size::NORMAL)',
    (16, 32): 'bn::sprite_shape_size(bn::sprite_shape::TALL, bn::sprite_size::BIG)',
    (32, 64): 'bn::sprite_shape_size(bn::sprite_shape::TALL, bn::sprite_size::HUGE)',
}


def emit_sprite_item(name, frames, palette):
    """frames: list of indexed Canvas; palette: 16 RGB tuples (index 0 ignored)."""
    w, h = frames[0].w, frames[0].h
    words = sprite_frames_tiles(frames)
    pal = list(palette) + [(0, 0, 0)] * (16 - len(palette))
    out = emit_tiles_array(name + '_tiles', words)
    out += emit_colors_array(name + '_colors', pal[:16])
    out += 'inline constexpr bn::sprite_item %s(%s, bn::span<const bn::tile>(%s_tiles), ' \
           'bn::span<const bn::color>(%s_colors), bn::bpp_mode::BPP_4, %d);\n\n' % (
               name, SHAPE_SIZES[(w, h)], name, name, len(frames))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# 8bpp background builder: chops RGB canvases into deduplicated 8x8 tiles (with flips) sharing one palette.
# ---------------------------------------------------------------------------------------------------------------------

class BgBuilder:
    def __init__(self, max_colors=255):
        self.colors = [(0, 0, 0)]       # index 0: transparent / backdrop
        self.color_index = {}
        self.tiles = []                 # list of tuple(64 indices)
        self.tile_index = {}
        self.max_colors = max_colors
        # Tile 0 is always fully transparent.
        self._add_tile(tuple([0] * 64))

    def color(self, c):
        key = rgb5(c)
        i = self.color_index.get(key)
        if i is None:
            if len(self.colors) > self.max_colors:
                # Palette full: use the nearest existing color.
                best, bi = 1e9, 1
                for j, cc in enumerate(self.colors[1:], 1):
                    k = rgb5(cc)
                    d = (k[0] - key[0]) ** 2 + (k[1] - key[1]) ** 2 + (k[2] - key[2]) ** 2
                    if d < best:
                        best, bi = d, j
                self.color_index[key] = bi
                return bi
            i = len(self.colors)
            self.colors.append((key[0] << 3, key[1] << 3, key[2] << 3))
            self.color_index[key] = i
        return i

    def _add_tile(self, t):
        i = len(self.tiles)
        self.tiles.append(t)
        self.tile_index[t] = (i, False, False)
        hf = tuple(t[y * 8 + (7 - x)] for y in range(8) for x in range(8))
        vf = tuple(t[(7 - y) * 8 + x] for y in range(8) for x in range(8))
        hvf = tuple(t[(7 - y) * 8 + (7 - x)] for y in range(8) for x in range(8))
        self.tile_index.setdefault(hf, (i, True, False))
        self.tile_index.setdefault(vf, (i, False, True))
        self.tile_index.setdefault(hvf, (i, True, True))
        return i

    def cell(self, canvas, x, y):
        """Returns the map cell value for the 8x8 block of an RgbCanvas at pixel (x, y)."""
        t = []
        for yy in range(8):
            row = canvas.px[y + yy]
            for xx in range(8):
                c = row[x + xx]
                t.append(0 if c is None else self.color(c))
        t = tuple(t)
        found = self.tile_index.get(t)
        if found is None:
            found = (self._add_tile(t), False, False)
        i, hf, vf = found
        return i | (1024 if hf else 0) | (2048 if vf else 0)

    def map_cells(self, canvas):
        cells = []
        for y in range(0, canvas.h, 8):
            for x in range(0, canvas.w, 8):
                cells.append(self.cell(canvas, x, y))
        return cells

    def emit_tiles_palette(self, prefix, bpp=8):
        words = []
        for t in self.tiles:
            if bpp == 8:
                words += tile_bytes_8bpp([t[r * 8:r * 8 + 8] for r in range(8)])
            else:
                for r in range(8):
                    w = 0
                    for x in range(8):
                        w |= (t[r * 8 + x] & 0xF) << (4 * x)
                    words.append(w)
        count = 16 if bpp == 4 else (len(self.colors) + 15) // 16 * 16
        assert len(self.colors) <= count
        colors = self.colors + [(0, 0, 0)] * (count - len(self.colors))
        out = emit_tiles_array(prefix + '_tiles_data', words)
        out += emit_colors_array(prefix + '_colors_data', colors)
        out += 'inline constexpr bn::regular_bg_tiles_item %s_tiles(bn::span<const bn::tile>(%s_tiles_data), ' \
               'bn::bpp_mode::BPP_%d);\n' % (prefix, prefix, bpp)
        out += 'inline constexpr bn::bg_palette_item %s_palette(bn::span<const bn::color>(%s_colors_data), ' \
               'bn::bpp_mode::BPP_%d);\n\n' % (prefix, prefix, bpp)
        return out


def emit_map(name, cells, w, h):
    lines = []
    for i in range(0, len(cells), 32):
        lines.append('    ' + ', '.join(str(c) for c in cells[i:i + 32]) + ',')
    out = 'alignas(4) inline constexpr bn::regular_bg_map_cell %s_cells[%d] = {\n%s\n};\n' % (name, len(cells), '\n'.join(lines))
    out += 'inline constexpr bn::regular_bg_map_item %s_map(%s_cells[0], bn::size(%d, %d));\n\n' % (name, name, w, h)
    return out


def emit_bytes(name, data, ctype='uint8_t'):
    lines = []
    for i in range(0, len(data), 64):
        lines.append('    ' + ','.join(str(d) for d in data[i:i + 64]) + ',')
    return 'inline constexpr %s %s[%d] = {\n%s\n};\n\n' % (ctype, name, len(data), '\n'.join(lines))


HEADER_INCLUDES = '''#include "bn_tile.h"
#include "bn_color.h"
#include "bn_span.h"
#include "bn_size.h"
#include "bn_sprite_item.h"
#include "bn_sprite_shape_size.h"
#include "bn_regular_bg_item.h"
#include "bn_regular_bg_tiles_item.h"
#include "bn_regular_bg_map_item.h"
#include "bn_bg_palette_item.h"
'''


def header(guard, body, extra_includes=''):
    return '// Generated by tools/gen_assets.py - do not edit.\n#ifndef %s\n#define %s\n\n%s%s\nnamespace gen\n{\n\n%s}\n\n#endif\n' % (
        guard, guard, HEADER_INCLUDES, extra_includes, body)
