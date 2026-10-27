#ifndef PW_DEFS_H
#define PW_DEFS_H

#include "bn_span.h"
#include "bn_sprite_item.h"
#include "bn_sprite_palette_item.h"
#include "bn_regular_bg_item.h"

// Plain data types filled by the generated tables (build_gen/pw_gen_*.h).
namespace pw
{

struct race_def
{
    const char* name;
    bool horde;
    const char* faction;
    const char* zone_name;
    const bn::sprite_item* sheet;
    const bn::sprite_item* robe_sheet;
    int zone;
    int classes_mask;
    const char* description_1;
    const char* description_2;
};

struct enemy_def
{
    const char* name;
    const bn::sprite_item* sheet;
    const bn::sprite_palette_item* palette;
    bool beast;
    int min_level;
    int max_level;
    int aggro_radius;
    int speed;          // 1/16 pixels per frame
    bool flying;
};

struct npc_def
{
    const char* name;
    const char* title;
    const bn::sprite_item* sheet;
    const bn::sprite_palette_item* palette;
    const char* greeting;
    bool heals;
};

struct quest_def
{
    const char* title;
    const char* text;
    const char* complete_text;
    int giver;
    int enemy;
    int count;
    int xp;
    int prereq;
};

struct spawn_def
{
    int enemy;
    int x;
    int y;
};

struct npc_place
{
    int npc;
    int x;
    int y;
    int direction;
};

struct area_def
{
    const char* name;
    int x;
    int y;
    int width;
    int height;
};

struct zone_def
{
    const char* name;
    const bn::regular_bg_item* ground;
    const bn::regular_bg_item* low;
    const bn::regular_bg_item* high;
    const uint8_t* collision;
    int width_cells;
    int height_cells;
    bn::span<const spawn_def> spawns;
    bn::span<const npc_place> npcs;
    bn::span<const area_def> areas;
    int start_x;
    int start_y;
    int grave_x;
    int grave_y;
};

enum class class_id : uint8_t
{
    WARRIOR,
    PALADIN,
    HUNTER,
    ROGUE,
    PRIEST,
    SHAMAN,
    MAGE,
    WARLOCK,
    DRUID,
    COUNT
};

enum class resource_kind : uint8_t
{
    MANA,
    RAGE,
    ENERGY
};

}

#endif
