#ifndef PW_CLASSES_H
#define PW_CLASSES_H

#include "pw_defs.h"
#include "pw_gen_sprites.h"

namespace pw
{

enum class ability_kind : uint8_t
{
    MELEE,      // weapon strike on the target (power = % of weapon damage)
    BOLT,       // homing projectile
    HEAL,       // heal self (power = % of max health)
    SHIELD,     // absorb shield (power = % of max health)
    NOVA,       // damage (and root) every enemy around the hero
    DOT,        // damage over time on the target (power = total %)
    DRAIN,      // damage the target and heal self by the same amount
    INSTANT     // instant spell damage on the target
};

struct ability_def
{
    const char* name;
    ability_kind kind;
    int cost;
    int cooldown;       // frames
    int power;          // percent
    int range;          // pixels
    int fx;             // gen::fx_frame (-1: none)
    int extra;          // slow/root frames for frost spells
};

struct class_def
{
    resource_kind resource;
    int base_health;
    int health_per_level;
    ability_def abilities[3];   // A (auto attack), B, R
};

constexpr int melee_range = 26;

inline constexpr class_def classes[] = {
    // Warrior
    { resource_kind::RAGE, 62, 18, {
        { "Attack", ability_kind::MELEE, 0, 36, 100, melee_range, -1, 0 },
        { "Heroic Strike", ability_kind::MELEE, 15, 30, 220, melee_range, gen::FX_HIT, 0 },
        { "Thunder Clap", ability_kind::NOVA, 20, 300, 140, 44, -1, 60 } } },
    // Paladin
    { resource_kind::MANA, 58, 17, {
        { "Attack", ability_kind::MELEE, 0, 40, 100, melee_range, -1, 0 },
        { "Holy Light", ability_kind::HEAL, 30, 150, 45, 0, gen::FX_SPARKLE, 0 },
        { "Judgement", ability_kind::INSTANT, 25, 360, 200, 96, gen::FX_SMITE, 0 } } },
    // Hunter
    { resource_kind::MANA, 52, 15, {
        { "Auto Shot", ability_kind::BOLT, 0, 42, 100, 130, gen::FX_ARROW_H, 0 },
        { "Arcane Shot", ability_kind::BOLT, 20, 180, 220, 130, gen::FX_SMITE, 0 },
        { "Serpent Sting", ability_kind::DOT, 15, 240, 260, 130, gen::FX_WRATH, 0 } } },
    // Rogue
    { resource_kind::ENERGY, 54, 15, {
        { "Attack", ability_kind::MELEE, 0, 28, 85, melee_range, -1, 0 },
        { "Sinister Strike", ability_kind::MELEE, 40, 20, 200, melee_range, gen::FX_HIT, 0 },
        { "Eviscerate", ability_kind::MELEE, 60, 300, 380, melee_range, gen::FX_HIT2, 0 } } },
    // Priest
    { resource_kind::MANA, 46, 13, {
        { "Smite", ability_kind::BOLT, 0, 54, 115, 120, gen::FX_SMITE, 0 },
        { "Lesser Heal", ability_kind::HEAL, 25, 90, 40, 0, gen::FX_SPARKLE, 0 },
        { "Power Word: Shield", ability_kind::SHIELD, 30, 600, 40, 0, gen::FX_SHIELD, 0 } } },
    // Shaman
    { resource_kind::MANA, 56, 16, {
        { "Attack", ability_kind::MELEE, 0, 40, 100, melee_range, -1, 0 },
        { "Lightning Bolt", ability_kind::BOLT, 20, 90, 200, 120, gen::FX_LIGHTNING, 0 },
        { "Healing Wave", ability_kind::HEAL, 30, 120, 45, 0, gen::FX_HEAL, 0 } } },
    // Mage
    { resource_kind::MANA, 44, 13, {
        { "Fireball", ability_kind::BOLT, 0, 54, 125, 120, gen::FX_FIREBALL, 0 },
        { "Frostbolt", ability_kind::BOLT, 20, 100, 170, 120, gen::FX_FROSTBOLT, 180 },
        { "Frost Nova", ability_kind::NOVA, 30, 600, 60, 52, -1, 180 } } },
    // Warlock
    { resource_kind::MANA, 48, 14, {
        { "Shadow Bolt", ability_kind::BOLT, 0, 54, 125, 120, gen::FX_SHADOWBOLT, 0 },
        { "Corruption", ability_kind::DOT, 20, 120, 300, 120, gen::FX_SHADOWBOLT2, 0 },
        { "Drain Life", ability_kind::DRAIN, 25, 240, 150, 110, gen::FX_SHADOWBOLT, 0 } } },
    // Druid
    { resource_kind::MANA, 50, 15, {
        { "Wrath", ability_kind::BOLT, 0, 54, 115, 120, gen::FX_WRATH, 0 },
        { "Healing Touch", ability_kind::HEAL, 30, 120, 50, 0, gen::FX_HEAL, 0 },
        { "Moonfire", ability_kind::INSTANT, 20, 150, 170, 110, gen::FX_SMITE2, 0 } } },
};

}

#endif
