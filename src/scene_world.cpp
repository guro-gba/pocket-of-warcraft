#include "bn_camera_ptr.h"
#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_sprite_tiles_ptr.h"
#include "bn_optional.h"
#include "bn_random.h"
#include "bn_math.h"
#include "bn_blending.h"
#include "bn_string.h"

#include "pw_common.h"
#include "pw_classes.h"
#include "pw_player_palette.h"
#include "pw_gen_bgs.h"
#include "pw_gen_data.h"
#include "pw_gen_zones.h"

namespace pw
{

namespace
{

constexpr int max_level = 10;
constexpr int dir_down = 0;
constexpr int dir_up = 1;
constexpr int dir_left = 2;
constexpr int dir_right = 3;

[[nodiscard]] int xp_to_next(int level)
{
    return 80 + level * 60;
}

[[nodiscard]] int sheet_dir(int dir)
{
    return dir == dir_down ? 0 : (dir == dir_up ? 1 : 2);
}

[[nodiscard]] int dist2(bn::fixed ax, bn::fixed ay, bn::fixed bx, bn::fixed by)
{
    int dx = (ax - bx).integer();
    int dy = (ay - by).integer();
    return dx * dx + dy * dy;
}

[[nodiscard]] int dir_towards(bn::fixed fx, bn::fixed fy, bn::fixed tx, bn::fixed ty)
{
    bn::fixed dx = tx - fx;
    bn::fixed dy = ty - fy;

    if(bn::abs(dx) > bn::abs(dy))
    {
        return dx < 0 ? dir_left : dir_right;
    }

    return dy < 0 ? dir_up : dir_down;
}

[[nodiscard]] bn::sprite_ptr make_sprite(const bn::sprite_item& item, int frame, const bn::sprite_palette_item& palette)
{
    return bn::sprite_ptr::create(0, 0, item.shape_size(), item.tiles_item().create_tiles(frame),
                                  palette.create_palette());
}

enum class enemy_state : uint8_t
{
    IDLE,
    CHASE,
    RETURN,
    DEAD
};

struct enemy
{
    int def = 0;
    int level = 1;
    bn::fixed x;
    bn::fixed y;
    bn::fixed home_x;
    bn::fixed home_y;
    bn::fixed wander_x;
    bn::fixed wander_y;
    int hp = 1;
    int max_hp = 1;
    enemy_state state = enemy_state::IDLE;
    int timer = 0;
    int attack_cooldown = 0;
    int attack_anim = 0;
    int respawn = 0;
    int dir = dir_right;
    int anim = 0;
    int hurt = 0;
    int dot_timer = 0;
    int dot_ticks = 0;
    int dot_damage = 0;
    int slow = 0;
    int root = 0;
    bn::optional<bn::sprite_ptr> sprite;
};

struct npc
{
    int def = 0;
    bn::fixed x;
    bn::fixed y;
    int dir = dir_down;
    bn::optional<bn::sprite_ptr> sprite;
    bn::optional<bn::sprite_ptr> mark;
};

struct projectile
{
    bn::fixed x;
    bn::fixed y;
    int target = 0;
    int fx = 0;
    int damage = 0;
    int slow = 0;
    int life = 0;
    bn::sprite_ptr sprite;
};

struct effect
{
    bn::sprite_ptr sprite;
    int first_frame = 0;
    int frames = 1;
    int period = 4;
    int timer = 0;
    int life = 0;
    int follow = -2;    // -2: none, -1: hero, >= 0: enemy index
    bool big = false;
};

struct float_text
{
    bn::vector<bn::sprite_ptr, 4> sprites;
    int timer = 0;
};

struct bar
{
    bn::vector<bn::sprite_ptr, 10> segments;
    int kind = 0;
    int last_fill = -1;
};

enum class dialog_mode : uint8_t
{
    NONE,
    TALK,
    OFFER,
    TURN_IN,
    LOG
};

class world
{

public:
    world(const profile& hero) :
        _hero(hero),
        _race(gen::races[hero.race]),
        _class(classes[hero.class_index]),
        _zone(*gen::zones[gen::races[hero.race].zone]),
        _camera(bn::camera_ptr::create(0, 0)),
        _ground(_zone.ground->create_bg(_zone.width_cells * 4, _zone.height_cells * 4)),
        _low(_zone.low->create_bg(_zone.width_cells * 4, _zone.height_cells * 4)),
        _high(_zone.high->create_bg(_zone.width_cells * 4, _zone.height_cells * 4)),
        _panel(gen::bg_panel_item.create_bg(8, 48)),
        _sheet(class_wears_robe(hero.class_index) ? *_race.robe_sheet : *_race.sheet),
        _body(_sheet.create_sprite(0, 0, 0)),
        _weapon(gen::weapons.create_sprite(0, 0, class_weapon(hero.class_index))),
        _text(gen::sprite_font)
    {
        _ground.set_priority(3);
        _low.set_priority(2);
        _high.set_priority(1);
        _panel.set_priority(0);
        _panel.set_visible(false);
        _ground.set_camera(_camera);
        _low.set_camera(_camera);
        _high.set_camera(_camera);

        bn::color colors[16];
        build_player_colors(hero.race, hero.class_index, colors);
        _palette = bn::sprite_palette_ptr::create_new(_sheet.palette_item());
        _palette->set_colors(colors);
        _body.set_palette(*_palette);
        _body.set_camera(_camera);
        _body.set_bg_priority(2);
        _weapon.set_camera(_camera);
        _weapon.set_bg_priority(2);
        _weapon.set_rotation_angle(0);

        _x = _zone.start_x;
        _y = _zone.start_y;
        _level = 1;
        _recalc_stats();
        _hp = _max_hp;
        _res = _class.resource == resource_kind::MANA ? _max_res :
               _class.resource == resource_kind::ENERGY ? 100 : 0;

        for(int i = 0; i < 256; ++i)
        {
            _random.update();
        }

        for(const spawn_def& spawn : _zone.spawns)
        {
            enemy e;
            e.def = spawn.enemy;
            e.home_x = spawn.x;
            e.home_y = spawn.y;
            _spawn_enemy(e);
            _enemies.push_back(bn::move(e));
        }

        for(const npc_place& place : _zone.npcs)
        {
            npc n;
            n.def = place.npc;
            n.x = place.x;
            n.y = place.y;
            n.dir = place.direction == 1 ? dir_left : dir_down;
            _npcs.push_back(bn::move(n));
        }

        _text.set_bg_priority(0);
        _create_bar(_hp_bar, gen::BAR_HP, 6, -112 + 4, -60);

        int res_kind = _class.resource == resource_kind::MANA ? gen::BAR_MANA :
                       _class.resource == resource_kind::RAGE ? gen::BAR_RAGE : gen::BAR_ENERGY;
        _create_bar(_res_bar, res_kind, 6, -112 + 4, -52);
        _create_bar(_xp_bar, gen::BAR_XP, 10, -36, 74);
        _update_camera();
        _refresh_hero_label();
        _refresh_tracker();
        _show_banner(_zone.name);
    }

    void run()
    {
        fade(false);

        while(true)
        {
            ++_frame;

            if(_dialog != dialog_mode::NONE)
            {
                _update_dialog();
            }
            else
            {
                _update_hero();
                _update_enemies();
                _update_projectiles();
                _check_area();
            }

            _update_effects();
            _update_floats();
            _update_npcs();
            _update_hud();
            _update_camera();
            _random.update();
            bn::core::update();
        }
    }

private:
    const profile& _hero;
    const race_def& _race;
    const class_def& _class;
    const zone_def& _zone;
    bn::camera_ptr _camera;
    bn::regular_bg_ptr _ground;
    bn::regular_bg_ptr _low;
    bn::regular_bg_ptr _high;
    bn::regular_bg_ptr _panel;
    const bn::sprite_item& _sheet;
    bn::sprite_ptr _body;
    bn::sprite_ptr _weapon;
    bn::optional<bn::sprite_palette_ptr> _palette;
    bn::sprite_text_generator _text;
    bn::random _random;

    bn::vector<enemy, 64> _enemies;
    bn::vector<npc, 6> _npcs;
    bn::vector<projectile, 12> _projectiles;
    bn::vector<effect, 10> _effects;
    bn::vector<float_text, 6> _floats;

    // Hero state.
    bn::fixed _x;
    bn::fixed _y;
    int _dir = dir_down;
    int _walk = 0;
    bool _moving = false;
    int _level = 1;
    int _xp = 0;
    int _hp = 1;
    int _max_hp = 1;
    int _res = 0;
    int _max_res = 100;
    int _shield = 0;
    int _cooldowns[3] = {};
    int _attack_anim = 0;
    int _combat_timer = 0;
    int _regen_timer = 0;
    int _target = -1;
    bool _ghost = false;
    bn::fixed _corpse_x;
    bn::fixed _corpse_y;
    bn::optional<bn::sprite_ptr> _corpse;
    int _frame = 0;

    // Quests.
    uint8_t _quest_state[gen::quests_count] = {};
    uint8_t _quest_progress[gen::quests_count] = {};

    // HUD.
    bar _hp_bar;
    bar _res_bar;
    bar _xp_bar;
    bar _target_bar;
    bn::vector<bn::sprite_ptr, 10> _hero_label;
    bn::vector<bn::sprite_ptr, 10> _target_label;
    bn::vector<bn::sprite_ptr, 24> _tracker;
    bn::vector<bn::sprite_ptr, 10> _banner;
    bn::vector<bn::sprite_ptr, 10> _message;
    bn::optional<bn::sprite_ptr> _target_ring;
    int _banner_timer = 0;
    int _message_timer = 0;
    int _shown_target = -2;
    int _shown_target_level = -1;
    int _area = -1;

    // Dialog.
    dialog_mode _dialog = dialog_mode::NONE;
    int _dialog_quest = -1;
    int _dialog_npc = -1;
    bn::vector<bn::sprite_ptr, 48> _dialog_text;

    // -----------------------------------------------------------------------------------------------------------------
    // Stats.
    // -----------------------------------------------------------------------------------------------------------------

    void _recalc_stats()
    {
        _max_hp = _class.base_health + (_level - 1) * _class.health_per_level;
        _max_res = _class.resource == resource_kind::MANA ? 80 + _level * 20 : 100;
    }

    [[nodiscard]] int _weapon_damage()
    {
        int base = 4 + _level * 2;
        return base - base / 4 + _random.get_int(base / 2 + 1);
    }

    [[nodiscard]] int _enemy_max_hp(int level) const
    {
        return 24 + (level - 1) * 16;
    }

    [[nodiscard]] int _enemy_damage(int level)
    {
        int base = 1 + level;
        return base + _random.get_int(base / 2 + 1);
    }

    [[nodiscard]] int _kill_xp(int level) const
    {
        int diff = _level - level;

        if(diff >= 5)
        {
            return 0;
        }

        int xp = 18 + level * 9;

        if(diff > 0)
        {
            xp = xp * (5 - diff) / 5;
        }
        else if(diff < 0)
        {
            xp += xp * (-diff) / 5;
        }

        return xp;
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Collision.
    // -----------------------------------------------------------------------------------------------------------------

    [[nodiscard]] bool _solid(int x, int y) const
    {
        if(x < 0 || y < 0 || x >= _zone.width_cells * 8 || y >= _zone.height_cells * 8)
        {
            return true;
        }

        return _zone.collision[(y >> 3) * _zone.width_cells + (x >> 3)];
    }

    [[nodiscard]] bool _blocked(bn::fixed fx, bn::fixed fy) const
    {
        int x = fx.integer();
        int y = fy.integer();
        return _solid(x - 4, y) || _solid(x + 3, y) || _solid(x - 4, y - 3) || _solid(x + 3, y - 3);
    }

    void _move(bn::fixed& x, bn::fixed& y, bn::fixed dx, bn::fixed dy, bool flying)
    {
        if(flying)
        {
            x += dx;
            y += dy;
            x = bn::clamp(x, bn::fixed(16), bn::fixed(_zone.width_cells * 8 - 16));
            y = bn::clamp(y, bn::fixed(16), bn::fixed(_zone.height_cells * 8 - 16));
            return;
        }

        if(dx != 0 && ! _blocked(x + dx, y))
        {
            x += dx;
        }

        if(dy != 0 && ! _blocked(x, y + dy))
        {
            y += dy;
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Hero.
    // -----------------------------------------------------------------------------------------------------------------

    void _update_hero()
    {
        for(int& cooldown : _cooldowns)
        {
            if(cooldown > 0)
            {
                --cooldown;
            }
        }

        if(_combat_timer > 0)
        {
            --_combat_timer;
        }

        // Movement.
        bn::fixed dx;
        bn::fixed dy;
        bn::fixed speed = _ghost ? bn::fixed(1.6) : bn::fixed(1.25);

        if(bn::keypad::left_held())
        {
            dx = -speed;
            _dir = dir_left;
        }
        else if(bn::keypad::right_held())
        {
            dx = speed;
            _dir = dir_right;
        }

        if(bn::keypad::up_held())
        {
            dy = -speed;

            if(dx == 0)
            {
                _dir = dir_up;
            }
        }
        else if(bn::keypad::down_held())
        {
            dy = speed;

            if(dx == 0)
            {
                _dir = dir_down;
            }
        }

        if(dx != 0 && dy != 0)
        {
            dx *= bn::fixed(0.72);
            dy *= bn::fixed(0.72);
        }

        _moving = dx != 0 || dy != 0;

        if(_moving)
        {
            _move(_x, _y, dx, dy, false);
            ++_walk;
        }
        else
        {
            _walk = 0;
        }

        if(_ghost)
        {
            if(dist2(_x, _y, _corpse_x, _corpse_y) < 20 * 20)
            {
                _resurrect();
            }

            if(bn::keypad::a_pressed() || bn::keypad::b_pressed())
            {
                _show_message("Return to your corpse to resurrect");
            }
        }
        else
        {
            _update_target();

            if(bn::keypad::a_pressed() && _talk_to_npc())
            {
                return;
            }

            if(bn::keypad::a_held())
            {
                _use_ability(0);
            }

            if(bn::keypad::b_pressed())
            {
                _use_ability(1);
            }

            if(bn::keypad::r_pressed())
            {
                _use_ability(2);
            }

            if(bn::keypad::start_pressed())
            {
                _open_log();
            }

            _regenerate();
        }

        if(_attack_anim > 0)
        {
            --_attack_anim;
        }

        _update_hero_sprite();
    }

    void _update_hero_sprite()
    {
        int frame = 0;

        if(_attack_anim > 0)
        {
            frame = 3;
        }
        else if(_moving)
        {
            int step = (_walk / 8) % 4;
            frame = step == 0 ? 1 : (step == 2 ? 2 : 0);
        }

        int z = -_y.integer();
        _body.set_tiles(_sheet.tiles_item(), sheet_dir(_dir) * 4 + frame);
        _body.set_horizontal_flip(_dir == dir_left);
        _body.set_position(_x, _y - 14);
        _body.set_z_order(z);

        // Weapon in hand, swung during attacks.
        int side = _dir == dir_left ? -1 : 1;
        bn::fixed wx = _x + (_dir == dir_up ? -7 : (_dir == dir_down ? 7 : 6 * side));
        bn::fixed wy = _y - 15;
        int angle = 15;
        int weapon = class_weapon(_hero.class_index);
        bool swings = weapon == gen::WEAPON_SWORD || weapon == gen::WEAPON_HAMMER ||
                      weapon == gen::WEAPON_DAGGER || weapon == gen::WEAPON_MACE;

        if(_attack_anim > 0)
        {
            if(swings)
            {
                angle = 60 - (12 - _attack_anim) * 14;
                wx += side * 3;
            }
            else
            {
                angle = -35;
                wy -= 2;
            }
        }

        angle *= -side;
        _weapon.set_rotation_angle((angle + 360) % 360);
        _weapon.set_position(wx, wy);
        _weapon.set_z_order(_dir == dir_up ? z + 1 : z - 1);
        _weapon.set_visible(! _ghost);
    }

    void _regenerate()
    {
        ++_regen_timer;

        bool in_combat = _combat_timer > 0;

        if(_regen_timer % (in_combat ? 60 : 8) == 0 && _hp < _max_hp)
        {
            _hp += bn::max(1, _max_hp / 50);
            _hp = bn::min(_hp, _max_hp);
        }

        switch(_class.resource)
        {

        case resource_kind::MANA:
            if(_regen_timer % (in_combat ? 30 : 6) == 0 && _res < _max_res)
            {
                _res = bn::min(_res + bn::max(1, _max_res / 40), _max_res);
            }
            break;

        case resource_kind::ENERGY:
            if(_regen_timer % 6 == 0 && _res < _max_res)
            {
                ++_res;
            }
            break;

        default:
            if(! in_combat && _regen_timer % 20 == 0 && _res > 0)
            {
                --_res;
            }
            break;
        }
    }

    void _gain_rage(int amount)
    {
        if(_class.resource == resource_kind::RAGE)
        {
            _res = bn::min(_res + amount, _max_res);
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Targeting.
    // -----------------------------------------------------------------------------------------------------------------

    [[nodiscard]] bool _valid_target(int index, int range) const
    {
        if(index < 0 || index >= _enemies.size())
        {
            return false;
        }

        const enemy& e = _enemies[index];
        return e.state != enemy_state::DEAD && e.state != enemy_state::RETURN &&
               dist2(_x, _y, e.x, e.y) <= range * range;
    }

    [[nodiscard]] int _nearest_enemy(int range, int exclude = -1) const
    {
        int best = -1;
        int best_d = range * range + 1;

        for(int i = 0, n = _enemies.size(); i < n; ++i)
        {
            if(i == exclude || ! _valid_target(i, range))
            {
                continue;
            }

            int d = dist2(_x, _y, _enemies[i].x, _enemies[i].y);

            // Prefer enemies in front of the hero.
            const enemy& e = _enemies[i];
            if(dir_towards(_x, _y, e.x, e.y) != _dir)
            {
                d += 24 * 24;
            }

            if(d < best_d)
            {
                best_d = d;
                best = i;
            }
        }

        return best;
    }

    void _update_target()
    {
        if(_target >= 0 && ! _valid_target(_target, 170))
        {
            _target = -1;
        }

        if(bn::keypad::l_pressed())
        {
            int next = _nearest_enemy(150, _target);

            if(next >= 0)
            {
                _target = next;
            }
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Abilities.
    // -----------------------------------------------------------------------------------------------------------------

    void _use_ability(int slot)
    {
        const ability_def& ability = _class.abilities[slot];

        if(_cooldowns[slot] > 0)
        {
            if(slot > 0)
            {
                _show_message("That ability isn't ready yet");
            }

            return;
        }

        bool self_cast = ability.kind == ability_kind::HEAL || ability.kind == ability_kind::SHIELD ||
                         ability.kind == ability_kind::NOVA;

        if(! self_cast)
        {
            if(! _valid_target(_target, ability.range + 40))
            {
                _target = _nearest_enemy(ability.range + 30);
            }

            if(_target < 0)
            {
                if(slot == 0 && ability.kind == ability_kind::MELEE)
                {
                    // Swing at the air.
                    _attack_anim = 12;
                    _cooldowns[0] = ability.cooldown;
                }
                else if(bn::keypad::a_pressed() || slot > 0)
                {
                    _show_message("No target");
                }

                return;
            }

            const enemy& e = _enemies[_target];

            if(dist2(_x, _y, e.x, e.y) > ability.range * ability.range)
            {
                if(slot > 0 || bn::keypad::a_pressed())
                {
                    _show_message("Out of range");
                }

                if(ability.kind == ability_kind::MELEE && slot == 0)
                {
                    _attack_anim = 12;
                    _cooldowns[0] = ability.cooldown;
                }

                return;
            }

            _dir = dir_towards(_x, _y, e.x, e.y);
        }

        if(_res < ability.cost)
        {
            _show_message(_class.resource == resource_kind::MANA ? "Not enough mana" :
                          _class.resource == resource_kind::RAGE ? "Not enough rage" : "Not enough energy");
            return;
        }

        _res -= ability.cost;
        _cooldowns[slot] = ability.cooldown;

        // Abilities share a short global cooldown with the auto attack.
        if(slot > 0)
        {
            _cooldowns[0] = bn::max(_cooldowns[0], 20);
        }

        _attack_anim = 12;
        int damage = _weapon_damage() * ability.power / 100;

        switch(ability.kind)
        {

        case ability_kind::MELEE:
            _damage_enemy(_target, damage, slot > 0);
            _gain_rage(slot == 0 ? 6 : 0);

            if(ability.fx >= 0)
            {
                _add_effect(gen::fx, ability.fx, 2, 4, 12, _target, false);
            }
            break;

        case ability_kind::BOLT:
        {
            if(_projectiles.full())
            {
                break;
            }

            bool vertical = ability.fx == gen::FX_ARROW_H && (_dir == dir_up || _dir == dir_down);
            int fx = vertical ? gen::FX_ARROW_V : ability.fx;
            bn::sprite_ptr sprite = gen::fx.create_sprite(_x, _y - 14, fx);
            sprite.set_camera(_camera);
            sprite.set_bg_priority(1);
            sprite.set_horizontal_flip(_dir == dir_left);
            sprite.set_vertical_flip(vertical && _dir == dir_down);
            _projectiles.push_back(projectile{ _x, _y - 14, _target, fx, damage, ability.extra, 120,
                                               bn::move(sprite) });
            break;
        }

        case ability_kind::HEAL:
        {
            int amount = _max_hp * ability.power / 100 + _level * 2;
            _hp = bn::min(_hp + amount, _max_hp);
            _add_float(amount, gen::font_green_palette, _x, _y - 34);
            _add_effect(gen::fx, gen::FX_HEAL, 2, 6, 30, -1, false);
            break;
        }

        case ability_kind::SHIELD:
            _shield = _max_hp * ability.power / 100;
            _add_effect(gen::fx, gen::FX_SHIELD, 1, 4, 40, -1, false);
            _show_message("Shielded");
            break;

        case ability_kind::NOVA:
        {
            _add_effect(gen::big_fx, 0, 3, 5, 15, -1, true);

            for(int i = 0, n = _enemies.size(); i < n; ++i)
            {
                if(_valid_target(i, ability.range))
                {
                    _damage_enemy(i, damage, true);

                    if(ability.extra > 0 && _enemies[i].state != enemy_state::DEAD)
                    {
                        _enemies[i].root = ability.extra;
                    }
                }
            }
            break;
        }

        case ability_kind::DOT:
        {
            enemy& e = _enemies[_target];
            e.dot_ticks = 5;
            e.dot_timer = 60;
            e.dot_damage = bn::max(1, damage / 5);
            _aggro(_target);
            _add_effect(gen::fx, ability.fx, 2, 6, 24, _target, false);
            break;
        }

        case ability_kind::DRAIN:
        {
            int before = _enemies[_target].hp;
            _damage_enemy(_target, damage, true);
            int drained = before - bn::max(0, _enemies[_target].hp);
            _hp = bn::min(_hp + drained, _max_hp);
            _add_effect(gen::fx, gen::FX_SHADOWBOLT, 2, 4, 20, _target, false);
            _add_effect(gen::fx, gen::FX_HEAL, 2, 6, 24, -1, false);
            break;
        }

        default:
            _damage_enemy(_target, damage, true);
            _add_effect(gen::fx, ability.fx, 2, 4, 20, _target, false);
            break;
        }

        _combat_timer = 300;
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Projectiles.
    // -----------------------------------------------------------------------------------------------------------------

    void _update_projectiles()
    {
        for(int i = 0; i < _projectiles.size();)
        {
            projectile& p = _projectiles[i];
            bool done = --p.life <= 0 || p.target >= _enemies.size() ||
                        _enemies[p.target].state == enemy_state::DEAD;

            if(! done)
            {
                const enemy& e = _enemies[p.target];
                bn::fixed tx = e.x;
                bn::fixed ty = e.y - 10;
                bn::fixed dx = tx - p.x;
                bn::fixed dy = ty - p.y;
                bn::fixed len = bn::sqrt(dx * dx + dy * dy);

                if(len < 6)
                {
                    _damage_enemy(p.target, p.damage, false);

                    if(p.slow > 0 && _enemies[p.target].state != enemy_state::DEAD)
                    {
                        _enemies[p.target].slow = p.slow;
                    }

                    _add_effect(gen::fx, gen::FX_HIT, 2, 3, 8, p.target, false);
                    done = true;
                }
                else
                {
                    bn::fixed speed = 3;
                    p.x += dx * speed / len;
                    p.y += dy * speed / len;
                    p.sprite.set_position(p.x, p.y);

                    if(p.fx != gen::FX_ARROW_H && p.fx != gen::FX_ARROW_V)
                    {
                        p.sprite.set_tiles(gen::fx.tiles_item(), p.fx + ((_frame / 4) % 2 ? 1 : 0));
                        p.sprite.set_horizontal_flip(dx < 0);
                    }
                }
            }

            if(done)
            {
                _projectiles.erase(_projectiles.begin() + i);
            }
            else
            {
                ++i;
            }
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Enemies.
    // -----------------------------------------------------------------------------------------------------------------

    void _spawn_enemy(enemy& e)
    {
        const enemy_def& def = gen::enemies[e.def];
        e.level = def.min_level + _random.get_int(def.max_level - def.min_level + 1);
        e.max_hp = _enemy_max_hp(e.level);
        e.hp = e.max_hp;
        e.x = e.home_x;
        e.y = e.home_y;
        e.wander_x = e.x;
        e.wander_y = e.y;
        e.state = enemy_state::IDLE;
        e.timer = _random.get_int(120);
        e.dot_ticks = 0;
        e.slow = 0;
        e.root = 0;
        e.hurt = 0;
    }

    void _aggro(int index)
    {
        enemy& e = _enemies[index];

        if(e.state == enemy_state::IDLE)
        {
            e.state = enemy_state::CHASE;
            e.attack_cooldown = 30;
        }
    }

    void _damage_enemy(int index, int damage, bool crit_text)
    {
        enemy& e = _enemies[index];

        if(e.state == enemy_state::DEAD)
        {
            return;
        }

        e.hp -= damage;
        e.hurt = 8;
        _combat_timer = 300;
        _target = index;
        _add_float(damage, crit_text ? gen::font_yellow_palette : gen::font_white_palette, e.x, e.y - 28);

        if(e.hp <= 0)
        {
            _kill_enemy(index);
        }
        else
        {
            _aggro(index);
        }
    }

    void _kill_enemy(int index)
    {
        enemy& e = _enemies[index];
        e.hp = 0;
        e.state = enemy_state::DEAD;
        e.respawn = 1500 + _random.get_int(600);
        e.timer = 0;

        if(_target == index)
        {
            _target = -1;
        }

        int xp = _kill_xp(e.level);

        if(xp > 0)
        {
            _gain_xp(xp);
        }

        // Quest progress.
        for(int q = 0; q < gen::quests_count; ++q)
        {
            const quest_def& quest = gen::quests[q];

            if(_quest_state[q] == 1 && quest.enemy == e.def)
            {
                ++_quest_progress[q];

                bn::string<48> text(gen::enemies[e.def].name);
                text.append(" slain: ");
                text.append(bn::to_string<4>(int(_quest_progress[q])));
                text.append("/");
                text.append(bn::to_string<4>(quest.count));

                if(_quest_progress[q] >= quest.count)
                {
                    _quest_state[q] = 2;
                    text = quest.title;
                    text.append(" (Complete)");
                }

                _show_message(text, true);
                _refresh_tracker();
            }
        }
    }

    void _update_enemies()
    {
        for(int i = 0, n = _enemies.size(); i < n; ++i)
        {
            enemy& e = _enemies[i];
            const enemy_def& def = gen::enemies[e.def];
            ++e.anim;

            if(e.hurt > 0)
            {
                --e.hurt;
            }

            if(e.state == enemy_state::DEAD)
            {
                ++e.timer;

                if(--e.respawn <= 0 && dist2(_x, _y, e.home_x, e.home_y) > 110 * 110)
                {
                    _spawn_enemy(e);
                }

                _update_enemy_sprite(e, def, false);
                continue;
            }

            // Damage over time.
            if(e.dot_ticks > 0 && --e.dot_timer <= 0)
            {
                e.dot_timer = 60;
                --e.dot_ticks;
                _damage_enemy(i, e.dot_damage, false);

                if(e.state == enemy_state::DEAD)
                {
                    _update_enemy_sprite(e, def, false);
                    continue;
                }
            }

            if(e.root > 0)
            {
                --e.root;
            }

            if(e.slow > 0)
            {
                --e.slow;
            }

            bool moving = false;
            bn::fixed speed = bn::fixed::from_data(def.speed << 8);  // speed / 16

            if(e.slow > 0)
            {
                speed /= 2;
            }

            int player_d2 = dist2(_x, _y, e.x, e.y);

            switch(e.state)
            {

            case enemy_state::IDLE:
                if(! _ghost && def.aggro_radius > 0 && player_d2 < def.aggro_radius * def.aggro_radius &&
                   _level - e.level < 6)
                {
                    _aggro(i);
                    break;
                }

                if(--e.timer <= 0)
                {
                    e.timer = 90 + _random.get_int(180);
                    e.wander_x = e.home_x + _random.get_int(49) - 24;
                    e.wander_y = e.home_y + _random.get_int(49) - 24;
                }

                if(dist2(e.x, e.y, e.wander_x, e.wander_y) > 4)
                {
                    moving = _step_towards(e, e.wander_x, e.wander_y, speed / 2, def.flying);
                }
                break;

            case enemy_state::CHASE:
                if(_ghost || dist2(e.x, e.y, e.home_x, e.home_y) > 220 * 220)
                {
                    e.state = enemy_state::RETURN;
                    break;
                }

                if(player_d2 > 16 * 16)
                {
                    if(e.root <= 0)
                    {
                        moving = _step_towards(e, _x, _y, speed, def.flying);
                    }
                }
                else
                {
                    e.dir = _x < e.x ? dir_left : dir_right;
                }

                if(e.attack_cooldown > 0)
                {
                    --e.attack_cooldown;
                }
                else if(player_d2 <= 20 * 20)
                {
                    e.attack_cooldown = 100;
                    e.attack_anim = 12;
                    _hurt_hero(_enemy_damage(e.level));
                }
                break;

            case enemy_state::RETURN:
                moving = _step_towards(e, e.home_x, e.home_y, speed * 2, true);
                e.hp = e.max_hp;
                e.dot_ticks = 0;

                if(dist2(e.x, e.y, e.home_x, e.home_y) < 9)
                {
                    e.state = enemy_state::IDLE;
                }
                break;

            default:
                break;
            }

            if(e.attack_anim > 0)
            {
                --e.attack_anim;
            }

            _update_enemy_sprite(e, def, moving);
        }
    }

    bool _step_towards(enemy& e, bn::fixed tx, bn::fixed ty, bn::fixed speed, bool flying)
    {
        bn::fixed dx = tx - e.x;
        bn::fixed dy = ty - e.y;
        bn::fixed mx = dx > speed ? speed : (dx < -speed ? -speed : dx);
        bn::fixed my = dy > speed ? speed : (dy < -speed ? -speed : dy);

        if(mx == 0 && my == 0)
        {
            return false;
        }

        _move(e.x, e.y, mx, my, flying);

        if(bn::abs(dx) > 1)
        {
            e.dir = dx < 0 ? dir_left : dir_right;
        }

        return true;
    }

    void _update_enemy_sprite(enemy& e, const enemy_def& def, bool moving)
    {
        bool on_screen = bn::abs(e.x - _camera.x()) < 140 && bn::abs(e.y - _camera.y()) < 104;
        bool visible = on_screen && (e.state != enemy_state::DEAD || e.timer < 90);

        if(! visible)
        {
            e.sprite.reset();
            return;
        }

        if(! e.sprite)
        {
            e.sprite = make_sprite(*def.sheet, 0, *def.palette);
            e.sprite->set_camera(_camera);
            e.sprite->set_bg_priority(2);
        }

        int frame = 0;

        if(e.attack_anim > 0)
        {
            frame = 3;
        }
        else if(moving || def.flying)
        {
            int step = (e.anim / 8) % 4;
            frame = step == 0 ? 1 : (step == 2 ? 2 : 0);
        }

        bn::fixed y = e.y;

        if(def.beast)
        {
            e.sprite->set_tiles(def.sheet->tiles_item(), frame);
            e.sprite->set_horizontal_flip(e.dir == dir_left);
        }
        else
        {
            int dir = e.dir;

            if(e.state == enemy_state::CHASE && dist2(e.x, e.y, _x, _y) < 30 * 30)
            {
                dir = dir_towards(e.x, e.y, _x, _y);
            }

            e.sprite->set_tiles(def.sheet->tiles_item(), sheet_dir(dir) * 4 + frame);
            e.sprite->set_horizontal_flip(dir == dir_left);
        }

        if(def.flying)
        {
            y -= 10;
        }

        e.sprite->set_position(e.x, y - 14);
        e.sprite->set_z_order(-e.y.integer());

        if(e.state == enemy_state::DEAD)
        {
            e.sprite->set_visible((e.timer / 4) % 2 == 0);
            e.sprite->set_tiles(def.sheet->tiles_item(), def.beast ? 0 : 4 * sheet_dir(e.dir));
        }
        else
        {
            e.sprite->set_visible(e.hurt == 0 || (e.hurt / 2) % 2 == 0);
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Hero damage, death and ghost.
    // -----------------------------------------------------------------------------------------------------------------

    void _hurt_hero(int damage)
    {
        if(_ghost)
        {
            return;
        }

        _combat_timer = 300;
        _gain_rage(damage / 2 + 2);

        if(_shield > 0)
        {
            int absorbed = bn::min(_shield, damage);
            _shield -= absorbed;
            damage -= absorbed;

            if(damage == 0)
            {
                _show_message("Absorbed");
                return;
            }
        }

        _hp -= damage;
        _add_float(damage, gen::font_red_palette, _x, _y - 34);

        if(_hp <= 0)
        {
            _die();
        }
    }

    void _die()
    {
        _hp = 0;
        _show_message("You have died. Release spirit...");

        for(int i = 0; i < 60; ++i)
        {
            _update_effects();
            _update_floats();
            _update_hud();
            bn::core::update();
        }

        fade(true, 24);
        _corpse_x = _x;
        _corpse_y = _y;
        _corpse = _sheet.create_sprite(_x, _y - 6, 0);
        _corpse->set_palette(*_palette);
        _corpse->set_camera(_camera);
        _corpse->set_rotation_angle(90);
        _corpse->set_bg_priority(2);
        _corpse->set_z_order(-_y.integer());

        _x = _zone.grave_x;
        _y = _zone.grave_y;
        _ghost = true;
        _target = -1;
        _projectiles.clear();
        _shield = 0;

        for(enemy& e : _enemies)
        {
            if(e.state == enemy_state::CHASE)
            {
                e.state = enemy_state::RETURN;
            }
        }

        bn::bg_palettes::set_grayscale_intensity(1);
        bn::sprite_palettes::set_grayscale_intensity(1);
        bn::blending::set_transparency_alpha(0.6);
        _body.set_blending_enabled(true);
        _update_camera();
        _update_hero_sprite();
        _show_banner("Spirit Healer");
        fade(false, 24);
        _show_message("Return to your corpse to resurrect");
    }

    void _resurrect()
    {
        _ghost = false;
        _corpse.reset();
        _hp = _max_hp / 2;

        if(_class.resource == resource_kind::MANA)
        {
            _res = _max_res / 2;
        }

        bn::bg_palettes::set_grayscale_intensity(0);
        bn::sprite_palettes::set_grayscale_intensity(0);
        _body.set_blending_enabled(false);
        _add_effect(gen::big_fx, 6, 2, 6, 36, -1, true);
        _show_message("You have been resurrected", true);
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Experience.
    // -----------------------------------------------------------------------------------------------------------------

    void _gain_xp(int xp)
    {
        if(_level >= max_level)
        {
            return;
        }

        _xp += xp;

        bn::string<24> text("+");
        text.append(bn::to_string<6>(xp));
        text.append(" XP");
        _add_float_text(text, gen::font_purple_palette, _x, _y - 44);

        while(_level < max_level && _xp >= xp_to_next(_level))
        {
            _xp -= xp_to_next(_level);
            ++_level;
            _recalc_stats();
            _hp = _max_hp;

            if(_class.resource == resource_kind::MANA)
            {
                _res = _max_res;
            }

            _add_effect(gen::big_fx, 3, 3, 6, 36, -1, true);
            bn::string<24> banner("Level ");
            banner.append(bn::to_string<4>(_level));
            banner.append("!");
            _show_banner(banner);
            _refresh_hero_label();
        }

        if(_level >= max_level)
        {
            _xp = 0;
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // NPCs and quests.
    // -----------------------------------------------------------------------------------------------------------------

    [[nodiscard]] int _npc_quest(int npc_def_index) const
    {
        // First quest of this NPC that isn't turned in and whose prerequisite is done.
        for(int q = 0; q < gen::quests_count; ++q)
        {
            const quest_def& quest = gen::quests[q];

            if(quest.giver == npc_def_index && _quest_state[q] < 3 &&
               (quest.prereq < 0 || _quest_state[quest.prereq] == 3))
            {
                return q;
            }
        }

        return -1;
    }

    void _update_npcs()
    {
        for(npc& n : _npcs)
        {
            const npc_def& def = gen::npcs[n.def];
            bool on_screen = bn::abs(n.x - _camera.x()) < 140 && bn::abs(n.y - _camera.y()) < 110;

            if(! on_screen)
            {
                n.sprite.reset();
                n.mark.reset();
                continue;
            }

            if(! n.sprite)
            {
                n.sprite = make_sprite(*def.sheet, 0, *def.palette);
                n.sprite->set_position(n.x, n.y - 14);
                n.sprite->set_camera(_camera);
                n.sprite->set_bg_priority(2);
                n.sprite->set_z_order(-n.y.integer());
            }

            int dir = n.dir;

            if(dist2(n.x, n.y, _x, _y) < 40 * 40 && ! _ghost)
            {
                dir = dir_towards(n.x, n.y, _x, _y);
            }

            n.sprite->set_tiles(def.sheet->tiles_item(), sheet_dir(dir) * 4);
            n.sprite->set_horizontal_flip(dir == dir_left);

            int q = _npc_quest(n.def);
            int mark = -1;

            if(q >= 0)
            {
                mark = _quest_state[q] == 0 ? 0 : (_quest_state[q] == 2 ? 1 : 2);
            }

            if(mark < 0)
            {
                n.mark.reset();
            }
            else
            {
                if(! n.mark)
                {
                    n.mark = gen::quest_marks.create_sprite(n.x, n.y - 40, mark);
                    n.mark->set_camera(_camera);
                    n.mark->set_bg_priority(1);
                }

                n.mark->set_tiles(gen::quest_marks.tiles_item(), mark);
                n.mark->set_y(n.y - 40 + ((_frame / 16) % 2));
            }
        }
    }

    bool _talk_to_npc()
    {
        for(int i = 0, n = _npcs.size(); i < n; ++i)
        {
            const npc& person = _npcs[i];

            if(dist2(person.x, person.y, _x, _y) < 28 * 28)
            {
                _open_npc_dialog(i);
                return true;
            }
        }

        return false;
    }

    void _open_npc_dialog(int index)
    {
        const npc& person = _npcs[index];
        const npc_def& def = gen::npcs[person.def];
        _dialog_npc = index;
        _dialog_quest = _npc_quest(person.def);

        bn::string<64> title(def.name);
        bn::string<200> body;
        const char* footer = "A: Close";
        _dialog = dialog_mode::TALK;

        if(_dialog_quest >= 0)
        {
            const quest_def& quest = gen::quests[_dialog_quest];
            int state = _quest_state[_dialog_quest];

            if(state == 0)
            {
                _dialog = dialog_mode::OFFER;
                title = quest.title;
                body = quest.text;
                body.append(" Slay: ");
                body.append(gen::enemies[quest.enemy].name);
                body.append(" x");
                body.append(bn::to_string<4>(quest.count));
                footer = "A: Accept   B: Decline";
            }
            else if(state == 2)
            {
                _dialog = dialog_mode::TURN_IN;
                title = quest.title;
                body = quest.complete_text;
                body.append(" Reward: ");
                body.append(bn::to_string<6>(quest.xp));
                body.append(" XP");
                footer = "A: Complete Quest";
            }
            else
            {
                title = quest.title;
                body = "Return when the task is done. ";
                body.append(gen::enemies[quest.enemy].name);
                body.append(": ");
                body.append(bn::to_string<4>(int(_quest_progress[_dialog_quest])));
                body.append("/");
                body.append(bn::to_string<4>(quest.count));
            }
        }
        else
        {
            body = def.greeting;

            if(def.heals)
            {
                _hp = _max_hp;

                if(_class.resource == resource_kind::MANA)
                {
                    _res = _max_res;
                }

                _add_effect(gen::fx, gen::FX_HEAL, 2, 6, 30, -1, false);
            }
            else if(_all_zone_quests_done())
            {
                body.append(" You have done all we asked. The wider world awaits you, hero!");
            }
        }

        _show_dialog(title, body, footer);
    }

    [[nodiscard]] bool _all_zone_quests_done() const
    {
        for(const npc& person : _npcs)
        {
            for(int q = 0; q < gen::quests_count; ++q)
            {
                if(gen::quests[q].giver == person.def && _quest_state[q] != 3)
                {
                    return false;
                }
            }
        }

        return true;
    }

    void _open_log()
    {
        _dialog = dialog_mode::LOG;

        bn::string<64> title(_hero.name);
        title.append(" - Level ");
        title.append(bn::to_string<4>(_level));
        title.append(" ");
        title.append(_race.name);
        title.append(" ");
        title.append(class_names[_hero.class_index]);

        _clear_dialog();
        _floats.clear();
        _banner.clear();
        _panel.set_visible(true);
        _text.set_left_alignment();
        _text.set_palette_item(gen::font_gold_palette);
        _text.generate(-112, 30, title, _dialog_text);
        _text.set_palette_item(gen::font_white_palette);

        int y = 41;
        int lines = 0;

        for(int q = 0; q < gen::quests_count && lines < 2; ++q)
        {
            if(_quest_state[q] == 1 || _quest_state[q] == 2)
            {
                bn::string<64> line(gen::quests[q].title);
                line.append(": ");

                if(_quest_state[q] == 2)
                {
                    line.append("Complete!");
                }
                else
                {
                    line.append(bn::to_string<4>(int(_quest_progress[q])));
                    line.append("/");
                    line.append(bn::to_string<4>(gen::quests[q].count));
                }

                _text.generate(-112, y, line, _dialog_text);
                y += 9;
                ++lines;
            }
        }

        if(lines == 0)
        {
            _text.set_palette_item(gen::font_grey_palette);
            _text.generate(-112, y, _all_zone_quests_done() ? "All quests here are done!" :
                                                              "No active quests. Look for a yellow !", _dialog_text);
            y += 9;
        }

        bn::string<64> abilities("A: ");
        abilities.append(_class.abilities[0].name);
        abilities.append("  B: ");
        abilities.append(_class.abilities[1].name);
        abilities.append("  R: ");
        abilities.append(_class.abilities[2].name);
        _text.set_palette_item(gen::font_blue_palette);
        _text.generate(-112, 59, abilities, _dialog_text);

        bn::string<64> xp_line("XP ");
        xp_line.append(bn::to_string<6>(_xp));
        xp_line.append("/");
        xp_line.append(bn::to_string<6>(xp_to_next(_level)));
        _text.set_palette_item(gen::font_grey_palette);
        _text.generate(-112, 69, xp_line, _dialog_text);
        _text.set_right_alignment();
        _text.generate(112, 69, "L: target  Start: close", _dialog_text);
        _text.set_center_alignment();
    }

    void _show_dialog(const bn::string_view& title, const bn::string_view& body, const char* footer)
    {
        _clear_dialog();
        _floats.clear();
        _banner.clear();
        _panel.set_visible(true);
        _text.set_left_alignment();
        _text.set_palette_item(gen::font_gold_palette);
        _text.generate(-112, 30, title, _dialog_text);
        _text.set_palette_item(gen::font_white_palette);

        bn::vector<bn::string<64>, 3> lines;
        wrap_text(body, 222, lines);
        int y = 41;

        for(const bn::string<64>& line : lines)
        {
            _text.generate(-112, y, line, _dialog_text);
            y += 9;
        }

        _text.set_palette_item(gen::font_grey_palette);
        _text.set_right_alignment();
        _text.generate(112, 69, footer, _dialog_text);
        _text.set_center_alignment();
    }

    void _clear_dialog()
    {
        _dialog_text.clear();
    }

    void _close_dialog()
    {
        _dialog = dialog_mode::NONE;
        _clear_dialog();
        _panel.set_visible(false);
    }

    void _update_dialog()
    {
        bool accept = bn::keypad::a_pressed();
        bool cancel = bn::keypad::b_pressed() || bn::keypad::start_pressed();

        if(! accept && ! cancel)
        {
            return;
        }

        dialog_mode mode = _dialog;
        int quest = _dialog_quest;
        _close_dialog();

        if(mode == dialog_mode::OFFER && accept)
        {
            _quest_state[quest] = 1;
            _quest_progress[quest] = 0;
            bn::string<64> text("Quest accepted: ");
            text.append(gen::quests[quest].title);
            _show_message(text, true);
            _refresh_tracker();
        }
        else if(mode == dialog_mode::TURN_IN && accept)
        {
            _quest_state[quest] = 3;
            bn::string<64> text(gen::quests[quest].title);
            text.append(" completed");
            _show_message(text, true);
            _gain_xp(gen::quests[quest].xp);
            _refresh_tracker();
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Areas.
    // -----------------------------------------------------------------------------------------------------------------

    void _check_area()
    {
        if(_frame % 15)
        {
            return;
        }

        int x = _x.integer();
        int y = _y.integer();
        int found = -1;

        for(int i = 0, n = _zone.areas.size(); i < n; ++i)
        {
            const area_def& area = _zone.areas[i];

            if(x >= area.x && y >= area.y && x < area.x + area.width && y < area.y + area.height)
            {
                found = i;
                break;
            }
        }

        if(found != _area)
        {
            _area = found;
            _show_banner(found >= 0 ? _zone.areas[found].name : _zone.name);
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // Effects and floating text.
    // -----------------------------------------------------------------------------------------------------------------

    void _add_effect(const bn::sprite_item& item, int first, int frames, int period, int life, int follow, bool big)
    {
        if(_effects.full())
        {
            _effects.erase(_effects.begin());
        }

        bn::sprite_ptr sprite = item.create_sprite(_x, _y - 14, first);
        sprite.set_camera(_camera);
        sprite.set_bg_priority(1);
        _effects.push_back(effect{ bn::move(sprite), first, frames, period, 0, life, follow, big });
        _position_effect(_effects.back());
    }

    void _position_effect(effect& fx)
    {
        if(fx.follow == -1)
        {
            fx.sprite.set_position(_x, _y - (fx.big ? 10 : 16));
        }
        else if(fx.follow >= 0 && fx.follow < _enemies.size())
        {
            const enemy& e = _enemies[fx.follow];
            fx.sprite.set_position(e.x, e.y - 12);
        }
    }

    void _update_effects()
    {
        for(int i = 0; i < _effects.size();)
        {
            effect& fx = _effects[i];
            ++fx.timer;

            if(fx.timer >= fx.life)
            {
                _effects.erase(_effects.begin() + i);
                continue;
            }

            const bn::sprite_item& item = fx.big ? gen::big_fx : gen::fx;
            fx.sprite.set_tiles(item.tiles_item(), fx.first_frame + (fx.timer / fx.period) % fx.frames);
            _position_effect(fx);
            ++i;
        }
    }

    void _add_float(int value, const bn::sprite_palette_item& palette, bn::fixed x, bn::fixed y)
    {
        _add_float_text(bn::to_string<8>(value), palette, x, y);
    }

    void _add_float_text(const bn::string_view& text, const bn::sprite_palette_item& palette, bn::fixed x, bn::fixed y)
    {
        if(_floats.full())
        {
            _floats.erase(_floats.begin());
        }

        float_text ft;
        _text.set_center_alignment();
        _text.set_palette_item(palette);
        _text.set_bg_priority(0);
        _text.generate(x, y, text, ft.sprites);

        for(bn::sprite_ptr& sprite : ft.sprites)
        {
            sprite.set_camera(_camera);
        }

        _floats.push_back(bn::move(ft));
    }

    void _update_floats()
    {
        for(int i = 0; i < _floats.size();)
        {
            float_text& ft = _floats[i];
            ++ft.timer;

            if(ft.timer > 50)
            {
                _floats.erase(_floats.begin() + i);
                continue;
            }

            if(ft.timer % 2 == 0)
            {
                for(bn::sprite_ptr& sprite : ft.sprites)
                {
                    sprite.set_y(sprite.y() - 1);
                }
            }

            ++i;
        }
    }

    // -----------------------------------------------------------------------------------------------------------------
    // HUD.
    // -----------------------------------------------------------------------------------------------------------------

    void _create_bar(bar& b, int kind, int segments, int x, int y)
    {
        b.kind = kind;
        b.segments.clear();
        b.last_fill = -1;

        for(int i = 0; i < segments; ++i)
        {
            bn::sprite_ptr sprite = gen::bars.create_sprite(x + i * 8, y, kind * 9);
            sprite.set_bg_priority(0);
            b.segments.push_back(bn::move(sprite));
        }
    }

    void _set_bar(bar& b, int value, int max_value)
    {
        int segments = b.segments.size();
        int total = segments * 8;
        int fill = max_value > 0 ? bn::clamp(value * total / max_value, 0, total) : 0;

        if(value > 0 && fill == 0)
        {
            fill = 1;
        }

        if(fill == b.last_fill)
        {
            return;
        }

        b.last_fill = fill;

        for(int i = 0; i < segments; ++i)
        {
            int f = bn::clamp(fill - i * 8, 0, 8);
            b.segments[i].set_tiles(gen::bars.tiles_item(), b.kind * 9 + f);
        }
    }

    void _set_bar_visible(bar& b, bool visible)
    {
        for(bn::sprite_ptr& sprite : b.segments)
        {
            sprite.set_visible(visible);
        }
    }

    void _refresh_hero_label()
    {
        _hero_label.clear();
        _text.set_left_alignment();
        _text.set_palette_item(gen::font_white_palette);

        bn::string<32> label(_hero.name);
        label.append("  Lv ");
        label.append(bn::to_string<4>(_level));
        _text.generate(-116, -71, label, _hero_label);
        _text.set_center_alignment();
    }

    void _refresh_tracker()
    {
        _tracker.clear();
        _text.set_right_alignment();

        int y = -38;
        int lines = 0;

        for(int q = 0; q < gen::quests_count && lines < 3; ++q)
        {
            if(_quest_state[q] == 1 || _quest_state[q] == 2)
            {
                const quest_def& quest = gen::quests[q];
                bn::string<48> line(gen::enemies[quest.enemy].name);
                line.append(" ");

                if(_quest_state[q] == 2)
                {
                    _text.set_palette_item(gen::font_green_palette);
                    line.append("(Done)");
                }
                else
                {
                    _text.set_palette_item(gen::font_yellow_palette);
                    line.append(bn::to_string<4>(int(_quest_progress[q])));
                    line.append("/");
                    line.append(bn::to_string<4>(quest.count));
                }

                _text.generate(118, y, line, _tracker);
                y += 9;
                ++lines;
            }
        }

        _text.set_center_alignment();
    }

    void _show_banner(const bn::string_view& text)
    {
        _banner.clear();
        _text.set_center_alignment();
        _text.set_palette_item(gen::font_gold_palette);
        _text.generate(0, -48, text, _banner);
        _banner_timer = 150;
    }

    void _show_message(const bn::string_view& text, bool good = false)
    {
        _message.clear();
        _text.set_center_alignment();
        _text.set_palette_item(good ? gen::font_yellow_palette : gen::font_red_palette);
        _text.generate(0, 58, text, _message);
        _message_timer = 90;
    }

    void _update_hud()
    {
        _set_bar(_hp_bar, _hp, _max_hp);
        _set_bar(_res_bar, _res, _max_res);
        _set_bar(_xp_bar, _xp, xp_to_next(_level));

        bool dialog = _dialog != dialog_mode::NONE;
        _set_bar_visible(_xp_bar, ! dialog);

        if(_banner_timer > 0 && --_banner_timer == 0)
        {
            _banner.clear();
        }

        if(_message_timer > 0 && --_message_timer == 0)
        {
            _message.clear();
        }

        for(bn::sprite_ptr& sprite : _message)
        {
            sprite.set_visible(! dialog);
        }

        // Target frame.
        int target_level = _target >= 0 ? _enemies[_target].level : -1;

        if(_target != _shown_target || target_level != _shown_target_level)
        {
            _shown_target = _target;
            _shown_target_level = target_level;
            _target_label.clear();

            if(_target >= 0)
            {
                const enemy& e = _enemies[_target];
                int diff = e.level - _level;
                const bn::sprite_palette_item& palette = diff >= 3 ? gen::font_red_palette :
                                                         diff >= -2 ? gen::font_yellow_palette :
                                                         diff >= -4 ? gen::font_green_palette : gen::font_grey_palette;
                bn::string<40> label(gen::enemies[e.def].name);
                label.append(" ");
                label.append(bn::to_string<4>(e.level));
                _text.set_right_alignment();
                _text.set_palette_item(palette);
                _text.generate(118, -71, label, _target_label);
                _text.set_center_alignment();

                if(_target_bar.segments.empty())
                {
                    _create_bar(_target_bar, gen::BAR_RAGE, 6, 112 - 44, -60);
                }

                _target_bar.last_fill = -1;
            }
            else
            {
                _target_bar.segments.clear();
            }
        }

        if(_target >= 0 && ! _target_bar.segments.empty())
        {
            const enemy& e = _enemies[_target];
            _set_bar(_target_bar, e.hp, e.max_hp);

            if(! _target_ring)
            {
                _target_ring = gen::target_ring.create_sprite(0, 0, 0);
                _target_ring->set_camera(_camera);
                _target_ring->set_bg_priority(2);
            }

            _target_ring->set_position(e.x, e.y - 1);
            _target_ring->set_z_order(-e.y.integer() + 1);
            _target_ring->set_tiles(gen::target_ring.tiles_item(), e.state == enemy_state::CHASE ? 0 : 1);
        }
        else
        {
            _target_ring.reset();
        }
    }

    void _update_camera()
    {
        int max_x = _zone.width_cells * 8 - 120;
        int max_y = _zone.height_cells * 8 - 80;
        bn::fixed cx = bn::clamp(_x, bn::fixed(120), bn::fixed(max_x));
        bn::fixed cy = bn::clamp(_y - 10, bn::fixed(80), bn::fixed(max_y));
        _camera.set_position(cx.round_integer(), cy.round_integer());
    }
};

}

void world_scene(const profile& hero)
{
    world* w = new world(hero);
    w->run();
    delete w;
}

}
