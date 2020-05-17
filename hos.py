#!/usr/bin/env python
from curses import wrapper, newwin
import curses
import os
import sys
from random import random, choice
from collections import defaultdict
from textwrap import wrap
import string
import shelve
from copy import copy, deepcopy

HEIGHT = 16
debug_log = open('debug', 'w')
LOAD_BOARD = 999
SLP = 0.01
SEQ_TYPES = (list, tuple)
objects = {}

class Player:
    def __init__(self, name, is_ai):
        self.name, self.is_ai = name, is_ai

    def __repr__(self):
        return f'<P: {self.name}>'

class Hero:
    def __init__(self, name, map_name, loc, owner, char):
        self.name, self.map_name, self.loc, self.owner, self.char = name, map_name, loc, owner, char

    def __str__(self):
        return self.char

    def __repr__(self):
        return f'<H: {self.name}>'

class Castle:
    def __init__(self, name, map_name, entry_loc, owner):
        self.name, self.map_name, self.entry_loc, self.owner = name, map_name, entry_loc, owner

    def __repr__(self):
        return f'<C: {self.name}>'


class Blocks:
    blank = ' '
    rock = '█'
    platform = '▁'
    door = '🚪'
    water = '⏖'
    fountain = '‿'
    tree1 = '🌲'
    tree2 = '🌳'
    rock2 = '▧'
    rock3 = '▓'
    cactus = '🌵'
    tulip = '🌷'
    snowman = '☃'
    snowflake = '❄'
    books = '📚'
    open_book = '📖'
    lever = '⎆'
    sharp_rock = '⩕'
    statue = 'Ω'
    hexagon = '⎔'
    soldier = '⍾'

class Windows:
    pass

class Misc:
    pass

class Colors:
    blue_on_white = 1
    yellow_on_white = 2
    green_on_white = 3
    yellow_on_black = 4
    blue_on_black = 5

def mkcell():
    return [Blocks.blank]

def mkrow():
    return [mkcell() for _ in range(79)]

def first(x):
    return x[0] if x else None
def last(x):
    return x[-1] if x else None

def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(board_grid)
    w = len(board_grid[1])
    newx, newy = loc.x+x, loc.y+y
    return 0 <= newy <= h-1 and 0 <= newx <= w-1

def pdb(*arg):
    curses.nocbreak()
    Windows.win.keypad(0)
    curses.echo()
    curses.endwin()
    import pdb; pdb.set_trace()

class Loc:
    def __init__(self, x, y):
        self.y, self.x = y, x

    def __iter__(self):
        yield self.x
        yield self.y

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __repr__(self):
        return str((self.x, self.y))

    def __eq__(self, l):
        if isinstance(l, Loc):
            return (self.x, self.y) == (l.x, l.y)

    def mod(self, y=0, x=0):
        new = copy(self)
        new.y += y
        new.x += x
        return new

    def mod_r(self):
        return self.mod(0, 1)

    def mod_l(self):
        return self.mod(0, -1)

    def mod_d(self):
        return self.mod(1, 0)

    def mod_u(self):
        return self.mod(-1, 0)

class Board:
    def __init__(self, loc, _map):
        self.B = [mkrow() for _ in range(HEIGHT)]
        self.labels = []
        self.colors = []
        self.loc = loc
        self._map = str(_map)
        # map_to_loc[str(_map)] = loc

    def __repr__(self):
        return f'<B: {self._map}>'

    def __getitem__(self, loc):
        o = self.B[loc.y][loc.x][-1]
        if isinstance(o,int): o = objects[o]
        return o

    def __iter__(self):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                yield Loc(x,y), cell

def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

class Boards:
    pass

board_grid = []

def main(stdscr):
    if not os.path.exists('saves'):
        os.mkdir('saves')
    Misc.is_game = 1
    curses.init_pair(Colors.blue_on_white, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(Colors.yellow_on_white, curses.COLOR_YELLOW, curses.COLOR_WHITE)
    curses.init_pair(Colors.green_on_white, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(Colors.yellow_on_black, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(Colors.blue_on_black, curses.COLOR_BLUE, curses.COLOR_BLACK)

    begin_x = 0; begin_y = 0; width = 80
    win = Windows.win = newwin(HEIGHT, width, begin_y, begin_x)
    begin_x = 0; begin_y = 16; height = 6; width = 80
    win2 = Windows.win2 = newwin(height, width, begin_y, begin_x)

    Boards.b1 = Board(Loc(0,0), '1')
    board_grid[:] = [
        ['1'],
    ]


def editor(stdscr, _map):
    Misc.is_game = 0
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    curses.curs_set(True)
    loc = Loc(40, 8)
    brush = None
    written = 0
    B = Board(Loc(0,0), _map)
    fname = f'maps/{_map}.map'
    if not os.path.exists(fname):
        with open(fname, 'w') as fp:
            for _ in range(HEIGHT):
                fp.write(Blocks.blank*78 + '\n')
    B.load_map(_map, 1)
    B.draw(win)

    while 1:
        k = win.getkey()
        if k=='Q': return
        elif k in 'hjklyubnHL':
            n = 1
            if k in 'HL':
                n = 5
            m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]

            for _ in range(n):
                if brush:
                    B.B[loc.y][loc.x] = [brush]
                if chk_oob(loc.mod(*m)):
                    loc = loc.mod(*m)

        elif k == ' ':
            brush = None
        elif k == 'e':
            brush = ' '
        elif k == 'r':
            brush = Blocks.rock
        elif k == 'd':
            B.put(Blocks.door, loc)
        elif k in '0123456789':
            B.put(k, loc)
        elif k == 'w':
            B.put(Blocks.water, loc)

        # NPCs
        elif k == 'O':
            B.put(Blocks.soldier, loc)

        elif k == 'T':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
        elif k == 'x':
            B.put(Blocks.rock2, loc)
            brush = Blocks.rock2
        elif k == 'C':
            B.put(Blocks.cactus, loc)
        elif k == 'v':
            B.put(Blocks.snowflake, loc)
        elif k == 'V':
            B.put(Blocks.snowman, loc)

        elif k == 'o':
            cmds = 'gm gl gr l b ob f'.split()
            cmd = ''
            BL=Blocks
            while 1:
                cmd += win.getkey()
                if cmd == 'b':  B.put(BL.books, loc)
                elif cmd == 'ob': B.put(BL.open_book, loc)
                elif cmd == 't':  B.put(BL.tulip, loc)
                elif cmd == 'f':  B.put(BL.fountain, loc)
                elif cmd == 'v': B.put(BL.lever, loc)
                elif cmd == 's': B.put(BL.sharp_rock, loc)
                elif cmd == 'r': B.put(BL.rock3, loc)
                elif cmd == 'd': B.put(BL.hexagon, loc)     # drawing

                elif any(c.startswith(cmd) for c in cmds):
                    continue
                break

        elif k in 'E':
            win.addstr(2,2, 'Are you sure you want to clear the map? [Y/N]')
            y = win.getkey()
            if y=='Y':
                for row in B.B:
                    for cell in row:
                        cell[:] = [Blocks.blank]
                B.B[-1][-1].append('_')
        elif k in 'f':
            B.put(Blocks.shelves, loc)
        elif k == 'W':
            with open(f'maps/{_map}.map', 'w') as fp:
                for row in B.B:
                    for cell in row:
                        fp.write(str(cell[-1]))
                    fp.write('\n')
            written=1
        B.draw(win)
        if brush==Blocks.blank:
            tool = 'eraser'
        elif brush==Blocks.rock:
            tool = 'rock'
        elif not brush:
            tool = ''
        else:
            tool = brush
        win.addstr(1,73, tool)
        win.addstr(0, 0 if loc.x>40 else 70,
                   str(loc))
        if written:
            win.addstr(2,65, 'map written')
            written=0
        win.move(loc.y, loc.x)


if __name__ == "__main__":
    argv = sys.argv[1:]
    DBG = first(argv) == '-d'
    load_game = None
    a = first(argv)
    if a and a.startswith('-l'):
        load_game = a[2:]
    if first(argv) == 'ed':
        wrapper(editor, argv[1])
    else:
        wrapper(main, load_game)
