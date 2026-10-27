#ifndef PW_COMMON_H
#define PW_COMMON_H

#include "bn_core.h"
#include "bn_string.h"
#include "bn_vector.h"
#include "bn_keypad.h"
#include "bn_string_view.h"
#include "bn_bg_palettes.h"
#include "bn_sprite_palettes.h"
#include "bn_sprite_text_generator.h"

#include "pw_defs.h"
#include "pw_gen_font.h"

namespace pw
{

// The hero created in the character creation screen.
struct profile
{
    int race = 0;
    int class_index = 0;
    bn::string<16> name;
};

inline const char* class_names[] = {
    "Warrior", "Paladin", "Hunter", "Rogue", "Priest", "Shaman", "Mage", "Warlock", "Druid"
};

// Classic class robes: casters wear long robes.
[[nodiscard]] inline bool class_wears_robe(int class_index)
{
    return class_index == int(class_id::PRIEST) || class_index == int(class_id::MAGE) ||
           class_index == int(class_id::WARLOCK);
}

[[nodiscard]] inline int text_width(const bn::string_view& text)
{
    int width = 0;

    for(char c : text)
    {
        int index = int(c) - 32;

        if(index >= 0 && index < int(sizeof(gen::font_widths)))
        {
            width += gen::font_widths[index];
        }
    }

    return width;
}

// Splits text in lines no wider than max_width pixels.
template<int MaxLines>
void wrap_text(const bn::string_view& text, int max_width, bn::vector<bn::string<64>, MaxLines>& lines)
{
    lines.clear();

    bn::string<64> line;
    bn::string<64> word;
    int space_width = gen::font_widths[0];

    auto flush_word = [&]()
    {
        if(word.empty())
        {
            return;
        }

        int line_width = text_width(line);
        int word_width = text_width(word);

        if(! line.empty() && line_width + space_width + word_width > max_width)
        {
            if(! lines.full())
            {
                lines.push_back(line);
            }

            line.clear();
        }

        if(! line.empty())
        {
            line.push_back(' ');
        }

        line.append(word);
        word.clear();
    };

    for(char c : text)
    {
        if(c == ' ')
        {
            flush_word();
        }
        else if(word.size() < word.max_size() - 1)
        {
            word.push_back(c);
        }
    }

    flush_word();

    if(! line.empty() && ! lines.full())
    {
        lines.push_back(line);
    }
}

inline void fade(bool out, int frames = 16)
{
    for(int i = 0; i <= frames; ++i)
    {
        bn::fixed intensity = bn::fixed(i) / frames;

        if(! out)
        {
            intensity = 1 - intensity;
        }

        bn::bg_palettes::set_fade(bn::color(0, 0, 0), intensity);
        bn::sprite_palettes::set_fade(bn::color(0, 0, 0), intensity);
        bn::core::update();
    }
}

void title_scene();
bool create_scene(profile& hero);
void world_scene(const profile& hero);

}

#endif
