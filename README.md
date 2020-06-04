
Requires: Python3, bearlibterminal


# HoS

HoS is a HoMM-like roguelike written in Python/bearlibterm.

(HoMM means Heroes of Might and Magic)

Requirements
---

- Python3  (On Mac OS run `brew install python3`, other platforms see http://www.python.org/downloads/)

- bearlibterminal
    `pip3 install bearlibterminal`

To play, clone the repo:

 - `git clone git@github.com:akulakov/hos.git`; 
 - then run `python3 hos.py`

# Commands

## Move

    h - move left

    l - move right

    y - move left+up

    u - move right+up

    b - move left+down

    n - move right+down

    H and L - run

## Town (castle) UI

    b - build menu
    r - recruit troops
    R - auto recruit all available and transfer to Hero army
    t - transfer troops between a hero and town
    H - recruit heroes

## Battle

    a - auto-battle
    f - fire ranged weapon

## Other

    q - quit

# Window Size

-s arg can be used to adjust tile size and therefore window size
Default is 24, so to make a smaller window, you can run, e.g.:

    python3 hos.py -s18
