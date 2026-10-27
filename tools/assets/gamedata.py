"""Game data: races, classes, enemies, NPCs and quests, emitted as constexpr C++ tables."""

import characters as C
import beasts as B
from core import emit_sprite_item, bn_color

RACES = [
    # id, name, horde, zone, classes, description lines
    ('human', 'Human', False, 'northshire', ['warrior', 'paladin', 'rogue', 'priest', 'mage', 'warlock'],
     ['Proud and resilient, the humans', 'of Stormwind lead the Alliance.']),
    ('dwarf', 'Dwarf', False, 'coldridge', ['warrior', 'paladin', 'hunter', 'rogue', 'priest'],
     ['Stout children of stone who', 'guard the halls of Ironforge.']),
    ('nightelf', 'Night Elf', False, 'shadowglen', ['warrior', 'hunter', 'rogue', 'priest', 'druid'],
     ['Ancient guardians of Teldrassil', 'who walk with the moon goddess.']),
    ('gnome', 'Gnome', False, 'coldridge', ['warrior', 'rogue', 'mage', 'warlock'],
     ['Brilliant tinkerers exiled from', 'their city of Gnomeregan.']),
    ('orc', 'Orc', True, 'valley_of_trials', ['warrior', 'hunter', 'rogue', 'shaman', 'warlock'],
     ['Freed from demonic corruption,', 'the orcs forge a new Horde.']),
    ('undead', 'Undead', True, 'deathknell', ['warrior', 'rogue', 'priest', 'mage', 'warlock'],
     ['The Forsaken: free of the Lich', 'King, bound to no one.']),
    ('tauren', 'Tauren', True, 'narache', ['warrior', 'hunter', 'shaman', 'druid'],
     ['Peaceful giants of Mulgore who', 'serve the Earth Mother.']),
    ('troll', 'Troll', True, 'valley_of_trials', ['warrior', 'hunter', 'rogue', 'priest', 'shaman', 'mage'],
     ['Darkspear trolls, sworn to', 'Thrall and his new Horde.']),
]

CLASSES = ['warrior', 'paladin', 'hunter', 'rogue', 'priest', 'shaman', 'mage', 'warlock', 'druid']

NAMES = {
    'human': ['Aldric', 'Bryanna', 'Cedric', 'Elena', 'Garret', 'Lysa', 'Rowan', 'Tobias'],
    'dwarf': ['Bromm', 'Dagna', 'Thorin', 'Muradin', 'Helga', 'Grimbar', 'Kurdran', 'Brenna'],
    'nightelf': ['Aerith', 'Shandris', 'Lunara', 'Taelan', 'Elune', 'Vaelis', 'Ilyara', 'Faelen'],
    'gnome': ['Fizzle', 'Tinka', 'Gizmo', 'Sprocket', 'Nixie', 'Wobble', 'Cogsy', 'Pip'],
    'orc': ['Grommash', 'Durga', 'Karg', 'Ragna', 'Throk', 'Zugra', 'Morg', 'Ugrok'],
    'undead': ['Mortis', 'Grimwald', 'Velisha', 'Ashra', 'Dreadus', 'Nyx', 'Corvin', 'Lilith'],
    'tauren': ['Hamuul', 'Tahna', 'Mahka', 'Orno', 'Kodo', 'Nahri', 'Tarvan', 'Sunwalk'],
    'troll': ['Zuljin', 'Senjin', 'Vanira', 'Rokhan', 'Zalazane', 'Jinxa', 'Volzu', 'Mazra'],
}

# Humanoid sheets: race -> robe? (robe variants are separate sheets).
HUMANOID_SHEETS = ['human', 'dwarf', 'nightelf', 'gnome', 'orc', 'undead', 'tauren', 'troll',
                   'kobold', 'trogg', 'skeleton', 'quilboar']
BEAST_SHEETS = ['wolf', 'nightsaber', 'boar', 'plainstrider', 'scorpid', 'bat', 'imp', 'grell']

# Outfits for NPCs / humanoid enemies: armor, armor dark, trim, legs, boots.
OUTFITS = {
    'guard': [(40, 70, 160), (26, 46, 110), (240, 200, 80), (130, 130, 150), (80, 80, 96)],
    'leather': [(130, 90, 54), (90, 60, 34), (180, 150, 100), (96, 80, 60), (64, 46, 30)],
    'robe_white': [(240, 240, 232), (180, 180, 190), (230, 196, 80), (220, 220, 214), (150, 140, 120)],
    'rags': [(120, 100, 70), (84, 70, 50), (100, 80, 56), (90, 76, 56), (60, 50, 36)],
    'defias': [(150, 40, 40), (96, 24, 24), (60, 50, 50), (70, 56, 50), (40, 32, 30)],
    'loincloth': [(120, 84, 50), (84, 58, 34), (150, 110, 70), (120, 84, 50), (84, 58, 34)],
    'fur': [(220, 220, 230), (170, 170, 186), (120, 90, 60), (110, 90, 70), (80, 60, 44)],
    'dwarf_iron': [(150, 150, 170), (100, 100, 120), (200, 160, 60), (110, 80, 50), (70, 50, 34)],
    'elf_sentinel': [(90, 60, 130), (60, 40, 90), (200, 200, 230), (70, 50, 100), (40, 30, 60)],
    'elf_druid': [(70, 120, 60), (44, 80, 40), (190, 160, 90), (100, 80, 60), (70, 50, 40)],
    'orc_armor': [(130, 60, 40), (86, 40, 26), (60, 50, 50), (90, 70, 50), (50, 40, 30)],
    'orc_warlock': [(110, 40, 120), (70, 24, 80), (200, 60, 40), (80, 30, 90), (40, 20, 50)],
    'forsaken': [(80, 70, 100), (50, 44, 66), (150, 130, 80), (60, 54, 70), (36, 32, 44)],
    'forsaken_priest': [(40, 36, 44), (24, 22, 28), (140, 50, 160), (40, 36, 44), (24, 22, 28)],
    'scarlet': [(230, 230, 224), (170, 170, 170), (190, 30, 40), (190, 30, 40), (90, 60, 40)],
    'zombie': [(100, 90, 70), (70, 62, 48), (80, 70, 54), (80, 70, 54), (50, 44, 36)],
    'tauren_brave': [(170, 120, 70), (120, 84, 46), (200, 60, 50), (140, 100, 60), (90, 64, 40)],
    'tauren_chief': [(200, 60, 50), (140, 40, 34), (240, 220, 160), (150, 110, 70), (90, 64, 40)],
    'kobold_worker': [(110, 90, 70), (80, 64, 50), (200, 170, 60), (90, 74, 56), (60, 50, 36)],
    'quilboar': [(110, 80, 50), (76, 54, 34), (200, 190, 150), (110, 80, 50), (76, 54, 34)],
    'bones': [(200, 194, 170), (140, 134, 112), (80, 76, 70), (200, 194, 170), (140, 134, 112)],
}

# Special race color sets for humanoid enemies (skin, skin dark, hair, hair dark, eyes, accent, accent dark).
SPECIAL_RACE_COLORS = {
    'defias': ('human', [(232, 180, 140), (190, 130, 96), (190, 30, 30), (130, 20, 20), (30, 30, 40), (232, 180, 140), (170, 110, 80)]),
    'frostmane': ('troll', [(170, 200, 220), (120, 150, 180), (240, 244, 250), (190, 200, 214), (90, 200, 255), (244, 238, 212), (180, 170, 140)]),
    'zombie': ('undead', [(130, 150, 100), (90, 104, 70), (70, 60, 50), (40, 34, 30), (255, 80, 40), (220, 214, 180), (150, 140, 110)]),
    'burly_trogg': ('trogg', [(120, 120, 140), (80, 80, 96), (70, 70, 80), (50, 50, 60), (255, 80, 40), (230, 220, 190), (120, 110, 90)]),
}

ENEMIES = [
    # id, name, sheet, colors-source, beast?, min lvl, max lvl, aggro radius, speed (1/16 px), flying
    ('kobold_vermin', 'Kobold Vermin', 'kobold', ('kobold', 'rags'), False, 1, 2, 40, 10, False),
    ('kobold_worker', 'Kobold Worker', 'kobold', ('kobold', 'kobold_worker'), False, 2, 3, 48, 10, False),
    ('young_wolf', 'Young Wolf', 'wolf', 'young_wolf', True, 1, 2, 48, 14, False),
    ('defias_thug', 'Defias Thug', 'human', ('defias', 'defias'), False, 3, 5, 56, 12, False),
    ('ragged_young_wolf', 'Ragged Young Wolf', 'wolf', 'ragged_wolf', True, 1, 2, 48, 14, False),
    ('rockjaw_trogg', 'Rockjaw Trogg', 'trogg', ('trogg', 'loincloth'), False, 2, 3, 48, 10, False),
    ('burly_rockjaw_trogg', 'Burly Rockjaw Trogg', 'trogg', ('burly_trogg', 'loincloth'), False, 4, 5, 56, 10, False),
    ('frostmane_whelp', 'Frostmane Troll Whelp', 'troll', ('frostmane', 'fur'), False, 3, 5, 56, 12, False),
    ('young_nightsaber', 'Young Nightsaber', 'nightsaber', 'nightsaber', True, 1, 2, 48, 15, False),
    ('young_thistle_boar', 'Young Thistle Boar', 'boar', 'thistle_boar', True, 2, 3, 40, 12, False),
    ('grellkin', 'Grellkin', 'grell', 'grellkin', True, 3, 5, 56, 11, False),
    ('mottled_boar', 'Mottled Boar', 'boar', 'mottled_boar', True, 1, 2, 40, 12, False),
    ('scorpid_worker', 'Scorpid Worker', 'scorpid', 'scorpid', True, 2, 3, 44, 10, False),
    ('vile_familiar', 'Vile Familiar', 'imp', 'vile_familiar', True, 3, 5, 56, 12, False),
    ('duskbat', 'Duskbat', 'bat', 'duskbat', True, 1, 2, 48, 14, True),
    ('mindless_zombie', 'Mindless Zombie', 'undead', ('zombie', 'zombie'), False, 1, 3, 40, 8, False),
    ('rattlecage_skeleton', 'Rattlecage Skeleton', 'skeleton', ('skeleton', 'bones'), False, 2, 4, 48, 11, False),
    ('scarlet_convert', 'Scarlet Convert', 'human', ('human', 'scarlet'), False, 4, 5, 56, 12, False),
    ('plainstrider', 'Plainstrider', 'plainstrider', 'plainstrider', True, 1, 2, 0, 14, False),
    ('battleboar', 'Battleboar', 'boar', 'battleboar', True, 2, 3, 44, 12, False),
    ('bristleback_quilboar', 'Bristleback Quilboar', 'quilboar', ('quilboar', 'quilboar'), False, 3, 5, 56, 11, False),
]

NPCS = [
    # id, name, title, sheet, race colors, outfit, greeting, heals
    ('marshal_mcbride', 'Marshal McBride', 'Northshire Guard', 'human', 'human', 'guard',
     'The Light guide you, recruit.', False),
    ('deputy_willem', 'Deputy Willem', 'Northshire Guard', 'human', 'human', 'guard',
     'Keep your blade sharp out there.', False),
    ('eagan_peltskinner', 'Eagan Peltskinner', 'Skinner', 'human', 'human', 'leather',
     'Those wolves are getting bold.', False),
    ('brother_paxton', 'Brother Paxton', 'Priest', 'human', 'human', 'robe_white',
     'Be healed, friend. The Light is with you.', True),
    ('sten_stoutarm', 'Sten Stoutarm', 'Coldridge Guard', 'dwarf', 'dwarf', 'dwarf_iron',
     'Cold enough fer ya?', False),
    ('balir_frosthammer', 'Balir Frosthammer', 'Mountaineer', 'dwarf', 'dwarf', 'dwarf_iron',
     'Troggs! Pourin out of the ground!', False),
    ('grelin_whitebeard', 'Grelin Whitebeard', 'Explorer', 'dwarf', 'dwarf', 'leather',
     'Have a sip by the fire, lad. Ye look worn.', True),
    ('conservator_ilthalaine', 'Conservator Ilthalaine', 'Conservator', 'nightelf', 'nightelf', 'elf_druid',
     'Ishnu-alah. The balance must be kept.', False),
    ('tenaron_stormgrip', 'Tenaron Stormgrip', 'Sentinel', 'nightelf', 'nightelf', 'elf_sentinel',
     'Something foul festers at Fel Rock.', False),
    ('melithar_staghelm', 'Melithar Staghelm', 'Druid of the Grove', 'nightelf', 'nightelf', 'elf_druid',
     'Elune restores you, young one.', True),
    ('gornek', 'Gornek', 'Den Master', 'orc', 'orc', 'orc_armor', 'Lok\'tar! Prove your strength.', False),
    ('zureetha_fargaze', 'Zureetha Fargaze', 'Warlock', 'orc', 'orc', 'orc_warlock',
     'The Burning Blade meddles in fel magic.', False),
    ('galgar', 'Galgar', 'Cook', 'orc', 'orc', 'leather', 'Eat! Cactus apple surprise!', True),
    ('shadow_priest_sarvis', 'Shadow Priest Sarvis', 'Priest', 'undead', 'undead', 'forsaken_priest',
     'Rise, Forsaken. The Dark Lady calls.', False),
    ('executor_arren', 'Executor Arren', 'Executor', 'undead', 'undead', 'forsaken',
     'The Scarlet fanatics crawl nearby.', False),
    ('novice_elreth', 'Novice Elreth', 'Novice', 'undead', 'undead', 'forsaken',
     'Death is only the beginning... and you look poorly.', True),
    ('grull_hawkwind', 'Grull Hawkwind', 'Hunter', 'tauren', 'tauren', 'tauren_brave',
     'The plains provide for the patient hunter.', False),
    ('chief_hawkwind', 'Chief Hawkwind', 'Chieftain', 'tauren', 'tauren', 'tauren_chief',
     'Welcome to Camp Narache, young one.', False),
    ('baine_bloodhoof', 'Baine Bloodhoof', 'Heir of the Bloodhoof', 'tauren', 'tauren', 'tauren_brave',
     'Walk with the Earth Mother.', True),
]

QUESTS = [
    # id, title, giver, enemy, count, xp, prereq, text, complete text
    ('wolves', 'Wolves Across the Border', 'eagan_peltskinner', 'young_wolf', 8, 140, None,
     'Young wolves prowl the woods south-west of the Abbey. Thin their numbers.',
     'Good work. The flock is safer now.'),
    ('kobold_cleanup', 'Kobold Camp Cleanup', 'deputy_willem', 'kobold_vermin', 10, 160, None,
     'Kobolds infest the hills near Echo Ridge Mine. Drive out the vermin!',
     'The vermin are scattered. Well done.'),
    ('echo_ridge', 'Investigate Echo Ridge', 'marshal_mcbride', 'kobold_worker', 10, 260, 'kobold_cleanup',
     'Kobold workers dig deeper in Echo Ridge. Stop them before they find more.',
     'You have done Northshire proud.'),
    ('defias', 'Brotherhood of Thieves', 'deputy_willem', 'defias_thug', 10, 380, 'kobold_cleanup',
     'Defias thugs raid the vineyards to the east. Bring them to justice.',
     'Stormwind thanks you, hero.'),
    ('outfitters', 'Dwarven Outfitters', 'sten_stoutarm', 'ragged_young_wolf', 8, 140, None,
     'We need pelts! Hunt the ragged wolves east of the trail.',
     'Fine pelts! These will keep us warm.'),
    ('new_threat', 'A New Threat', 'balir_frosthammer', 'rockjaw_trogg', 10, 180, None,
     'Rockjaw troggs swarm from Coldridge Pass to the south-west. Beat them back!',
     'Hah! Ye fight like a true mountaineer.'),
    ('burly', 'Burly Brutes', 'balir_frosthammer', 'burly_rockjaw_trogg', 6, 300, 'new_threat',
     'The big troggs lead the swarm. Smash the Burly Rockjaws!',
     'That will teach them to dig here.'),
    ('troll_cave', 'The Troll Cave', 'grelin_whitebeard', 'frostmane_whelp', 10, 320, None,
     'Frostmane trolls camp to the west. Clear out the whelps.',
     'The camp is quiet now. Good job, lad.'),
    ('balance1', 'The Balance of Nature', 'conservator_ilthalaine', 'young_nightsaber', 7, 140, None,
     'The nightsabers have grown too many. Restore the balance in the woods west.',
     'The balance is restored... for now.'),
    ('balance2', 'The Balance of Nature', 'conservator_ilthalaine', 'young_thistle_boar', 7, 200, 'balance1',
     'Now the thistle boars of the south must be culled as well.',
     'Shadowglen breathes easier. Thank you.'),
    ('fel_moss', 'Fel Moss Corruption', 'tenaron_stormgrip', 'grellkin', 10, 320, None,
     'Grellkin carry fel moss from Fel Rock to the east. Destroy them.',
     'The corruption is contained. Elune be praised.'),
    ('cutting_teeth', 'Cutting Teeth', 'gornek', 'mottled_boar', 10, 140, None,
     'Mottled boars roam to the west. Kill them and show your strength.',
     'Good. You have the makings of a warrior.'),
    ('scorpid', 'Sting of the Scorpid', 'gornek', 'scorpid_worker', 10, 200, 'cutting_teeth',
     'Scorpids nest in the south-east hollow. Bring me their stingers.',
     'Their poison will serve the Horde.'),
    ('vile_familiars', 'Vile Familiars', 'zureetha_fargaze', 'vile_familiar', 12, 320, None,
     'The Burning Blade summons imps in the cave to the east. Banish them.',
     'The demons are gone. For now.'),
    ('mindless', 'The Mindless Ones', 'shadow_priest_sarvis', 'mindless_zombie', 10, 160, None,
     'Mindless zombies shamble in the west. Put them to rest.',
     'They will serve the Dark Lady in death.'),
    ('rattlecages', 'Rattling the Rattlecages', 'novice_elreth', 'rattlecage_skeleton', 8, 200, None,
     'Rattlecage skeletons haunt the graveyard edge. Shatter them.',
     'Fewer bones to sweep up. Thank you.'),
    ('scarlet', 'The Scarlet Crusade', 'executor_arren', 'scarlet_convert', 10, 380, 'mindless',
     'Scarlet zealots camp to the south. Show them the Forsaken do not fear.',
     'Their camp burns. Well done.'),
    ('hunt_begins', 'The Hunt Begins', 'grull_hawkwind', 'plainstrider', 7, 140, None,
     'Hunt the plainstriders on the plains to the north-east.',
     'You honor the hunt.'),
    ('battleboar', 'The Battleboar', 'chief_hawkwind', 'battleboar', 8, 200, None,
     'Battleboars trample the southern fields. Drive them off.',
     'The fields are safe once more.'),
    ('rite', 'Rite of Strength', 'baine_bloodhoof', 'bristleback_quilboar', 10, 380, None,
     'The Bristleback quilboars camp in the south-east ravine. Defeat them.',
     'Your strength is proven, young brave.'),
]

ZONE_ORDER = ['northshire', 'coldridge', 'shadowglen', 'valley_of_trials', 'deathknell', 'narache']


def cstr(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def race_colors(key):
    if key in SPECIAL_RACE_COLORS:
        return SPECIAL_RACE_COLORS[key][1]
    return C.RACE_COLORS[key]


def full_palette(race_key, outfit):
    rc = race_colors(race_key)
    a, ad, t, l, bo = outfit
    return [(0, 0, 0), C.OUTLINE] + list(rc[:4]) + [a, ad, t, l, bo, rc[4], rc[5], rc[6], C.METAL, C.WHITE]


def emit_colors(name, pal):
    return 'inline constexpr bn::color %s[16] = {%s};\n' % (name, ', '.join(bn_color(c) for c in pal))


def generate_sprites():
    out = ''
    for race in HUMANOID_SHEETS:
        frames = C.humanoid_sheet(race)
        out += emit_sprite_item('sheet_%s' % race, frames, C.palette(race, C.CLASS_COLORS['warrior']))
        if race in ('human', 'dwarf', 'nightelf', 'gnome', 'orc', 'undead', 'tauren', 'troll'):
            frames = C.humanoid_sheet(race, robe=True)
            out += emit_sprite_item('sheet_%s_robe' % race, frames, C.palette(race, C.CLASS_COLORS['priest']))
    for kind in BEAST_SHEETS:
        pal = None
        for name, (k, p) in B.BEAST_PALETTES.items():
            if k == kind:
                pal = p
                break
        out += emit_sprite_item('sheet_%s' % kind, B.beast_sheet(kind), pal)
    return out


def generate_tables():
    out = ''
    # Race colors (7 each) and class outfits (5 each) so the game composes player palettes at runtime.
    out += 'inline constexpr bn::color race_colors[%d][7] = {\n' % len(RACES)
    for r in RACES:
        out += '    {%s},\n' % ', '.join(bn_color(c) for c in C.RACE_COLORS[r[0]])
    out += '};\n\n'
    out += 'inline constexpr bn::color class_colors[%d][5] = {\n' % len(CLASSES)
    for cl in CLASSES:
        out += '    {%s},\n' % ', '.join(bn_color(c) for c in C.CLASS_COLORS[cl])
    out += '};\n\n'
    out += 'inline constexpr bn::color outline_color = %s;\n' % bn_color(C.OUTLINE)
    out += 'inline constexpr bn::color metal_color = %s;\n' % bn_color(C.METAL)
    out += 'inline constexpr bn::color white_color = %s;\n\n' % bn_color(C.WHITE)

    # Races.
    out += 'inline constexpr const char* race_names_list[%d][8] = {\n' % len(RACES)
    for r in RACES:
        out += '    {%s},\n' % ', '.join(cstr(n) for n in NAMES[r[0]])
    out += '};\n\n'
    out += 'inline constexpr pw::race_def races[] = {\n'
    for r in RACES:
        rid, name, horde, zone, classes, desc = r
        mask = sum(1 << CLASSES.index(c) for c in classes)
        zone_names = {'northshire': 'Northshire Valley', 'coldridge': 'Coldridge Valley', 'shadowglen': 'Shadowglen',
                      'valley_of_trials': 'Valley of Trials', 'deathknell': 'Deathknell', 'narache': 'Camp Narache'}
        out += '    pw::race_def{%s, %s, %s, %s, &sheet_%s, &sheet_%s_robe, %d, %d, %s, %s},\n' % (
            cstr(name), 'true' if horde else 'false', cstr('Horde' if horde else 'Alliance'), cstr(zone_names[zone]),
            rid, rid, ZONE_ORDER.index(zone), mask, cstr(desc[0]), cstr(desc[1]))
    out += '};\n\n'

    # Enemies.
    beast_pal_names = {}
    for e in ENEMIES:
        eid, name, sheet, colors, beast = e[:5]
        if beast:
            pal = B.BEAST_PALETTES[colors][1]
        else:
            race_key, outfit = colors
            pal = full_palette(race_key, OUTFITS[outfit])
        out += emit_colors('enemy_%s_colors' % eid, pal)
        out += 'inline constexpr bn::sprite_palette_item enemy_%s_palette(bn::span<const bn::color>(enemy_%s_colors), ' \
               'bn::bpp_mode::BPP_4);\n' % (eid, eid)
    out += '\nenum enemy_id : uint8_t\n{\n'
    for e in ENEMIES:
        out += '    ENEMY_%s,\n' % e[0].upper()
    out += '    ENEMY_COUNT\n};\n\n'
    out += 'inline constexpr pw::enemy_def enemies[] = {\n'
    for e in ENEMIES:
        eid, name, sheet, colors, beast, lo, hi, aggro, speed, flying = e
        out += '    pw::enemy_def{%s, &sheet_%s, &enemy_%s_palette, %s, %d, %d, %d, %d, %s},\n' % (
            cstr(name), sheet, eid, 'true' if beast else 'false', lo, hi, aggro, speed, 'true' if flying else 'false')
    out += '};\n\n'

    # NPCs.
    for n in NPCS:
        nid, name, title, sheet, race_key, outfit, greet, heals = n
        out += emit_colors('npc_%s_colors' % nid, full_palette(race_key, OUTFITS[outfit]))
        out += 'inline constexpr bn::sprite_palette_item npc_%s_palette(bn::span<const bn::color>(npc_%s_colors), ' \
               'bn::bpp_mode::BPP_4);\n' % (nid, nid)
    out += '\nenum npc_id : uint8_t\n{\n'
    for n in NPCS:
        out += '    NPC_%s,\n' % n[0].upper()
    out += '    NPC_COUNT\n};\n\n'
    out += 'inline constexpr pw::npc_def npcs[] = {\n'
    for n in NPCS:
        nid, name, title, sheet, race_key, outfit, greet, heals = n
        robe = outfit in ('robe_white', 'forsaken_priest', 'orc_warlock')
        out += '    pw::npc_def{%s, %s, &sheet_%s%s, &npc_%s_palette, %s, %s},\n' % (
            cstr(name), cstr(title), sheet, '_robe' if robe else '', nid, cstr(greet), 'true' if heals else 'false')
    out += '};\n\n'

    # Quests.
    qids = [q[0] for q in QUESTS]
    nids = [n[0] for n in NPCS]
    eids = [e[0] for e in ENEMIES]
    out += 'inline constexpr pw::quest_def quests[] = {\n'
    for q in QUESTS:
        qid, title, giver, enemy, count, xp, prereq, text, done = q
        out += '    pw::quest_def{%s, %s, %s, %d, %d, %d, %d, %d},\n' % (
            cstr(title), cstr(text), cstr(done), nids.index(giver), eids.index(enemy), count, xp,
            qids.index(prereq) if prereq else -1)
    out += '};\n\n'
    out += 'inline constexpr int quests_count = %d;\n\n' % len(QUESTS)
    return out


def enemy_index(eid):
    return [e[0] for e in ENEMIES].index(eid)


def npc_index(nid):
    return [n[0] for n in NPCS].index(nid)
