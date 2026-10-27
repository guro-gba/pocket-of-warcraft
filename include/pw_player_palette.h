#ifndef PW_PLAYER_PALETTE_H
#define PW_PLAYER_PALETTE_H

#include "bn_color.h"

#include "pw_defs.h"
#include "pw_gen_data.h"

namespace pw
{

// Builds the 16 colors palette of a hero: race colors (skin, hair, eyes...) + class outfit colors.
inline void build_player_colors(int race, int class_index, bn::color* colors)
{
    const bn::color* rc = gen::race_colors[race];
    const bn::color* cc = gen::class_colors[class_index];
    colors[0] = bn::color(0, 0, 0);
    colors[1] = gen::outline_color;
    colors[2] = rc[0];
    colors[3] = rc[1];
    colors[4] = rc[2];
    colors[5] = rc[3];
    colors[6] = cc[0];
    colors[7] = cc[1];
    colors[8] = cc[2];
    colors[9] = cc[3];
    colors[10] = cc[4];
    colors[11] = rc[4];
    colors[12] = rc[5];
    colors[13] = rc[6];
    colors[14] = gen::metal_color;
    colors[15] = gen::white_color;
}

[[nodiscard]] inline int class_weapon(int class_index)
{
    switch(class_id(class_index))
    {

    case class_id::WARRIOR:
        return gen::WEAPON_SWORD;

    case class_id::PALADIN:
        return gen::WEAPON_HAMMER;

    case class_id::HUNTER:
        return gen::WEAPON_BOW;

    case class_id::ROGUE:
        return gen::WEAPON_DAGGER;

    case class_id::PRIEST:
        return gen::WEAPON_STAFF_PRIEST;

    case class_id::SHAMAN:
        return gen::WEAPON_MACE;

    case class_id::MAGE:
        return gen::WEAPON_STAFF_MAGE;

    case class_id::WARLOCK:
        return gen::WEAPON_STAFF_WARLOCK;

    default:
        return gen::WEAPON_STAFF_DRUID;
    }
}

}

#endif
