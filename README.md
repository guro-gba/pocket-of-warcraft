# Pocket of Warcraft

A single player Game Boy Advance demake of classic World of Warcraft, made with
[Butano](https://github.com/GValiente/butano).

It plays as a 3/4 top-down action RPG in the style of Shining Soul or Diablo.
Every graphic in the game is drawn by code in `tools/assets/`, so the repository has no image files.

## What's in it

- **Start screen** with the "Pocket of Warcraft" logo and the Alliance and Horde crests.
- **Character creation.** Pick one of the 8 classic races and one of the 9 classes, using the original race and
  class restrictions (no Gnome Paladins!). The preview shows your hero in their class colors, with a random
  race-appropriate name.
- **A playable starting zone for each race**, laid out like the originals:

| Race | Starting zone | Landmarks | Enemies | Quest givers |
| --- | --- | --- | --- | --- |
| Human | Northshire Valley | Northshire Abbey, Echo Ridge Mine, vineyards | Kobold Vermin & Workers, Young Wolves, Defias Thugs | Marshal McBride, Deputy Willem, Eagan Peltskinner |
| Dwarf, Gnome | Coldridge Valley | Anvilmar, Frostmane camp, Coldridge Pass | Ragged Young Wolves, Rockjaw Troggs, Frostmane Troll Whelps | Sten Stoutarm, Balir Frosthammer, Grelin Whitebeard |
| Night Elf | Shadowglen | Aldrassil, moonwell, Fel Rock | Young Nightsabers, Thistle Boars, Grellkin | Conservator Ilthalaine, Tenaron Stormgrip |
| Orc, Troll | Valley of Trials | The Den, Burning Blade Coven | Mottled Boars, Scorpid Workers, Vile Familiars | Gornek, Zureetha Fargaze |
| Undead | Deathknell | Chapel ruins, crypt, graveyard, Scarlet camp | Duskbats, Mindless Zombies, Rattlecage Skeletons, Scarlet Converts | Shadow Priest Sarvis, Executor Arren, Novice Elreth |
| Tauren | Camp Narache | Tents and totem, Brambleblade Ravine | Plainstriders, Battleboars, Bristleback Quilboars | Grull Hawkwind, Chief Hawkwind, Baine Bloodhoof |

- **WoW-style gameplay:**
  - Quest givers show a `!` when they have a quest, a grey `?` while it's in progress, and a yellow `?` when it's
    ready to turn in. There are 20 quests in total.
  - Mana, rage or energy depending on your class.
  - XP and levels, up to level 10.
  - Enemy names are colored by difficulty, from grey to red.
  - Floating combat text.
  - Area names appear as you explore.
  - Enemies chase you, give up if you lead them too far from home, and respawn later.
  - Healer NPCs restore your health and mana.
  - When you die, you come back as a ghost at the graveyard in a greyscale world. Run back to your corpse to
    resurrect.
- **Three abilities per class**, based on the classic low level kits:

| Class | A | B | R |
| --- | --- | --- | --- |
| Warrior | Attack | Heroic Strike | Thunder Clap |
| Paladin | Attack | Holy Light | Judgement |
| Hunter | Auto Shot | Arcane Shot | Serpent Sting |
| Rogue | Attack | Sinister Strike | Eviscerate |
| Priest | Smite | Lesser Heal | Power Word: Shield |
| Shaman | Attack | Lightning Bolt | Healing Wave |
| Mage | Fireball | Frostbolt (slows) | Frost Nova (roots) |
| Warlock | Shadow Bolt | Corruption | Drain Life |
| Druid | Wrath | Healing Touch | Moonfire |

## Controls

| Button | Title / character creation | In game |
| --- | --- | --- |
| D-Pad | Up/Down: race, Left/Right: class | Move |
| A | Start / enter world | Talk to an NPC, or auto attack (hold) |
| B | Back to title | Class ability 1 |
| R | | Class ability 2 |
| L | | Cycle target |
| Start | Start / enter world | Character & quest log |
| Select | New random name | |

## Building

You need Butano's usual requirements (devkitARM or Wonderful Toolchain, and Python 3).

```sh
git clone --recursive https://github.com/guro-gba/pocket-of-warcraft
cd pocket-of-warcraft
make -j8
```

This produces `pocket-of-warcraft.gba`, which you can play on mGBA or on real hardware.

- Butano is included as a git submodule in `butano/`.
- Before compiling, `tools/gen_assets.py` draws all the art and writes it as C++ headers into `build_gen/`.
  It reruns only when the generator sources change.
- Audio is disabled (`AUDIOBACKEND := null`), so maxmod's `mmutil` isn't needed.
- Every push builds the ROM on GitHub Actions. The `.gba` file is attached to each run as an artifact.

## Project layout

```
src/                  game code (title, character creation, world/combat/quests)
include/              shared definitions, class kits, palette helpers
tools/gen_assets.py   asset generator entry point
tools/assets/
  core.py             canvases, tile deduplication, C++ emitters
  font.py             hand made 8x8 pixel font
  characters.py       race heads + parametric bodies (class outfits are palette swaps)
  beasts.py           wolves, nightsabers, boars, plainstriders, scorpids, bats, imps, grells
  world.py            terrain textures and world objects (trees, abbey, Anvilmar, Aldrassil, tents...)
  zonebuilder.py      terrain transitions, object layering, collision, big map output
  zones.py            the six starting zone layouts, spawns, NPCs and areas
  gamedata.py         races, enemies, NPCs and quests
  ui.py               weapons, spell effects, HUD, crests, title and character select backgrounds
```

Each zone is 1024x1024 pixels and uses three big map layers: ground, a low object layer drawn below
sprites, and a high layer (tree canopies and roofs) drawn above sprites, so characters can walk behind things.
