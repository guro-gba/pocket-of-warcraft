"""Beasts and small creatures (32x32 frames, side view facing right). Frames: 0 stand, 1 step a, 2 step b, 3 attack."""

from core import Canvas

O, S, SD, H, HD, E, A, AD, W, X1, X2 = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
MAP = {'o': O, 's': S, 'S': SD, 'h': H, 'H': HD, 'e': E, 'a': A, 'A': AD, 'w': W, 'x': X1, 'X': X2}

FRAME = 32


def legs(c, positions, top, bottom, frame, color, foot=None, width=2):
    """positions: list of (x, phase) where phase 0/1 picks which half of the gait the leg follows."""
    for x, phase in positions:
        off = 0
        if frame in (1, 2):
            off = 1 if (frame == 1) == (phase == 0) else -1
        lift = 1 if off > 0 else 0
        for k in range(width):
            c.line(x + k, top, x + k + off, bottom - lift, color)
        if foot is not None:
            c.rect(x + off, bottom - lift, width, 1, foot)


BODIES = {}

BODIES['wolf'] = dict(
    art=['...................s..s...',
         '..................sSssSs..',
         'S.................sssesss.',
         'SS...............ssssssSSo',
         '.SSssssssssssssssssssssss.',
         '..SsssssssssssssssssssS...',
         '...sssssssssssssssssss....',
         '...SsssssssssssssssssS....',
         '....hhhhhhhhhhhhhhhhh.....'],
    y=17, legs=[(4, 0), (7, 1), (16, 1), (19, 0)], leg_top=25, foot=SD)

BODIES['nightsaber'] = dict(
    art=['.....................ss...',
         'SS..................sssss.',
         '.S.................sssesss',
         '..S................ssssssw',
         '..SsssSsssSsssSsssssssss..',
         '...ssSsssSsssSsssSssss....',
         '...sSsssSsssSsssSssss.....',
         '....ssssssssssssssss......',
         '....hhhhhhhhhhhhhhhh......'],
    y=17, legs=[(5, 0), (8, 1), (16, 1), (19, 0)], leg_top=25, foot=SD)

BODIES['boar'] = dict(
    art=['......H.H.H.H.H...........',
         '....HHHHHHHHHHHHH.........',
         '...SsssssssssssssSs.......',
         '..SssssssssssssssssSs.....',
         '.Sssssssssssssssssssses...',
         '.Ssssssssssssssssssssssss.',
         '.Sssssssssssssssssssssshhh',
         '..SssssssssssssssssssaAhhh',
         '...SssssssssssssssssS.aa..',
         '....hhhhhhhhhhhhhhhh......'],
    y=17, legs=[(5, 0), (8, 1), (15, 1), (18, 0)], leg_top=26, foot=AD)

BODIES['plainstrider'] = dict(
    art=['....................hh....',
         '...................hhhhaa.',
         '...................hehaaA.',
         '...................hhh....',
         '...................hh.....',
         '..................hh......',
         '..................hh......',
         'SS...............shh......',
         'SSSssssssssssssssss.......',
         '.SSSssssssssssssss........',
         '..SSSsssssssssssss........',
         '....SsssssssssssS.........',
         '......SssssssSS...........'],
    y=7, legs=[(9, 0), (12, 1)], leg_top=19, foot=AD, leg_w=1)

BODIES['scorpid'] = dict(
    art=['..........SSS.............',
         '.........SsssS............',
         '........Ss..aS............',
         '...........SA.............',
         '..........Ss..............',
         '.........Ss.........aa..aa',
         '.........Ss........aa....a',
         '...SSsSsSsSsSsSsSs.aSS..Sa',
         '..SsssSsssSsssSsssSSsaaaa.',
         '..SssssssssssssssssssSs...',
         '...SSSSSSSSSSSSSSSSSS.....'],
    y=16, legs=[(5, 0), (8, 1), (11, 0), (14, 1)], leg_top=26, foot=None, leg_w=1)

BODIES['bat'] = dict(
    art=['.......a.....a..........',
         '.......sS...Ss..........',
         '.......sssssss..........',
         '.......sesssse..........',
         '........swsws...........',
         '.........sss............'],
    y=12, legs=[], leg_top=0, foot=None)

BODIES['imp'] = dict(
    art=['...a......a...',
         '...aa....aa...',
         '....ssssss....',
         '...ssessess...',
         '...ssssssss...',
         '....sswwss....',
         '.....ssss.....',
         '...SssssssS...',
         '..SssssssssS..',
         '..s.ssssss.s..',
         '..s.SssssS.s..',
         '....ss..ss....'],
    y=15, legs=[(6, 0), (9, 1)], leg_top=27, foot=SD)

BODIES['grell'] = dict(
    art=['.aa........aa.',
         '..aaa....aaa..',
         '....ssssss....',
         '...ssessess...',
         '...ssssssss...',
         '....sswwss....',
         '.....ssss.....',
         '...SssssssS...',
         '..ShhhhhhhhS..',
         '..s.hhhhhh.s..',
         '..s.SssssS.s..',
         '....ss..ss....'],
    y=15, legs=[(6, 0), (9, 1)], leg_top=27, foot=SD)


def draw_wings(c, frame):
    # Bat wings: up on frames 0/2, down on 1/3.
    up = frame in (0, 2)
    for side in (-1, 1):
        cx = 15
        for i in range(1, 9):
            x = cx + side * (3 + i)
            y = 14 + (-(9 - i) // 2 if up else (i // 2))
            c.vline(x, y, y + (5 - i // 2), S if i % 3 else SD)
            c.set(x, y - 1 if up else y, SD)


def draw_beast(kind, frame):
    b = BODIES[kind]
    c = Canvas(FRAME, FRAME)
    art = b['art']
    w = len(art[0])
    x0 = 16 - w // 2
    lunge = 2 if frame == 3 else 0
    if kind == 'bat':
        bob = {0: 0, 1: 2, 2: 1, 3: 0}[frame]
        draw_wings(c, frame)
        c.ascii(x0 + 2, b['y'] + bob - 2, art, MAP)
        c.outline(O)
        return c
    if kind == 'scorpid' and frame == 3:
        # Tail strike: shift the stinger forward.
        art = [r[2:] + '..' if i < 5 else r for i, r in enumerate(art)]
    if b['legs']:
        legs(c, [(x0 + x + lunge, p) for x, p in b['legs']], b['leg_top'], 30, frame, SD, b['foot'],
             b.get('leg_w', 2))
    bob = 1 if frame in (1, 2) and kind != 'scorpid' else 0
    c.ascii(x0 + lunge, b['y'] + bob, art, MAP)
    c.outline(O)
    return c


def beast_sheet(kind):
    return [draw_beast(kind, f) for f in range(4)]


# palette: outline, main, main dark, secondary, secondary dark, eye, accent, accent dark, white, extra1, extra2
def pal(main, main_d, sec, sec_d, eye, acc, acc_d):
    return [(0, 0, 0), (24, 18, 22), main, main_d, sec, sec_d, eye, acc, acc_d, (250, 250, 244), (0, 0, 0),
            (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]


BEAST_PALETTES = {
    'young_wolf': ('wolf', pal((150, 146, 140), (96, 92, 90), (200, 196, 186), (150, 146, 140), (240, 200, 60), (40, 30, 30), (60, 56, 56))),
    'ragged_wolf': ('wolf', pal((176, 168, 160), (110, 104, 100), (236, 232, 224), (176, 168, 160), (120, 200, 255), (40, 30, 30), (80, 76, 76))),
    'prairie_wolf': ('wolf', pal((180, 140, 90), (124, 92, 56), (226, 200, 150), (180, 140, 90), (240, 200, 60), (40, 30, 30), (90, 70, 50))),
    'nightsaber': ('nightsaber', pal((84, 72, 140), (44, 36, 84), (150, 140, 200), (84, 72, 140), (140, 255, 230), (40, 30, 30), (40, 30, 70))),
    'mottled_boar': ('boar', pal((168, 100, 64), (110, 60, 36), (220, 190, 160), (60, 36, 24), (40, 10, 10), (244, 238, 212), (190, 180, 150))),
    'thistle_boar': ('boar', pal((120, 96, 120), (76, 58, 80), (200, 170, 190), (70, 140, 80), (255, 80, 60), (244, 238, 212), (190, 180, 150))),
    'battleboar': ('boar', pal((110, 70, 50), (66, 40, 28), (200, 160, 120), (40, 24, 16), (255, 60, 30), (250, 246, 220), (190, 180, 150))),
    'plainstrider': ('plainstrider', pal((150, 120, 90), (100, 76, 56), (210, 190, 160), (150, 130, 100), (30, 20, 20), (240, 170, 60), (180, 110, 40))),
    'scorpid': ('scorpid', pal((200, 96, 50), (130, 56, 30), (230, 140, 80), (130, 56, 30), (30, 20, 20), (240, 210, 120), (150, 110, 60))),
    'duskbat': ('bat', pal((90, 70, 90), (56, 40, 60), (140, 110, 130), (56, 40, 60), (255, 60, 60), (230, 220, 200), (150, 140, 120))),
    'vile_familiar': ('imp', pal((214, 70, 50), (140, 36, 26), (255, 160, 60), (140, 36, 26), (255, 240, 80), (60, 30, 30), (30, 20, 20))),
    'grellkin': ('grell', pal((110, 160, 60), (66, 104, 36), (130, 90, 60), (90, 60, 40), (255, 230, 60), (90, 120, 50), (60, 80, 30))),
}
