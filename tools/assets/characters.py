"""Humanoid characters: the 8 classic playable races plus humanoid enemies, built from ASCII heads and a
parametric body. Class outfits are just palette swaps done at runtime (palette indices 6-10)."""

from core import Canvas

# Palette indices shared by every humanoid sprite.
O, SK, SKD, HR, HRD, AR, ARD, TR, LG, BT, EY, AC, ACD, MT, WH = range(1, 16)

MAP = {'o': O, 's': SK, 'S': SKD, 'h': HR, 'H': HRD, 'r': AR, 'R': ARD, 't': TR, 'l': LG, 'b': BT,
       'e': EY, 'a': AC, 'A': ACD, 'm': MT, 'w': WH}

# Frame order inside every humanoid sprite sheet.
DIRS = ('down', 'up', 'side')
FRAMES_PER_DIR = 4   # stand, step a, step b, attack
FRAME_W, FRAME_H = 16, 32


class Build:
    """Body proportions. y values are rows inside the 16x32 frame; feet always end at row 30."""

    def __init__(self, head_y, torso_y, hip_y, torso_w, leg_w=2, leg_gap=2, arm_len=None, hunch=0):
        self.head_y = head_y
        self.torso_y = torso_y
        self.hip_y = hip_y
        self.torso_w = torso_w
        self.leg_w = leg_w
        self.leg_gap = leg_gap
        self.arm_len = arm_len
        self.hunch = hunch


# ---------------------------------------------------------------------------------------------------------------------
# Heads: front / back / side (side faces right). Rows of any width, centered on x = 8.
# ---------------------------------------------------------------------------------------------------------------------

HEADS = {}

HEADS['human'] = dict(
    front=['..hhhh..',
           '.hhhhhhh',
           'hhsssshh',
           '.sesses.',
           '.ssssss.',
           '.ssSSss.',
           '..ssss..'],
    back=['..hhhh..',
          '.hhhhhh.',
          'hhhhhhhh',
          '.hhhhhh.',
          '.hHhhHh.',
          '.hhhhhh.',
          '..ssss..'],
    side=['..hhhh..',
          '.hhhhhhh',
          'hhhhssss',
          '.hhssses',
          '.hhsssss',
          '..hsSSs.',
          '...sss..'])

HEADS['dwarf'] = dict(
    front=['...hhhh...',
           '..hhhhhh..',
           '..hssssh..',
           '..sesses..',
           '.hssSSssh.',
           '.hhhsshhh.',
           '.hhhhhhhh.',
           '..hhhhhh..',
           '..hHhhHh..',
           '...hHHh...',
           '....hh....'],
    back=['...hhhh...',
          '..hhhhhh..',
          '..hhhhhh..',
          '..hhhhhh..',
          '..hHhhHh..',
          '.hhhhhhhh.',
          '.h......h.'],
    side=['...hhhh...',
          '..hhhhhh..',
          '..hhhsssss',
          '..hhssses.',
          '..hhsssSSs',
          '..hhhhhhhh',
          '...hhhhhhh',
          '....hhhhh.',
          '....hHHh..',
          '.....hh...'])

HEADS['nightelf'] = dict(
    front=['....hhhhh...',
           '...hhhhhhh..',
           'aa.hhsssshh.aa'[0:12],
           '.aahsesseshaa'[0:12],
           '...hssssssh.',
           '...hhsSSshh.',
           '...hh.ss.hh.',
           '...hh....hh.'],
    back=['....hhhhh...',
          '...hhhhhhh..',
          'aa.hhhhhhh.a',
          '.aahhhhhhhaa',
          '...hhHhHhh..',
          '...hhhhhhh..',
          '...hhhhhhh..',
          '....hhhhh...'],
    side=['...hhhhh....',
          '..hhhhhhh...',
          '.hhhhhssss..',
          'hhaahsssess.',
          'hh.aassssss.',
          'hh..hsSSss..',
          'hh...ssss...',
          '.h..........'])

HEADS['gnome'] = dict(
    front=['..h....h..',
           '.hhh..hhh.',
           '..hhhhhh..',
           '.hhhhhhhh.',
           'hhsssssshh',
           '.ssessess.',
           '.ssssssss.',
           '..ssSSss..',
           '...ssss...'],
    back=['..h....h..',
          '.hhh..hhh.',
          '..hhhhhh..',
          '.hhhhhhhh.',
          'hhhhhhhhhh',
          '.hhHhhHhh.',
          '.hhhhhhhh.',
          '..hhhhhh..',
          '...ssss...'],
    side=['...h..h...',
          '..hhh.hhh.',
          '...hhhhhh.',
          '..hhhhhhhh',
          '.hhhhsssss',
          '.hhhssssess'[0:10],
          '.hhsssssss',
          '..hssSSss.',
          '...sssss..'])

HEADS['orc'] = dict(
    front=['....hh....',
           '...hhhh...',
           '..ssssss..',
           '.sSssssSs.',
           '.sesSSses.',
           '.ssssssss.',
           '.saSSSSas.',
           '..ssssss..'],
    back=['....hh....',
          '...hhhh...',
          '..hhhhhh..',
          '.sshhhhss.',
          '.ssshhsss.',
          '.ssssssss.',
          '.ssssssss.',
          '..ssssss..'],
    side=['...hh.....',
          '..hhhh....',
          '..hhssss..',
          '.hsssSsss.',
          '.ssssseSss'[0:10],
          '.sssssssss',
          '..sssssaS.',
          '...sssss..'])

HEADS['undead'] = dict(
    front=['..hhhh..',
           '.hhhhhh.',
           'hhsssshh',
           'hseSSesh',
           '.SssssS.',
           '.SaAaAS.',
           '..aAaA..'],
    back=['..hhhh..',
          '.hhhhhh.',
          'hhhhhhhh',
          'hhhhhhhh',
          '.hHhhHh.',
          '..hhhh..',
          '..SSSS..'],
    side=['..hhhh..',
          '.hhhhhhh',
          'hhhhssss',
          'hhhsSses',
          '.hhSssss',
          '..SSaAaA',
          '...SaAa.'])

HEADS['tauren'] = dict(
    front=['aa..........aa',
           '.aa........aa.',
           '..aa.hhhh.aa..',
           '...aahhhhaa...',
           '....hsssshh...'[0:14],
           '....sesseS....'[0:14],
           '....ssssss....',
           '...swwwwwws...'[0:14],
           '...swSwwSws...'[0:14],
           '....swwwws....',
           '.....hhhh.....'],
    back=['aa..........aa',
          '.aa........aa.',
          '..aa.hhhh.aa..',
          '...aahhhhaa...',
          '....hhhhhh....',
          '....hhhhhh....',
          '....hHhhHh....',
          '....hhhhhh....',
          '...hhhhhhhh...',
          '....hhhhhh....'],
    side=['.......aa.....',
          '......aa.aa...',
          '.....hhhhhaa..',
          '....hhhhhh.a..',
          '....hhhssss...',
          '....hhsssess..',
          '....hsssswwww.',
          '....hssswwwSw.',
          '.....hhswwwww.',
          '......hhhww...'])

HEADS['troll'] = dict(
    front=['.....hh.....',
           '....hhhh....',
           '....hhhh....',
           'a...ssss...a',
           'aa.ssssss.aa',
           '.aasesseSsa.'[0:12],
           '...ssssss...',
           '..aSSSSSSa..',
           '..a.ssss.a..'],
    back=['.....hh.....',
          '....hhhh....',
          '....hhhh....',
          'a...ssss...a',
          'aa.ssssss.aa',
          '.aassssssaa.',
          '...ssssss...',
          '...ssssss...',
          '....ssss....'],
    side=['..hh........',
          '.hhhh.......',
          '..hhhh......',
          '..sssss.....',
          '.aassssss...',
          'aa.sssssess.',
          '...sssssssss',
          '....sssSSaa.',
          '....sssss.a.'])

# Humanoid enemy heads.
HEADS['kobold'] = dict(   # rat-dog face with a candle on the head ("You no take candle!")
    front=['....e.....',
           '....w.....',
           '...AwA....',
           '.hhhhhhh..',
           'hhsssssh..',
           '.hsesesh..',
           '..sssss...',
           '..sSoSs...',
           '...www....'],
    back=['....e.....',
          '....w.....',
          '...AwA....',
          '.hhhhhhh..',
          'hhhhhhhhh.',
          '.hhhhhhh..',
          '..hhhhh...',
          '..hhhhh...',
          '...hhh....'],
    side=['...e......',
          '...w......',
          '..AwA.....',
          '.hhhhhh...',
          'hhhhhsss..',
          '.hhhsseSss',
          '..hssssssS',
          '..hsssSwo.',
          '...sss....'])

HEADS['trogg'] = dict(    # stone skinned, jutting jaw
    front=['...SSSS...',
           '..SssssS..',
           '.SsesseSS.'[0:10],
           '.SssSSssS.',
           'SsaaaaaasS',
           'SsSSSSSSsS',
           '.SssssssS.',
           '..SSSSSS..'],
    back=['...SSSS...',
          '..SssssS..',
          '.SssssssS.',
          '.SsSssSsS.',
          'SssssssssS',
          'SssssssssS',
          '.SssssssS.',
          '..SSSSSS..'],
    side=['..SSSS....',
          '.SssssS...',
          '.SsssesS..',
          'SsssssssS.',
          'SssssaaaaS',
          'SssssSSSSS',
          '.SsssssSS.',
          '..SSSSS...'])

HEADS['skeleton'] = dict(
    front=['..ssss..',
           '.ssssss.',
           'ssssssss',
           'sOOssOOs',
           'sOesseOs'[0:8],
           '.ssOOss.',
           '.sSsSsS.',
           '..sSsS..'],
    back=['..ssss..',
          '.ssssss.',
          'ssssssss',
          'ssssssss',
          'sSssssSs',
          '.ssssss.',
          '..ssss..',
          '...SS...'],
    side=['..ssss..',
          '.ssssss.',
          'ssssssss',
          'sssssOOs',
          'sssssOes',
          '.sssssOs',
          '..ssSsSs',
          '...sSsS.'])

HEADS['quilboar'] = dict(  # boar head with spines
    front=['.a.a..a.a.',
           '..aaaaaa..',
           '.ahhhhhha.',
           '.hheHHehh.',
           '.hhhhhhhh.',
           '.whssssbw.'[0:10],
           '.wssSSssw.',
           '..ssssss..'],
    back=['.a.a..a.a.',
          '..aaaaaa..',
          '.aahhhhaa.',
          '.ahhhhhha.',
          '.hhhHHhhh.',
          '.hhhhhhhh.',
          '..hhhhhh..',
          '...hhhh...'],
    side=['a.a.a.....',
          '.aaaaa....',
          'aahhhhhh..',
          'ahhhhehh..',
          '.hhhhhhsss',
          '.hhhhhssSs',
          '..hhhhsssw',
          '...hhhh.w.'])

for race in list(HEADS):
    HEADS[race]['front'] = [r.replace('O', 'o') for r in HEADS[race]['front']]
    HEADS[race]['side'] = [r.replace('O', 'o') for r in HEADS[race]['side']]

BUILDS = {
    'human': Build(head_y=8, torso_y=15, hip_y=23, torso_w=8),
    'dwarf': Build(head_y=10, torso_y=17, hip_y=25, torso_w=10, leg_w=3, leg_gap=2),
    'nightelf': Build(head_y=5, torso_y=13, hip_y=22, torso_w=8),
    'gnome': Build(head_y=13, torso_y=22, hip_y=27, torso_w=6, leg_w=2, leg_gap=2),
    'orc': Build(head_y=8, torso_y=15, hip_y=23, torso_w=10, leg_w=3, leg_gap=2, hunch=1),
    'undead': Build(head_y=7, torso_y=14, hip_y=22, torso_w=6, leg_w=2, leg_gap=2),
    'tauren': Build(head_y=2, torso_y=13, hip_y=23, torso_w=12, leg_w=4, leg_gap=2),
    'troll': Build(head_y=4, torso_y=13, hip_y=22, torso_w=8, leg_w=2, leg_gap=2, hunch=1),
    'kobold': Build(head_y=11, torso_y=20, hip_y=26, torso_w=6),
    'trogg': Build(head_y=10, torso_y=17, hip_y=25, torso_w=10, leg_w=3, leg_gap=2, hunch=1),
    'skeleton': Build(head_y=7, torso_y=15, hip_y=23, torso_w=6),
    'quilboar': Build(head_y=8, torso_y=15, hip_y=23, torso_w=10, leg_w=3, leg_gap=2, hunch=1),
}

# Races whose feet are hooves (no boots palette).
HOOVES = ('tauren',)


def draw_head(c, rows, top, flip=False):
    w = len(rows[0])
    x0 = 8 - w // 2
    c.ascii(x0, top, rows, MAP, flip=flip)


def draw_humanoid(race, direction, frame, robe=False):
    """direction: down / up / side. frame: 0 stand, 1 step a, 2 step b, 3 attack."""
    b = BUILDS[race]
    c = Canvas(FRAME_W, FRAME_H)
    tw = b.torso_w
    tx0 = 8 - tw // 2
    feet = 30
    bob = 1 if frame in (1, 2) else 0
    ty = b.torso_y + bob
    hy = b.hip_y + bob
    head_y = b.head_y + bob
    hooves = race in HOOVES

    # Legs.
    if direction in ('down', 'up'):
        gap = b.leg_gap
        lw = b.leg_w
        lx = 8 - gap // 2 - lw
        rx = 8 + (gap + 1) // 2
        lift_l = 1 if frame == 1 else 0
        lift_r = 1 if frame == 2 else 0
        for (x, lift) in ((lx, lift_l), (rx, lift_r)):
            bottom = feet - lift
            c.rect(x, hy, lw, bottom - hy + 1, LG)
            c.rect(x, bottom - 1, lw, 2, ACD if hooves else BT)
        if robe:
            c.rect(tx0, hy, tw, feet - 2 - hy, AR)
            c.rect(tx0 + tw - 1, hy, 1, feet - 2 - hy, ARD)
            c.rect(tx0, feet - 3, tw, 1, TR)
    else:
        lw = b.leg_w
        cx = 8 - lw // 2
        if frame in (1, 2):
            spread = 2 if frame == 1 else -2
            for s, col in ((spread, LG), (-spread, LG)):
                x = cx + s
                c.line(cx, hy, x, feet - 1, col)
                c.rect(min(cx, x), hy, lw, 2, col)
                for k in range(lw):
                    c.line(cx + k, hy, x + k, feet - 1, col)
                c.rect(x, feet - 1, lw + 1, 2, ACD if hooves else BT)
        else:
            c.rect(cx, hy, lw + 1, feet - hy, LG)
            c.rect(cx, feet - 1, lw + 2, 2, ACD if hooves else BT)
        if robe:
            c.rect(cx - 1, hy, lw + 3, feet - 2 - hy, AR)
            c.rect(cx - 1, feet - 3, lw + 3, 1, TR)

    # Torso.
    if direction in ('down', 'up'):
        c.rect(tx0, ty, tw, hy - ty, AR)
        c.rect(tx0 + tw - 1, ty, 1, hy - ty, ARD)
        c.rect(tx0, hy - 1, tw, 1, TR)          # belt
        if direction == 'down':
            c.rect(7, ty, 2, 1, TR)              # collar
        # Shoulders.
        c.rect(tx0 - 1, ty, 2, 2, TR)
        c.rect(tx0 + tw - 1, ty, 2, 2, TR)
        # Arms.
        arm_len = b.arm_len or (hy - ty)
        swing_l = -1 if frame == 1 else (1 if frame == 2 else 0)
        if frame == 3:
            # Attack: right arm raised forward.
            c.rect(tx0 - 1, ty + 1, 1, arm_len, AR)
            c.rect(tx0 - 1, ty + arm_len, 1, 2, SK)
            c.rect(tx0 + tw, ty - 2, 1, 4, AR)
            c.rect(tx0 + tw, ty - 3, 1, 2, SK)
        else:
            c.rect(tx0 - 1, ty + 1, 1, arm_len + swing_l, AR)
            c.rect(tx0 - 1, ty + arm_len + swing_l, 1, 2, SK)
            c.rect(tx0 + tw, ty + 1, 1, arm_len - swing_l, ARD)
            c.rect(tx0 + tw, ty + arm_len - swing_l, 1, 2, SK)
    else:
        sw = max(tw - 2, 4)
        sx0 = 8 - sw // 2 + b.hunch
        c.rect(sx0, ty, sw, hy - ty, AR)
        c.rect(sx0, ty, 1, hy - ty, ARD)
        c.rect(sx0, hy - 1, sw, 1, TR)
        c.rect(sx0 + 1, ty, sw - 2, 2, TR)
        arm_len = b.arm_len or (hy - ty)
        ax = 8 + b.hunch
        if frame == 3:
            c.rect(ax, ty + 2, 5, 2, AR)
            c.rect(ax + 5, ty + 2, 2, 2, SK)
        else:
            off = {0: 0, 1: 1, 2: -1}[frame]
            c.line(ax, ty + 1, ax + off, ty + arm_len - 1, AR)
            c.line(ax - 1, ty + 1, ax - 1 + off, ty + arm_len - 1, ARD)
            c.rect(ax - 1 + off, ty + arm_len, 2, 2, SK)

    # Head (drawn last so beards and tusks overlap the torso).
    heads = HEADS[race]
    if direction == 'down':
        draw_head(c, heads['front'], head_y)
    elif direction == 'up':
        draw_head(c, heads['back'], head_y)
    else:
        draw_head(c, heads['side'], head_y + (1 if b.hunch else 0))

    c.outline(O)
    return c


def humanoid_sheet(race, robe=False):
    frames = []
    for d in DIRS:
        for f in range(FRAMES_PER_DIR):
            frames.append(draw_humanoid(race, d, f, robe))
    return frames


# ---------------------------------------------------------------------------------------------------------------------
# Palettes.
# ---------------------------------------------------------------------------------------------------------------------

OUTLINE = (24, 18, 22)

# skin, skin dark, hair, hair dark, eyes, accent, accent dark
RACE_COLORS = {
    'human': [(240, 188, 148), (196, 136, 100), (120, 74, 36), (78, 46, 22), (40, 48, 96), (240, 188, 148), (180, 120, 90)],
    'dwarf': [(238, 170, 128), (190, 118, 86), (200, 88, 34), (136, 52, 20), (40, 40, 60), (200, 88, 34), (120, 80, 60)],
    'nightelf': [(160, 124, 210), (112, 82, 160), (64, 180, 180), (34, 110, 124), (232, 250, 255), (160, 124, 210), (112, 82, 160)],
    'gnome': [(250, 210, 182), (210, 160, 130), (244, 96, 176), (172, 52, 124), (40, 96, 170), (250, 210, 182), (190, 140, 110)],
    'orc': [(98, 158, 62), (62, 108, 40), (40, 34, 34), (20, 18, 18), (40, 20, 10), (244, 238, 212), (180, 170, 140)],
    'undead': [(150, 168, 150), (96, 112, 104), (64, 52, 76), (36, 30, 46), (255, 228, 80), (224, 218, 192), (150, 140, 120)],
    'tauren': [(148, 100, 62), (98, 64, 38), (64, 42, 26), (40, 26, 16), (20, 14, 10), (238, 228, 200), (110, 90, 70)],
    'troll': [(92, 144, 196), (60, 98, 144), (228, 64, 44), (156, 36, 24), (255, 204, 70), (244, 238, 212), (180, 170, 140)],
    'kobold': [(190, 140, 90), (136, 96, 58), (110, 76, 44), (76, 50, 28), (255, 210, 50), (250, 246, 230), (120, 110, 100)],
    'trogg': [(150, 140, 120), (96, 88, 76), (90, 80, 70), (60, 52, 46), (255, 120, 40), (230, 220, 190), (120, 110, 90)],
    'skeleton': [(230, 224, 200), (160, 152, 128), (60, 50, 50), (30, 26, 26), (90, 255, 140), (230, 224, 200), (160, 152, 128)],
    'quilboar': [(220, 150, 140), (170, 100, 92), (120, 70, 50), (80, 44, 30), (255, 60, 40), (236, 226, 190), (130, 110, 80)],
}

# armor, armor dark, trim, legs, boots
CLASS_COLORS = {
    'warrior': [(168, 112, 64), (112, 70, 38), (196, 200, 210), (96, 80, 70), (70, 48, 30)],
    'paladin': [(208, 210, 220), (140, 144, 160), (240, 196, 60), (150, 150, 168), (110, 110, 128)],
    'hunter': [(112, 150, 70), (72, 100, 44), (150, 104, 60), (110, 84, 52), (80, 56, 34)],
    'rogue': [(70, 64, 72), (40, 36, 44), (150, 40, 40), (56, 50, 58), (36, 30, 34)],
    'priest': [(240, 240, 232), (180, 180, 190), (230, 196, 80), (220, 220, 214), (150, 140, 120)],
    'shaman': [(40, 100, 200), (24, 60, 140), (220, 180, 80), (110, 80, 50), (80, 56, 34)],
    'mage': [(120, 90, 210), (76, 54, 150), (120, 220, 250), (100, 70, 180), (60, 40, 110)],
    'warlock': [(90, 40, 110), (52, 22, 66), (100, 220, 60), (70, 30, 86), (40, 20, 50)],
    'druid': [(150, 96, 44), (100, 62, 28), (90, 170, 70), (110, 78, 44), (80, 56, 34)],
}

ROBE_CLASSES = ('priest', 'mage', 'warlock')

METAL = (200, 204, 214)
WHITE = (250, 250, 244)


def palette(race, outfit):
    rc = RACE_COLORS[race]
    skin, skin_d, hair, hair_d, eyes, acc, acc_d = rc
    a, ad, t, l, bo = outfit
    return [(0, 0, 0), OUTLINE, skin, skin_d, hair, hair_d, a, ad, t, l, bo, eyes, acc, acc_d, METAL, WHITE]
