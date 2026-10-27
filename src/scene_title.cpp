#include "bn_regular_bg_ptr.h"
#include "bn_sprite_ptr.h"

#include "pw_common.h"
#include "pw_gen_bgs.h"

namespace pw
{

void title_scene()
{
    bn::bg_palettes::set_fade(bn::color(0, 0, 0), 1);
    bn::sprite_palettes::set_fade(bn::color(0, 0, 0), 1);

    bn::regular_bg_ptr bg = gen::bg_title_item.create_bg(8, 48);
    bn::sprite_text_generator text(gen::sprite_font);
    text.set_center_alignment();

    bn::vector<bn::sprite_ptr, 8> press_start;
    bn::vector<bn::sprite_ptr, 16> credits;
    text.set_palette_item(gen::font_grey_palette);
    text.generate(0, 64, "A classic demake for the Game Boy Advance", credits);
    text.set_palette_item(gen::font_yellow_palette);
    text.generate(0, 36, "PRESS START", press_start);

    fade(false);

    int counter = 0;

    while(! bn::keypad::start_pressed() && ! bn::keypad::a_pressed())
    {
        ++counter;

        bool visible = (counter / 32) % 2 == 0;

        for(bn::sprite_ptr& sprite : press_start)
        {
            sprite.set_visible(visible);
        }

        // Slow drift of the sky.
        bg.set_x(8 + ((counter / 16) % 2));
        bn::core::update();
    }

    fade(true);
}

}
