#!/usr/bin/env python3
"""Generates every graphic and data table of Pocket of Warcraft as C++ headers.

Usage: gen_assets.py <output folder>

All the art is drawn by code in tools/assets/ (no image files). Outputs are only rewritten when the generator
sources change, so incremental builds stay fast.
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'assets'))

import core  # noqa: E402
from core import header, emit_sprite_item, emit_map, BgBuilder  # noqa: E402


def sources_hash():
    h = hashlib.sha1()
    for folder in (HERE, os.path.join(HERE, 'assets')):
        for name in sorted(os.listdir(folder)):
            if name.endswith('.py'):
                with open(os.path.join(folder, name), 'rb') as f:
                    h.update(name.encode())
                    h.update(f.read())
    return h.hexdigest()


def write(out_dir, name, text):
    path = os.path.join(out_dir, name)
    if os.path.exists(path):
        with open(path, 'r') as f:
            if f.read() == text:
                return
    with open(path, 'w') as f:
        f.write(text)


def gen_font(out_dir):
    import font
    body = font.generate()
    write(out_dir, 'pw_gen_font.h', header('PW_GEN_FONT_H', body, '#include "bn_sprite_font.h"\n'
                                                                 '#include "bn_sprite_palette_item.h"\n'
                                                                 '#include "bn_utf8_characters_map_ref.h"\n'))


def gen_sprites(out_dir):
    import gamedata
    import ui
    body = gamedata.generate_sprites()
    body += emit_sprite_item('weapons', [ui.weapon(w) for w in ui.WEAPONS], ui.WEAPON_PALETTE)
    body += 'enum weapon_frame : uint8_t { %s };\n\n' % ', '.join('WEAPON_%s' % w.upper() for w in ui.WEAPONS)
    body += emit_sprite_item('fx', [ui.fx(f) for f in ui.FX], ui.FX_PALETTE)
    body += 'enum fx_frame : uint8_t { %s };\n\n' % ', '.join('FX_%s' % f.upper() for f in ui.FX)
    body += emit_sprite_item('big_fx', ui.big_fx(), ui.FX_PALETTE)
    body += emit_sprite_item('bars', ui.bar_frames(), ui.UI_PALETTE)
    body += 'enum bar_kind : uint8_t { %s };\n\n' % ', '.join('BAR_%s' % b.upper() for b in ui.BARS)
    body += emit_sprite_item('quest_marks', ui.quest_marks(), ui.UI_PALETTE)
    body += emit_sprite_item('target_ring', ui.target_ring(), ui.UI_PALETTE)
    body += emit_sprite_item('cursor', [ui.cursor()], ui.UI_PALETTE)
    icons, pal = ui.to_indexed([ui.class_icon(c) for c in ui.CLASS_ORDER])
    body += emit_sprite_item('class_icons', icons, pal)
    # Dimmed copy for classes the selected race can't be.
    dim = [(int(c[0] * 0.3), int(c[1] * 0.3), int(c[2] * 0.3)) for c in pal]
    body += core.emit_colors_array('class_icons_dim_colors', dim[:16] + [(0, 0, 0)] * (16 - len(dim)))
    body += 'inline constexpr bn::sprite_palette_item class_icons_dim_palette(' \
            'bn::span<const bn::color>(class_icons_dim_colors), bn::bpp_mode::BPP_4);\n\n'
    races = ['human', 'dwarf', 'nightelf', 'gnome', 'orc', 'undead', 'tauren', 'troll']
    # One shared palette per faction.
    for faction, members in (('alliance', races[:4]), ('horde', races[4:])):
        icons, pal = ui.to_indexed([ui.race_icon(r) for r in members])
        body += emit_sprite_item('race_icons_%s' % faction, icons, pal)
    crests, pal = ui.to_indexed([ui.crest(False), ui.crest(True)])
    body += emit_sprite_item('crests', crests, pal)
    write(out_dir, 'pw_gen_sprites.h', header('PW_GEN_SPRITES_H', body, '#include "bn_sprite_palette_item.h"\n'))


def gen_data(out_dir):
    import gamedata
    body = gamedata.generate_tables()
    write(out_dir, 'pw_gen_data.h', header('PW_GEN_DATA_H', body, '#include "pw_defs.h"\n#include "pw_gen_sprites.h"\n'))


def gen_bgs(out_dir):
    import ui
    body = ''
    for name, img, bpp in (('title', ui.title_bg(), 8), ('charselect', ui.charselect_bg(), 8)):
        bb = BgBuilder()
        cells = bb.map_cells(img)
        body += bb.emit_tiles_palette('bg_' + name, bpp)
        body += emit_map('bg_' + name, cells, img.w // 8, img.h // 8)
        body += 'inline constexpr bn::regular_bg_item bg_%s_item(bg_%s_tiles, bg_%s_palette, bg_%s_map);\n\n' % (
            name, name, name, name)
    bb = BgBuilder(max_colors=15)
    img = ui.panel_bg()
    cells = bb.map_cells(img)
    body += bb.emit_tiles_palette('bg_panel', 4)
    body += emit_map('bg_panel', cells, img.w // 8, img.h // 8)
    body += 'inline constexpr bn::regular_bg_item bg_panel_item(bg_panel_tiles, bg_panel_palette, bg_panel_map);\n\n'
    write(out_dir, 'pw_gen_bgs.h', header('PW_GEN_BGS_H', body))


def gen_zones(out_dir, verbose):
    import zones
    import gamedata
    names = []
    for name, fn in zones.ZONES:
        z = fn()
        prefix = 'zone_' + name
        body, stats, _ = z.emit(prefix)
        if verbose:
            print('  %s: %d tiles, %d colors' % (name, stats[0], stats[1]))
        body += 'inline constexpr pw::spawn_def %s_spawns[] = {\n' % prefix
        for e, x, y in z.spawns:
            body += '    pw::spawn_def{%d, %d, %d},\n' % (gamedata.enemy_index(e), x, y)
        body += '};\n\n'
        body += 'inline constexpr pw::npc_place %s_npcs[] = {\n' % prefix
        for n, x, y, d in z.npcs:
            body += '    pw::npc_place{%d, %d, %d, %d},\n' % (gamedata.npc_index(n), x, y, d)
        body += '};\n\n'
        body += 'inline constexpr pw::area_def %s_areas[] = {\n' % prefix
        for a, x, y, w, h in z.areas:
            body += '    pw::area_def{%s, %d, %d, %d, %d},\n' % (gamedata.cstr(a), x, y, w, h)
        body += '};\n\n'
        body += 'inline constexpr pw::zone_def %s_def{%s, &%s_ground_item, &%s_low_item, &%s_high_item, ' \
                '%s_collision, %d, %d, bn::span<const pw::spawn_def>(%s_spawns), ' \
                'bn::span<const pw::npc_place>(%s_npcs), bn::span<const pw::area_def>(%s_areas), %d, %d, %d, %d};\n' % (
                    prefix, gamedata.cstr(z.name), prefix, prefix, prefix, prefix, z.w, z.h, prefix, prefix, prefix,
                    z.start[0], z.start[1], z.grave[0], z.grave[1])
        write(out_dir, 'pw_gen_%s.h' % prefix, header('PW_GEN_%s_H' % prefix.upper(), body, '#include "pw_defs.h"\n'))
        names.append(prefix)
    body = ''.join('#include "pw_gen_%s.h"\n' % n for n in names)
    body2 = 'inline constexpr const pw::zone_def* zones[] = {%s};\n' % ', '.join('&%s_def' % n for n in names)
    write(out_dir, 'pw_gen_zones.h', '// Generated by tools/gen_assets.py - do not edit.\n#ifndef PW_GEN_ZONES_H\n'
                                     '#define PW_GEN_ZONES_H\n\n%s\nnamespace gen\n{\n\n%s\n}\n\n#endif\n' % (body, body2))


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else 'build_gen'
    os.makedirs(out_dir, exist_ok=True)
    stamp_path = os.path.join(out_dir, '.stamp')
    digest = sources_hash()
    if os.path.exists(stamp_path):
        with open(stamp_path) as f:
            if f.read().strip() == digest:
                return
    print('Generating assets...')
    gen_font(out_dir)
    gen_sprites(out_dir)
    gen_data(out_dir)
    gen_bgs(out_dir)
    gen_zones(out_dir, True)
    with open(stamp_path, 'w') as f:
        f.write(digest)


if __name__ == '__main__':
    main()
