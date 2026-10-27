#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"
#include "bn_sprite_palette_ptr.h"
#include "bn_random.h"
#include "bn_optional.h"

#include "pw_common.h"
#include "pw_player_palette.h"
#include "pw_gen_bgs.h"
#include "pw_gen_data.h"

namespace pw
{

namespace
{
    constexpr int race_count = 8;
    constexpr int class_count = int(class_id::COUNT);

    [[nodiscard]] bn::fixed_point race_icon_position(int race)
    {
        int column = race < 4 ? -90 : 90;
        int row = race % 4;
        return bn::fixed_point(column, -33 + row * 19);
    }

    [[nodiscard]] bn::fixed_point class_icon_position(int class_index)
    {
        return bn::fixed_point(-80 + class_index * 20, 44);
    }

    [[nodiscard]] bool class_allowed(int race, int class_index)
    {
        return gen::races[race].classes_mask & (1 << class_index);
    }

    [[nodiscard]] int first_allowed_class(int race, int preferred)
    {
        if(class_allowed(race, preferred))
        {
            return preferred;
        }

        for(int i = 0; i < class_count; ++i)
        {
            if(class_allowed(race, i))
            {
                return i;
            }
        }

        return 0;
    }
}

bool create_scene(profile& hero)
{
    bn::random random;

    for(int i = 0; i < 64; ++i)
    {
        random.update();
    }

    bn::regular_bg_ptr bg = gen::bg_charselect_item.create_bg(8, 48);
    bn::sprite_text_generator text(gen::sprite_font);
    text.set_center_alignment();

    // Faction crests and race icons.
    bn::sprite_ptr alliance_crest = gen::crests.create_sprite(-90, -58, 0);
    bn::sprite_ptr horde_crest = gen::crests.create_sprite(90, -58, 1);
    bn::vector<bn::sprite_ptr, race_count> race_icons;

    for(int race = 0; race < race_count; ++race)
    {
        const bn::sprite_item& icons = race < 4 ? gen::race_icons_alliance : gen::race_icons_horde;
        race_icons.push_back(icons.create_sprite(race_icon_position(race), race % 4));
    }

    bn::vector<bn::sprite_ptr, class_count> class_icons;

    for(int i = 0; i < class_count; ++i)
    {
        class_icons.push_back(gen::class_icons.create_sprite(class_icon_position(i), i));
    }

    bn::sprite_ptr race_cursor = gen::cursor.create_sprite(0, 0);
    bn::sprite_ptr class_cursor = gen::cursor.create_sprite(0, 0);
    race_cursor.set_bg_priority(0);
    class_cursor.set_bg_priority(0);

    int race = random.get_int(race_count);
    int class_index = first_allowed_class(race, random.get_int(class_count));
    int name_index = random.get_int(8);
    bool dirty = true;
    int counter = 0;

    const bn::sprite_item* hero_sheet = nullptr;
    bn::optional<bn::sprite_ptr> hero_sprite;
    bn::optional<bn::sprite_ptr> weapon_sprite;
    bn::optional<bn::sprite_palette_ptr> hero_palette;
    bn::vector<bn::sprite_ptr, 32> labels;

    fade(false);

    while(true)
    {
        if(bn::keypad::up_pressed())
        {
            race = (race + race_count - 1) % race_count;
            name_index = random.get_int(8);
            dirty = true;
        }
        else if(bn::keypad::down_pressed())
        {
            race = (race + 1) % race_count;
            name_index = random.get_int(8);
            dirty = true;
        }
        else if(bn::keypad::left_pressed() || bn::keypad::right_pressed())
        {
            int step = bn::keypad::left_pressed() ? class_count - 1 : 1;
            int next = class_index;

            for(int i = 0; i < class_count; ++i)
            {
                next = (next + step) % class_count;

                if(class_allowed(race, next))
                {
                    break;
                }
            }

            class_index = next;
            dirty = true;
        }
        else if(bn::keypad::select_pressed())
        {
            name_index = (name_index + 1 + random.get_int(7)) % 8;
            dirty = true;
        }
        else if(bn::keypad::a_pressed() || bn::keypad::start_pressed())
        {
            hero.race = race;
            hero.class_index = class_index;
            hero.name = gen::race_names_list[race][name_index];
            fade(true);
            return true;
        }
        else if(bn::keypad::b_pressed())
        {
            fade(true);
            return false;
        }

        if(dirty)
        {
            dirty = false;
            class_index = first_allowed_class(race, class_index);
            race_cursor.set_position(race_icon_position(race));
            class_cursor.set_position(class_icon_position(class_index));

            for(int i = 0; i < class_count; ++i)
            {
                class_icons[i].set_palette(class_allowed(race, i) ? gen::class_icons.palette_item() :
                                                                    gen::class_icons_dim_palette);
            }

            const race_def& race_info = gen::races[race];
            bool robe = class_wears_robe(class_index);
            const bn::sprite_item& sheet = robe ? *race_info.robe_sheet : *race_info.sheet;
            hero_sheet = &sheet;
            hero_sprite.reset();
            weapon_sprite.reset();
            hero_sprite = sheet.create_sprite(0, -8, 0);
            hero_sprite->set_scale(2);

            bn::color colors[16];
            build_player_colors(race, class_index, colors);

            if(! hero_palette)
            {
                hero_palette = bn::sprite_palette_ptr::create_new(sheet.palette_item());
            }

            hero_palette->set_colors(colors);
            hero_sprite->set_palette(*hero_palette);
            weapon_sprite = gen::weapons.create_sprite(14, -10, class_weapon(class_index));
            weapon_sprite->set_scale(2);
            weapon_sprite->set_z_order(1);

            labels.clear();
            text.set_palette_item(gen::font_gold_palette);
            text.generate(0, -72, gen::race_names_list[race][name_index], labels);
            text.set_palette_item(gen::font_white_palette);

            bn::string<48> title;
            title.append(race_info.name);
            title.append(" ");
            title.append(class_names[class_index]);
            text.generate(0, -61, title, labels);
            text.set_palette_item(race_info.horde ? gen::font_red_palette : gen::font_blue_palette);
            bn::string<48> faction(race_info.faction);
            faction.append(" - ");
            faction.append(race_info.zone_name);
            text.generate(0, -50, faction, labels);
            text.set_palette_item(gen::font_grey_palette);
            text.set_palette_item(gen::font_white_palette);
            text.generate(0, 56, race_info.description_1, labels);
            text.generate(0, 65, race_info.description_2, labels);
            text.set_palette_item(gen::font_grey_palette);
            text.generate(0, 75, "Pad: race/class  Select: name  A: play", labels);
        }

        // Turn the hero around and walk in place.
        ++counter;

        int facing = (counter / 90) % 4;    // down, side, up, side (flipped)
        int dir_index = facing == 0 ? 0 : (facing == 2 ? 1 : 2);
        int step = (counter / 10) % 4;
        int frame = step == 1 ? 1 : (step == 3 ? 2 : 0);
        hero_sprite->set_tiles(hero_sheet->tiles_item(), dir_index * 4 + frame);
        hero_sprite->set_horizontal_flip(facing == 3);
        weapon_sprite->set_x(facing == 3 ? -14 : 14);
        weapon_sprite->set_horizontal_flip(facing == 3);
        weapon_sprite->set_z_order(facing == 2 ? 1 : -1);
        bn::core::update();
    }
}

}
