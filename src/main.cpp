#include "bn_core.h"

#include "pw_common.h"

int main()
{
    bn::core::init();

    while(true)
    {
        pw::title_scene();

        pw::profile hero;

        if(pw::create_scene(hero))
        {
            pw::world_scene(hero);
        }
    }
}
