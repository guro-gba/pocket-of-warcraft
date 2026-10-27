"""The starting zones of the eight classic races. Coordinates are in 8 pixel cells; maps are 128x128 cells."""

import world as W
from world import Terrain
from zonebuilder import ZoneBuilder

SIZE = 128

# Shared palettes.
WOOD = [(140, 96, 56), (96, 62, 34)]
DARK_WOOD = [(100, 70, 46), (64, 44, 30)]
STONE = [(170, 166, 156), (200, 196, 186), (110, 106, 100)]
GREY_ROCK = [(70, 68, 66), (96, 94, 90), (124, 120, 114), (150, 146, 138), (178, 174, 166)]
METAL = (120, 120, 130)


def elwynn_leaves():
    return [(36, 80, 32), (52, 108, 40), (72, 136, 48), (98, 160, 60), (130, 186, 80)]


# ---------------------------------------------------------------------------------------------------------------------
# Northshire Valley (Human).
# ---------------------------------------------------------------------------------------------------------------------

def northshire():
    T = {
        'grass': Terrain('grass', 3, W.grass_tex((86, 150, 58), (68, 126, 46), (118, 176, 72),
                                                 [(250, 250, 250), (250, 220, 60), (220, 70, 70)]), variants=3,
                         weights=[0.55, 0.3, 0.15]),
        'dirt': Terrain('dirt', 2, W.dirt_tex((156, 120, 78), (126, 94, 60), (182, 146, 98)), variants=2),
        'road': Terrain('road', 1, W.cobble_tex((156, 152, 142), (124, 120, 112), (184, 180, 170), (96, 92, 86))),
        'water': Terrain('water', 0, W.water_tex((52, 102, 180), (44, 88, 160), (110, 160, 220)), solid=True),
        'rock': Terrain('rock', 4, W.rock_tex((110, 104, 96), (82, 78, 72), (140, 134, 124)), solid=True, variants=2),
    }
    z = ZoneBuilder('Northshire Valley', SIZE, SIZE, T, 'grass', seed=101)
    z.reserve(56, 31, 16, 14)
    z.edge_colors['water'] = (170, 200, 230)
    leaves = elwynn_leaves()
    trunk = [(110, 74, 44), (78, 50, 28), (140, 98, 60)]

    def oak(r):
        return W.tree_round(leaves, trunk, seed=r.rand(3))

    def pine(r):
        return W.tree_pine([(30, 86, 50), (44, 110, 62), (62, 136, 78)], trunk, seed=r.rand(3))

    # Echo Ridge (rocky hills, north-west) and the mine.
    z.ellipse('rock', 12, 10, 26, 20, noise=0.4)
    z.ellipse('grass', 22, 30, 9, 5)
    # Roads and paths.
    z.rect('road', 52, 30, 26, 8)
    z.path('road', [(64, 34), (63, 50), (60, 66), (64, 84), (66, 100), (64, 128)], 4)
    z.path('dirt', [(56, 36), (44, 38), (32, 34), (22, 30)], 3)
    z.path('dirt', [(72, 36), (86, 46), (96, 58), (104, 64)], 3)
    z.path('dirt', [(62, 70), (44, 80), (30, 90)], 2)
    # Pond south-east and the stream feeding it.
    z.ellipse('water', 98, 104, 12, 7, noise=0.3)
    z.path('water', [(124, 92), (112, 98), (104, 102)], 3)

    # Forest border (west/south/east), rocks to the north.
    z.forest_edge(lambda r: oak(r) if r.rand(3) else pine(r), 7, skip=lambda x, y: 58 <= x <= 70 and y > 110)
    z.block_border(2)

    # Northshire Abbey.
    z.place(W.abbey(STONE, [(60, 72, 110), (82, 98, 146), (98, 118, 170), (150, 166, 210)], (230, 196, 90)), 47, 13)
    z.area('Northshire Abbey', 44, 12, 40, 26)
    # Houses and stable.
    house_wall = [(232, 226, 210), (250, 246, 236), (150, 140, 120)]
    house_roof = [(52, 64, 104), (78, 96, 150), (96, 116, 170), (140, 156, 200)]
    z.place(W.building(48, 24, 24, house_wall, house_roof, (120, 84, 50), [(110, 72, 40), (80, 50, 28)],
                       timber=(110, 76, 46)), 30, 18)
    z.place(W.building(48, 24, 24, house_wall, house_roof, (120, 84, 50), [(110, 72, 40), (80, 50, 28)],
                       timber=(110, 76, 46)), 90, 26)
    z.place(W.well(STONE, WOOD, (60, 110, 190)), 80, 38)
    z.place(W.signpost(WOOD), 60, 52)
    for x in range(40, 50, 2):
        z.place(W.fence(WOOD), x, 26)
    # Echo Ridge Mine.
    z.place(W.mine_entrance(GREY_ROCK, WOOD), 16, 22)
    z.place(W.crate(WOOD), 24, 30)
    z.place(W.barrel(WOOD, METAL), 13, 30)
    z.place(W.campfire(), 28, 36)
    z.area('Echo Ridge Mine', 6, 18, 30, 26)
    # Northshire Vineyards.
    for i, y in enumerate(range(62, 88, 4)):
        z.place(W.vine_rows([(60, 120, 50), (90, 150, 60)], (110, 50, 120), (110, 80, 50), 64), 92 - (i % 2) * 2, y)
    z.place(W.haystack([(150, 120, 40), (190, 160, 60), (220, 196, 90), (240, 220, 130)]), 88, 58)
    z.place(W.building(40, 24, 20, house_wall, [(110, 50, 40), (150, 70, 52), (170, 86, 60), (200, 120, 90)],
                       (120, 84, 50), [(110, 72, 40), (80, 50, 28)], timber=(110, 76, 46)), 110, 52)
    z.area('Northshire Vineyards', 86, 54, 36, 36)
    # Wolf woods.
    z.scatter(oak, 12, 64, 36, 44, 16, margin=1)
    z.scatter(lambda r: W.bush([(40, 90, 36), (56, 116, 44), (80, 140, 56), (110, 170, 70)], (200, 40, 60)),
              10, 40, 108, 80, 18)
    z.scatter(lambda r: W.rock(GREY_ROCK, seed=r.rand(5)), 8, 8, 112, 112, 14)
    z.scatter(oak, 70, 88, 20, 24, 5, margin=1)
    z.area('Northshire Woods', 8, 60, 44, 56)

    # Gameplay.
    z.start = (64 * 8 + 4, 40 * 8)
    z.grave = (84 * 8, 48 * 8)
    z.npc('marshal_mcbride', 61, 37)
    z.npc('deputy_willem', 67, 41, 1)
    z.npc('eagan_peltskinner', 54, 45)
    z.npc('brother_paxton', 70, 37)
    z.spawn('kobold_vermin', 18, 34, 26, 16, 8)
    z.spawn('kobold_worker', 6, 44, 22, 20, 7)
    z.spawn('young_wolf', 12, 66, 34, 40, 10)
    z.spawn('defias_thug', 90, 60, 26, 28, 8)
    return z


# ---------------------------------------------------------------------------------------------------------------------
# Coldridge Valley (Dwarf & Gnome).
# ---------------------------------------------------------------------------------------------------------------------

def coldridge():
    T = {
        'snow': Terrain('snow', 3, W.snow_tex((228, 234, 244), (196, 206, 226), (250, 252, 255)), variants=2),
        'trail': Terrain('trail', 2, W.dirt_tex((176, 166, 160), (146, 136, 132), (204, 196, 192))),
        'ice': Terrain('ice', 1, W.cracked_tex((160, 204, 232), (130, 180, 214), (200, 230, 248)), variants=2),
        'rock': Terrain('rock', 4, W.rock_tex((112, 112, 122), (84, 84, 96), (150, 150, 162)), solid=True, variants=2),
        'water': Terrain('water', 0, W.water_tex((50, 90, 160), (40, 76, 140), (120, 170, 220)), solid=True),
    }
    z = ZoneBuilder('Coldridge Valley', SIZE, SIZE, T, 'snow', seed=202)
    z.reserve(56, 21, 16, 14)
    z.edge_colors['ice'] = (236, 246, 255)
    trunk = [(100, 70, 46), (70, 48, 30), (130, 90, 60)]
    pine_leaves = [(26, 70, 54), (38, 92, 68), (54, 116, 84)]
    snow = [(240, 244, 252), (206, 216, 234)]

    def pine(r):
        return W.tree_pine(pine_leaves, trunk, snow=snow, seed=r.rand(3))

    z.border('rock', 9, noise=5)
    z.ellipse('rock', 64, 2, 30, 14, noise=0.3)
    z.ellipse('ice', 92, 58, 14, 9, noise=0.3)
    z.ellipse('water', 92, 58, 6, 3, noise=0.2)
    z.path('trail', [(64, 26), (62, 44), (58, 64), (54, 84), (56, 104), (60, 128)], 3)
    z.path('trail', [(60, 50), (44, 50), (30, 48)], 2)
    z.path('trail', [(56, 84), (40, 92), (26, 96)], 2)
    z.path('trail', [(62, 44), (78, 46), (90, 44)], 2)
    z.block_border(3)

    rock_cols = [(80, 80, 92), (104, 104, 116), (128, 128, 140), (156, 156, 168), (190, 190, 200)]
    z.place(W.anvilmar(rock_cols, [(150, 146, 140), (176, 172, 166), (104, 100, 96)], (200, 160, 70)), 56, 4)
    z.area('Anvilmar', 44, 4, 40, 26)
    z.place(W.campfire(), 72, 28)
    z.place(W.crate(WOOD), 48, 22)
    z.place(W.barrel(WOOD, METAL), 50, 24)
    # Frostmane troll camp (west).
    hut_wall = [(150, 120, 90), (120, 94, 70)]
    z.place(W.frostmane_hut(hut_wall, (240, 244, 252), (230, 222, 196)), 18, 38)
    z.place(W.frostmane_hut(hut_wall, (240, 244, 252), (230, 222, 196)), 28, 56)
    z.place(W.bones_pile((226, 218, 196)), 26, 46)
    z.place(W.campfire(), 24, 50)
    z.area('Frostmane Camp', 12, 34, 30, 30)
    # Trogg cave (south-west).
    z.place(W.cave_entrance(rock_cols, 48, 40), 14, 88)
    z.area('Coldridge Pass', 10, 80, 36, 36)
    z.scatter(lambda r: W.ice_crystals([(170, 220, 250), (230, 248, 255)]), 80, 66, 30, 20, 6)
    z.scatter(pine, 10, 10, 108, 108, 46, margin=1)
    z.scatter(lambda r: W.rock(rock_cols, seed=r.rand(5)), 10, 10, 108, 108, 18)
    z.scatter(lambda r: W.boulder_big(rock_cols, seed=r.rand(5)), 12, 30, 100, 80, 6, margin=1)

    z.start = (64 * 8 + 4, 30 * 8)
    z.grave = (78 * 8, 34 * 8)
    z.npc('sten_stoutarm', 60, 28)
    z.npc('balir_frosthammer', 68, 30)
    z.npc('grelin_whitebeard', 44, 52)
    z.spawn('ragged_young_wolf', 66, 66, 40, 34, 10)
    z.spawn('rockjaw_trogg', 18, 92, 30, 22, 9)
    z.spawn('burly_rockjaw_trogg', 34, 100, 20, 16, 5)
    z.spawn('frostmane_whelp', 14, 40, 28, 26, 9)
    return z


# ---------------------------------------------------------------------------------------------------------------------
# Shadowglen (Night Elf).
# ---------------------------------------------------------------------------------------------------------------------

def shadowglen():
    T = {
        'moss': Terrain('moss', 3, W.grass_tex((58, 98, 76), (44, 80, 64), (76, 120, 90),
                                               [(200, 140, 250), (160, 230, 250), (250, 200, 250)], seed=4),
                        variants=3, weights=[0.6, 0.28, 0.12]),
        'path': Terrain('path', 2, W.dirt_tex((128, 108, 132), (102, 84, 108), (156, 134, 160))),
        'water': Terrain('water', 0, W.water_tex((50, 90, 150), (40, 74, 130), (130, 200, 230)), solid=True),
    }
    z = ZoneBuilder('Shadowglen', SIZE, SIZE, T, 'moss', seed=303)
    z.reserve(56, 33, 16, 14)
    z.edge_colors['water'] = (150, 220, 230)
    leaves = [(30, 70, 80), (40, 96, 104), (56, 124, 126), (80, 150, 146), (120, 186, 176)]
    trunk = [(116, 90, 120), (80, 60, 90), (150, 120, 150)]

    def tree(r):
        return W.tree_teldrassil(leaves, trunk, (190, 250, 230), seed=r.rand(3))

    z.path('path', [(64, 38), (64, 60), (58, 80), (62, 100), (64, 128)], 3)
    z.path('path', [(64, 46), (44, 52), (28, 60)], 2)
    z.path('path', [(64, 46), (84, 52), (100, 60), (108, 66)], 2)
    z.ellipse('path', 64, 40, 14, 6)
    z.ellipse('water', 36, 100, 10, 6, noise=0.3)
    z.forest_edge(tree, 7, skip=lambda x, y: 58 <= x <= 70 and y > 112)
    z.block_border(2)

    z.place(W.aldrassil([(126, 98, 120), (92, 70, 92), (160, 128, 150)], leaves, (200, 255, 230), (40, 24, 50)), 50, 6)
    z.area('Aldrassil', 46, 6, 36, 34)
    z.place(W.moonwell([(150, 150, 170), (190, 190, 210)], (70, 120, 200), (170, 240, 255)), 78, 36)
    z.place(W.nightelf_house([(150, 120, 170), (120, 94, 140)], [(110, 70, 140), (140, 94, 170), (80, 50, 110)],
                             (200, 180, 230)), 32, 34)
    z.place(W.nightelf_house([(150, 120, 170), (120, 94, 140)], [(110, 70, 140), (140, 94, 170), (80, 50, 110)],
                             (200, 180, 230)), 86, 20)
    # Fel Rock (grell cave, east).
    rock_cols = [(70, 60, 80), (90, 80, 104), (112, 100, 128), (136, 124, 150), (160, 150, 176)]
    z.place(W.cave_entrance(rock_cols, 48, 40, inner=(30, 50, 20)), 104, 56)
    z.area('Fel Rock', 92, 52, 32, 30)
    z.area('Shadowglen Woods', 8, 50, 40, 50)
    z.scatter(tree, 10, 48, 108, 70, 24, margin=1)
    z.scatter(lambda r: W.bush([(30, 70, 70), (40, 96, 90), (60, 120, 110), (90, 150, 140)], (220, 120, 250)),
              10, 10, 108, 108, 22)
    z.scatter(lambda r: W.rock(rock_cols, seed=r.rand(5)), 10, 10, 108, 108, 10)

    z.start = (64 * 8 + 4, 42 * 8)
    z.grave = (44 * 8, 46 * 8)
    z.npc('conservator_ilthalaine', 60, 40)
    z.npc('tenaron_stormgrip', 69, 39)
    z.npc('melithar_staghelm', 74, 44)
    z.spawn('young_nightsaber', 12, 52, 34, 40, 10)
    z.spawn('young_thistle_boar', 40, 84, 46, 26, 10)
    z.spawn('grellkin', 92, 64, 28, 24, 9)
    return z


# ---------------------------------------------------------------------------------------------------------------------
# Valley of Trials (Orc & Troll).
# ---------------------------------------------------------------------------------------------------------------------

def valley_of_trials():
    T = {
        'dirt': Terrain('dirt', 3, W.cracked_tex((196, 116, 62), (166, 92, 48), (216, 144, 84)), variants=3,
                        weights=[0.6, 0.25, 0.15]),
        'path': Terrain('path', 2, W.dirt_tex((210, 160, 104), (180, 130, 80), (232, 186, 130))),
        'rock': Terrain('rock', 4, W.rock_tex((150, 80, 52), (114, 58, 38), (180, 110, 74)), solid=True, variants=2),
    }
    z = ZoneBuilder('Valley of Trials', SIZE, SIZE, T, 'dirt', seed=404)
    z.reserve(56, 31, 16, 14)
    rock_cols = [(110, 54, 36), (140, 74, 48), (168, 98, 64), (190, 124, 84), (214, 154, 110)]
    trunk = [(110, 76, 50), (80, 54, 36)]
    leaves = [(110, 100, 40), (140, 128, 52), (168, 150, 64), (196, 170, 80)]

    z.border('rock', 9, noise=6)
    z.ellipse('rock', 64, 0, 24, 8, noise=0.3)
    z.path('path', [(64, 30), (62, 50), (66, 70), (62, 90), (64, 128)], 3)
    z.path('path', [(62, 50), (42, 60), (28, 70)], 2)
    z.path('path', [(66, 46), (86, 46), (104, 46)], 2)
    z.path('path', [(66, 70), (86, 84), (98, 96)], 2)
    z.ellipse('path', 64, 30, 16, 8, noise=0.3)
    z.block_border(3)

    hut_wall = [(150, 100, 60), (120, 78, 46)]
    hut_roof = [(170, 120, 70), (140, 96, 56), (196, 146, 90)]
    z.place(W.hut_round(hut_wall, hut_roof, (230, 220, 190), 64, 56, spikes=(240, 232, 210), banner=(170, 30, 30)), 56, 10)
    z.area('The Den', 48, 8, 32, 30)
    z.place(W.hut_round(hut_wall, hut_roof, (230, 220, 190), 48, 48, spikes=(240, 232, 210)), 38, 18)
    z.place(W.hut_round(hut_wall, hut_roof, (230, 220, 190), 48, 48, spikes=(240, 232, 210), banner=(170, 30, 30)), 78, 20)
    for x in range(44, 56, 2):
        z.place(W.palisade(DARK_WOOD), x, 34)
    for x in range(74, 86, 2):
        z.place(W.palisade(DARK_WOOD), x, 34)
    z.place(W.banner_pole((170, 30, 30), (30, 20, 20), (90, 60, 40)), 57, 32)
    z.place(W.banner_pole((170, 30, 30), (30, 20, 20), (90, 60, 40)), 70, 32)
    z.place(W.campfire(), 64, 40)
    # Burning Blade Coven (east cave with imps).
    z.place(W.cave_entrance(rock_cols, 48, 40, inner=(40, 10, 10)), 104, 30)
    z.area('Burning Blade Coven', 92, 28, 30, 30)
    z.area('Scorpid Hollow', 70, 80, 44, 36)
    z.area('Boar Run', 10, 56, 40, 44)
    z.scatter(lambda r: W.tree_savanna(leaves, trunk, seed=r.rand(3)), 10, 10, 108, 108, 26, margin=1)
    z.scatter(lambda r: W.rock(rock_cols, seed=r.rand(5)), 10, 10, 108, 108, 22)
    z.scatter(lambda r: W.boulder_big(rock_cols, seed=r.rand(5)), 10, 40, 108, 76, 8, margin=1)
    z.scatter(lambda r: W.grass_tuft([(150, 140, 60), (120, 110, 50), (180, 160, 80)]), 10, 10, 108, 108, 30)
    z.scatter(lambda r: W.bones_pile((236, 228, 206)), 10, 50, 108, 70, 6)

    z.start = (64 * 8 + 4, 40 * 8)
    z.grave = (40 * 8, 46 * 8)
    z.npc('gornek', 61, 38)
    z.npc('zureetha_fargaze', 68, 37, 1)
    z.npc('galgar', 58, 44)
    z.spawn('mottled_boar', 12, 58, 36, 40, 10)
    z.spawn('scorpid_worker', 70, 82, 40, 30, 10)
    z.spawn('vile_familiar', 92, 36, 26, 22, 9)
    return z


# ---------------------------------------------------------------------------------------------------------------------
# Deathknell (Undead).
# ---------------------------------------------------------------------------------------------------------------------

def deathknell():
    T = {
        'deadgrass': Terrain('deadgrass', 3, W.grass_tex((116, 112, 76), (92, 90, 62), (140, 136, 92),
                                                         [(150, 150, 130), (90, 70, 90)], seed=7),
                             variants=3, weights=[0.6, 0.3, 0.1]),
        'mud': Terrain('mud', 2, W.dirt_tex((96, 86, 70), (76, 68, 56), (118, 106, 88))),
        'water': Terrain('water', 0, W.water_tex((60, 80, 80), (48, 64, 66), (100, 124, 120)), solid=True),
    }
    z = ZoneBuilder('Deathknell', SIZE, SIZE, T, 'deadgrass', seed=505)
    z.reserve(56, 23, 16, 14)
    wood = [(110, 100, 92), (80, 72, 66)]
    stone = [(130, 128, 124), (160, 156, 150), (90, 88, 86)]

    def dead(r):
        return W.tree_dead(wood, seed=r.rand(4))

    z.path('mud', [(64, 30), (62, 52), (66, 76), (62, 98), (64, 128)], 3)
    z.path('mud', [(62, 52), (40, 62), (24, 72)], 2)
    z.path('mud', [(66, 60), (88, 64), (104, 66)], 2)
    z.ellipse('mud', 64, 30, 16, 6)
    z.ellipse('water', 100, 96, 9, 5, noise=0.3)
    z.forest_edge(dead, 7, spacing=(3, 3), skip=lambda x, y: 58 <= x <= 70 and y > 112)
    z.block_border(2)

    z.place(W.chapel_ruin(stone, [(60, 50, 70), (80, 68, 92), (100, 86, 110), (130, 116, 140)], (170, 150, 110)), 70, 6)
    z.place(W.crypt(stone, (30, 24, 34)), 50, 12)
    z.area('Deathknell', 44, 6, 44, 30)
    # Graveyard.
    for i, (x, y) in enumerate([(36, 20), (40, 21), (44, 20), (36, 25), (40, 26), (44, 25), (36, 30), (40, 31), (44, 30)]):
        z.place(W.tombstone(stone, i % 3), x, y)
    for x in range(32, 48, 2):
        z.place(W.iron_fence((60, 60, 70)), x, 16)
    z.area('Deathknell Graveyard', 30, 14, 20, 22)
    # Scarlet Crusade camp (south).
    cloth = [(240, 236, 228), (200, 196, 190)]
    z.place(W.tent_scarlet(cloth, (190, 30, 40), (100, 80, 60)), 70, 96)
    z.place(W.tent_scarlet(cloth, (190, 30, 40), (100, 80, 60)), 86, 104)
    z.place(W.banner_pole((190, 30, 40), (240, 220, 120), (90, 70, 50)), 80, 94)
    z.place(W.campfire(), 80, 102)
    z.place(W.crate(WOOD), 92, 98)
    z.area('Scarlet Encampment', 64, 88, 40, 30)
    # Abandoned farm (west).
    z.place(W.building(48, 24, 24, [(130, 120, 106), (150, 140, 124), (90, 84, 74)],
                       [(60, 52, 50), (80, 70, 66), (96, 84, 80), (120, 108, 100)], (90, 80, 70),
                       [(70, 56, 46), (50, 40, 32)], timber=(80, 70, 60)), 14, 52)
    z.area('Night Web\'s Hollow', 8, 48, 40, 40)
    z.scatter(dead, 10, 40, 108, 76, 24, margin=1)
    z.scatter(lambda r: W.tombstone(stone, r.rand(3)), 10, 40, 108, 70, 10)
    z.scatter(lambda r: W.bones_pile((206, 200, 180)), 10, 30, 108, 80, 8)
    z.scatter(lambda r: W.rock([(70, 68, 66), (90, 88, 84), (110, 108, 102), (130, 126, 120)], seed=r.rand(5)),
              10, 10, 108, 108, 12)

    z.start = (64 * 8 + 4, 32 * 8)
    z.grave = (42 * 8, 36 * 8)
    z.npc('shadow_priest_sarvis', 60, 31)
    z.npc('executor_arren', 68, 31, 1)
    z.npc('novice_elreth', 54, 38)
    z.spawn('duskbat', 80, 46, 34, 30, 9)
    z.spawn('mindless_zombie', 12, 60, 34, 30, 10)
    z.spawn('rattlecage_skeleton', 22, 40, 26, 16, 6)
    z.spawn('scarlet_convert', 64, 90, 40, 26, 9)
    return z


# ---------------------------------------------------------------------------------------------------------------------
# Camp Narache (Tauren).
# ---------------------------------------------------------------------------------------------------------------------

def narache():
    T = {
        'plains': Terrain('plains', 3, W.grass_tex((150, 168, 72), (126, 144, 58), (178, 194, 96),
                                                   [(250, 240, 120), (240, 140, 60)], seed=9),
                          variants=3, weights=[0.6, 0.28, 0.12]),
        'path': Terrain('path', 2, W.dirt_tex((176, 136, 86), (148, 110, 68), (200, 160, 108))),
        'water': Terrain('water', 0, W.water_tex((60, 120, 180), (50, 100, 160), (130, 190, 230)), solid=True),
        'mesa': Terrain('mesa', 4, W.rock_tex((176, 100, 70), (140, 74, 52), (206, 134, 96)), solid=True, variants=2),
    }
    z = ZoneBuilder('Camp Narache', SIZE, SIZE, T, 'plains', seed=606)
    z.reserve(56, 41, 16, 14)
    z.edge_colors['water'] = (190, 220, 240)
    trunk = [(110, 76, 50), (80, 54, 36), (140, 100, 66)]
    leaves = [(54, 96, 40), (70, 120, 48), (94, 146, 60), (124, 170, 76), (160, 196, 100)]
    hide = [(206, 176, 130), (176, 146, 104), (226, 200, 156)]
    paint = [(180, 50, 40), (60, 90, 160)]

    z.border('mesa', 8, noise=6)
    z.path('path', [(64, 46), (64, 70), (60, 90), (64, 128)], 3)
    z.path('path', [(64, 40), (84, 32), (100, 28)], 2)
    z.path('path', [(60, 70), (40, 80), (26, 88)], 2)
    z.path('path', [(66, 76), (86, 92), (98, 100)], 2)
    z.ellipse('path', 64, 40, 18, 10, noise=0.3)
    z.path('water', [(0, 60), (20, 62), (34, 58), (46, 60)], 3)
    z.ellipse('water', 48, 60, 6, 4)
    z.block_border(3)

    z.place(W.totem(DARK_WOOD, [(190, 50, 40), (250, 240, 200)], [(240, 240, 230), (60, 90, 160)]), 62, 30)
    for (x, y) in [(46, 30), (74, 28), (44, 44), (76, 44), (56, 18)]:
        z.place(W.tent_tauren(hide, paint, (90, 60, 40)), x, y)
    z.place(W.campfire(), 64, 44)
    z.place(W.haystack([(150, 120, 40), (190, 160, 60), (220, 196, 90), (240, 220, 130)]), 54, 50)
    z.area('Camp Narache', 40, 14, 48, 40)
    # Bristleback camp (south-east).
    bramble = [(70, 50, 30), (96, 70, 40), (124, 94, 52), (150, 120, 70)]
    z.place(W.quilboar_hut(bramble, (220, 210, 170)), 96, 92)
    z.place(W.quilboar_hut(bramble, (220, 210, 170)), 106, 104)
    z.place(W.campfire(), 100, 102)
    z.area('Brambleblade Ravine', 82, 84, 38, 36)
    z.area('Red Cloud Mesa', 8, 8, 112, 10)
    z.scatter(lambda r: W.tree_round(leaves, trunk, seed=r.rand(3)), 10, 10, 108, 108, 16, margin=2)
    z.scatter(lambda r: W.grass_tuft([(120, 140, 50), (170, 190, 80), (200, 210, 110)]), 10, 10, 108, 108, 40)
    rock_cols = [(130, 70, 50), (160, 92, 64), (190, 120, 84), (214, 150, 110)]
    z.scatter(lambda r: W.rock(rock_cols, seed=r.rand(5)), 10, 10, 108, 108, 18)
    z.scatter(lambda r: W.boulder_big(rock_cols, seed=r.rand(5)), 10, 60, 108, 56, 5, margin=1)

    z.start = (64 * 8 + 4, 50 * 8)
    z.grave = (40 * 8, 56 * 8)
    z.npc('grull_hawkwind', 58, 47)
    z.npc('chief_hawkwind', 68, 38, 1)
    z.npc('baine_bloodhoof', 70, 50)
    z.spawn('plainstrider', 82, 22, 34, 34, 10)
    z.spawn('battleboar', 12, 70, 40, 36, 10)
    z.spawn('bristleback_quilboar', 82, 86, 34, 26, 9)
    return z


ZONES = [
    ('northshire', northshire),
    ('coldridge', coldridge),
    ('shadowglen', shadowglen),
    ('valley_of_trials', valley_of_trials),
    ('deathknell', deathknell),
    ('narache', narache),
]
