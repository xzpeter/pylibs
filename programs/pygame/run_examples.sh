#!/bin/bash

game_list="
aliens
oldalien
stars
chimp
moveit
fonty
freetype_misc
vgrade
eventlist
arraydemo
sound
sound_array_demos
liquid
glcube
scrap_clipboard
mask
testsprite
headless_no_windows_needed
fastevents
overlay
blend_fill
blit_blends
cursors
pixelarray
scaletest
midi
scroll
camera"

run_example_script () {
    local name=${1}
    local tmp_file="/tmp/pygame-test.py"
    cat > $tmp_file <<EOF
import pygame
import pygame.examples.${name}
pygame.examples.${name}.main()
EOF
    python $tmp_file
    rm -rf $tmp_file
}

for game in $game_list; do
    run_example_script $game
done
