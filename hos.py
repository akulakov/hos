#!/usr/bin/env python
from curses import wrapper, newwin
import curses
import os
import sys
from random import choice
from collections import defaultdict
from textwrap import wrap
import string
# import shelve
from copy import copy  #, deepcopy

HEIGHT = 16
debug_log = open('debug', 'w')
LOAD_BOARD = 999
SLP = 0.01
SEQ_TYPES = (list, tuple)
board_grid = []

class ObjectsClass:
    def __setitem__(self, k, v):
        setattr(self, f'id_{k}', v)

    def __getitem__(self, k):
        return getattr(self, f'id_{k}')

    def __getattr__(self, k):
        id = getattr(ID, k)
        return getattr(self, f'id_{id}')

Objects = ObjectsClass()

class Player:
    gold = 0

    def __init__(self, name, is_ai):
        self.name, self.is_ai = name, is_ai

    def __repr__(self):
        return f'<P: {self.name}>'

class Castle:
    def __init__(self, name, map_name, entry_loc, owner):
        self.name, self.map_name, self.entry_loc, self.owner = name, map_name, entry_loc, owner

    def __repr__(self):
        return f'<C: {self.name}>'

class Type:
    door1 = 1
    container = 2

class Blocks:
    """All game tiles."""
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
    hero1 = '🙍'
    gold = '🌕'

BLOCKING = [Blocks.rock, ]

class ID:
    castle1 = 1
    hero1 = 2

class Windows:
    win2 = None

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
    """Game board (single screen)."""
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

    def found_type_at(self, type, loc):
        def get_obj(x):
            return Objects.get(x) or x
        return any(get_obj(x).type==type for x in self.get_all_obj(loc))

    def get_all(self, loc):
        return [n for n in self.B[loc.y][loc.x] if n!=Blocks.blank]

    def remove(self, obj, loc=None):
        loc = loc or obj.loc
        cell = self.B[loc.y][loc.x]
        cell.remove(obj if obj in cell else obj.id)

    def get_all_obj(self, loc):
        return [Objects.get(n) or n for n in self.B[loc.y][loc.x] if not isinstance(n, str)]

    def load_map(self, map_num, for_editor=0):
        _map = open(f'maps/{map_num}.map').readlines()
        self.containers = containers = []
        self.doors = doors = []
        self.specials = specials = defaultdict(list)
        BL=Blocks

        for y in range(HEIGHT):
            for x in range(79):
                char = _map[y][x]
                loc = Loc(x,y)
                if char != BL.blank:
                    if char==BL.rock:
                        self.put(BL.rock, loc)
                    elif char==Blocks.door:
                        d = Item(Blocks.door, 'door', loc, self._map)
                        doors.append(d)

                    elif char=='s':
                        Item(Blocks.sunflower, 'sunflower', loc, self._map)

                    elif char==Blocks.sharp_rock:
                        Item(Blocks.sharp_rock, 'sharp_rock', loc, type=Type.deadly, board_map=self._map)

                    elif char == BL.snowman:
                        Item(char, 'snowman', loc, self._map)
                    elif char == BL.snowflake:
                        Item(char, 'snowflake', loc, self._map)

                    elif char==Blocks.rock3:
                        Item(Blocks.rock3, 'rock', loc, type=Type.blocking, board_map=self._map)

                    elif char==Blocks.cactus:
                        Item(Blocks.cactus, 'cactus', loc, self._map)

                    elif char==Blocks.water:
                        Item(Blocks.water, 'water', loc, type=Type.water, board_map=self._map)

                    elif char==Blocks.tulip:
                        Item(Blocks.tulip, 'tulip', loc, self._map)

                    elif char==Blocks.fountain:
                        Item(Blocks.fountain, 'water fountain basin', loc, self._map)

                    elif char in (BL.books, BL.open_book):
                        Item(char, 'books', loc, self._map)

                    elif char in (Blocks.tree1, Blocks.tree2):
                        Item(char, 'tree', loc, self._map)

                    elif char==Blocks.rock2:
                        Item(char, '', loc, self._map)

                    elif char==Blocks.soldier:
                        Being(loc, name='Soldier', char=BL.soldier, board_map=self._map)

                    elif char in '0123456789':
                        specials[int(char)] = loc
                        if for_editor:
                            self.put(char, loc)
        return containers, doors, specials

    def board_1(self):
        self.load_map('1')
        # Being(self.specials[1], name='Hero1', char=Blocks.hero1, board_map=self._map)
        Hero(self.specials[1], '1', name='Ardor', char=Blocks.hero1, id=ID.hero1)

    def draw(self, win):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                # tricky bug: if an 'invisible' item put somewhere, then a being moves on top of it, it's drawn, but
                # when it's moved out, the invisible item is drawn, but being an empty string, it doesn't draw over the
                # being's char, so the 'image' of the being remains there, even after being moved away.
                cell = [c for c in cell if str(c)]
                a = last(cell)
                if isinstance(a, int):
                    a = Objects[a]
                win.addstr(y,x, str(a))
        for y,x,txt in self.labels:
            win.addstr(y,x,txt)
        for loc, col in self.colors:
            win.addstr(loc.y, loc.x, str(self[loc]), curses.color_pair(col))
        win.refresh()
        if Windows.win2:
            Windows.win2.addstr(0,74, str(self._map))

    def put(self, obj, loc=None):
        """
        If loc is not given, try to use obj's own location attr.
        If loc IS given, update obj's own location attr if possible.
        """
        loc = loc or obj.loc
        if not isinstance(obj, (int, str)):
            obj.board_map = self._map
            obj.loc = loc
        try:
            self.B[loc.y][loc.x].append(getattr(obj, 'id', None) or obj)
        except Exception as e:
            sys.stdout.write(str(loc))
            raise

    def is_blocked(self, loc):
        for x in self.get_all(loc):
            if isinstance(x, int):
                x = objects[x]
            if x in BLOCKING or getattr(x, 'type', None) in BLOCKING:
                return True
        return False

def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

class Boards:
    pass

class BeingItemMixin:
    is_player = 0
    state = 0

    def tele(self, loc):
        self.B.remove(self)
        self.put(loc)

    def put(self, loc):
        self.loc = loc
        B=self.B
        B.put(self)

    def has(self, id):
        return self.inv.get(id)

    def remove1(self, id):
        self.inv[id] -= 1

    def add1(self, id, n=1):
        self.inv[id] += n

    def move_to_board(self, _map, specials_ind=None, loc=None):
        to_B = getattr(Boards, _map)
        if specials_ind is not None:
            loc = to_B.specials[specials_ind]
        self.B.remove(self)
        self.loc = loc
        to_B.put(self)
        self.board_map = to_B._map
        return to_B

    @property
    def B(self):
        if self.board_map:
            print("self.board_map", self.board_map)
            return getattr(Boards, 'b_'+self.board_map)


class Item(BeingItemMixin):
    board_map = None

    def __init__(self, char, name, loc=None, board_map=None, put=True, id=None, type=None):
        self.char, self.name, self.loc, self.board_map, self.id, self.type = char, name, loc, board_map, id, type
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if board_map and put:
            self.B.put(self)

    def __str__(self):
        return self.char

    def __repr__(self):
        return f'<I: {self.char}>'

    def move(self, dir, n=1):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        for _ in range(n):
            new = self.loc.mod(*m)
            self.B.remove(self)
            self.loc = new
            self.B.put(self)


class Being(BeingItemMixin):
    n = None
    is_being = 1
    type = None
    char = None

    def __init__(self, loc=None, board_map=None, put=True, id=None, name=None, state=0, n=1, char='?'):
        self.id, self.loc, self.board_map, self.name, self.state, self.n  = id, loc, board_map, name, state, n
        self.char = self.char or char
        self.inv = defaultdict(int)
        print("id", id)
        if id:
            Objects[id] = self
        if board_map and put:
            self.B.put(self)

    def __str__(self):
        return self.char

    def talk(self, being, dialog=None, yesno=False, resp=False):
        being = objects.get(being) or being
        loc = being.loc
        if isinstance(dialog, str):
            dialog = [dialog]
        x = min(loc.x, 60)
        multichoice = 0

        for m, txt in enumerate(dialog):
            lst = []
            if isinstance(txt, (list,tuple)):
                multichoice = len(txt)
                for n, t in enumerate(txt):
                    lst.append(f'{n+1}) {t}')
                txt = '\n'.join(lst)
            x = min(40, x)
            w = 78 - x
            lines = (len(txt) // w) + 4
            txt = wrap(txt, w)
            txt = '\n'.join(txt)
            offset_y = lines if loc.y<8 else -lines

            y = max(0, loc.y+offset_y)
            win = newwin(lines+2, w+2, y, x)
            win.addstr(1,1, txt + (' [Y/N]' if yesno else ''))

            if yesno:
                # TODO in some one-time dialogs, may need to detect 'no' explicitly
                k = win.getkey()
                del win
                return k in 'Yy'

            elif multichoice:
                for _ in range(2):
                    k = win.getkey()
                    try:
                        k=int(k)
                    except ValueError:
                        k = 0
                    if k in range(1, multichoice+1):
                        del win
                        return k

            if resp and m==len(dialog)-1:
                i=''
                for _ in range(10):
                    k=win.getkey()
                    if k=='\n': break
                    i+=k
                    status(i)
                    Windows.win2.refresh()
                del win
                return i

            win.getkey()
            del win
            self.B.draw(Windows.win)
            Windows.win2.clear()
            Windows.win2.refresh()

    def _move(self, dir):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[dir]
        if chk_oob(self.loc, *m):
            return True, self.loc.mod(*m)
        else:
            if chk_b_oob(self.B.loc, *m):
                return LOAD_BOARD, self.B.loc.mod(*m)
        return 0, 0

    def move(self, dir):
        B = self.B
        rv = self._move(dir)
        if rv and (rv[0] == LOAD_BOARD):
            return rv
        new = rv[1]
        if new and isinstance(B[new], Being):
            self.attack(B[new])
            return True, True

        # TODO This is a little messy, doors are by type and keys are by ID
        if new and B.found_type_at(Type.door1, new):
            d = B[new]
            cas = Objects[d.id]
            if cas.player == self.player:
                cas.build_ui()
            else:
                cas.battle_ui()
            return None, None

        if new and B.is_blocked(new):
            new = None

        if new:
            print(f'removing from {self.loc}')
            B.remove(self)
            if new[0] == LOAD_BOARD or new[0] is None:
                return new
            self.loc = new
            self.put(new)
            Windows.win2.refresh()
            return True, True
        return None, None

    def handle_player_move(self, new):
        B=self.B
        pick_up = []
        top_obj = B.get_top_obj(new)
        items = B.get_all_obj(new)
        if top_obj:
            if isinstance(top_obj, int):
                top_obj = Objects[top_obj.id]

        for x in reversed(items):
            if x.id == ID.gold:
                self.gold += 1
                B.remove(x, new)
            elif x.id in pick_up:
                self.inv[x.id] += 1
                B.remove(x, new)

        names = [o.name for o in B.get_all_obj(new) if o.name]
        plural = len(names)>1
        names = ', '.join(names)
        if names:
            a = ':' if plural else ' a'
            status(f'You see{a} {names}')

    def attack(self, obj):
        if abs(self.loc.x - obj.loc.x) <= 1 and \
           abs(self.loc.y - obj.loc.y) <= 1:
                self.battle_ui(obj)

    def hit(self, obj):
        B=self.B
        if obj.health:
            obj.health -= 1
            status(f'{self} hits {obj} for 1pt')
            if obj.health <=0:
                B.remove(obj)

    def loot(self, cont):
        items = {k:v for k,v in cont.inv.items() if v}
        lst = []
        for x in items:
            if x==ID.gold:
                self.gold+=1
            else:
                self.inv[x] += cont.inv[x]
            cont.inv[x] = 0
            lst.append(str(objects[x]))
        status('You found {}'.format(', '.join(lst)))
        if not items:
            status(f'{cont.name} is empty')

    def action(self):
        B=self.B
        cont = last( [x for x in B.get_all_obj(self.loc) if x.type==Type.container] )

        r,l = self.loc.mod_r(), self.loc.mod_l()
        rd, ld = r.mod_d(), l.mod_d()
        locs = [self.loc]

        if chk_oob(r): locs.append(r)
        if chk_oob(l): locs.append(l)
        if chk_oob(rd): locs.append(rd)
        if chk_oob(ld): locs.append(ld)

        def is_near(id):
            return getattr(ID, id) in B.get_ids(locs)

        if cont:
            self.loot(cont)

    def use(self):
        win = newwin(len(self.inv), 40, 2, 10)
        ascii_letters = string.ascii_letters
        for n, (id,qty) in enumerate(self.inv.items()):
            item = Objects[id]
            win.addstr(n,0, f' {ascii_letters[n]}) {item.name:4} - {qty} ')
        ch = win.getkey()
        item = None
        if ch in ascii_letters:
            try:
                item_id = list(self.inv.keys())[string.ascii_letters.index(ch)]
            except IndexError:
                return
        if not item_id: return

        status('Nothing happens')

    @property
    def alive(self):
        return self.health>0

    @property
    def dead(self):
        return not self.alive


class Hero(Being):
    def __init__(self, *args, player=None ,**kwargs ):
        super().__init__(*args, **kwargs)
        self.player = player

    def __str__(self):
        return self.char

    def __repr__(self):
        return f'<H: {self.name} ({self.player})>'


class Saves:
    saves = {}
    loaded = 0

    def load(self, name):
        global Objects
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        self.saves = sh['saves']
        s = self.saves[name]
        boards[:] = s['boards']
        Objects = s['objects']
        player = objects[ID.player]
        loc = player.loc
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        return player, B

    def save(self, cur_brd, name=None):
        if not name:
            for n in range(1,999):
                fn = f'saves/{n}.data'
                name = str(n)
                if not os.path.exists(fn+'.db'):
                    break
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        s = {}
        s['boards'] = boards
        s['cur_brd'] = cur_brd
        s['objects'] = objects
        s['done_events'] = done_events
        player = obj_by_attr.player
        bl = cur_brd
        B = boards[bl.y][bl.x]
        sh['saves'] = {name: s}
        sh.close()
        return B.get_all(player.loc), name



def main(stdscr, load_game):
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

    Boards.b_1 = Board(Loc(0,0), '1')
    Boards.b_1.board_1()
    board_grid[:] = [
        ['1'],
    ]
    Misc.B = Boards.b_1
    Misc.player = Player('green', False)

    # def __init__(self, loc=None, board_map=None, put=True, id=None, name=None, state=0, n=1, char='?'):
    Misc.hero = Objects.hero1
    ok=1
    Misc.B.draw(win)
    while ok:
        ok=handle_ui()

def handle_ui():
    win, win2 = Windows.win, Windows.win2
    k = win.getkey()
    win2.clear()
    win2.addstr(1,0, ' '*78)
    win2.addstr(2,0,k)
    hero = Misc.hero
    if k=='q':
        return 0

    elif k in 'yubnhjkl':
        rv = hero.move(k)

        if rv[0] == LOAD_BOARD:
            loc = rv[1]
            x, y = hero.loc
            if k=='l': x = 0
            if k=='h': x = 78
            if k=='k': y = 15
            if k=='j': y = 0

            # ugly but....
            p_loc = Loc(x, y)
            if chk_b_oob(loc):
                Misc.B = hero.move_to_board(boards[loc.y][loc.x]._map, loc=p_loc)

    elif k == '.':
        pass
    elif k == 'o':
        name = prompt(win2)
        hero, B = Saves().load(name)
    elif k == 's':
        name = prompt(win2)
        Saves().save(Misc.B.loc, name)
        status(f'Saved game as "{name}"')
        Windows.win2.refresh()
    elif k == 'v':
        status(str(hero.loc))
    elif k == ' ':
        hero.action()
    elif k == '5' and DBG:
        k = win.getkey()
        k+= win.getkey()
        try:
            print(Misc.B.B[int(k)])
            status(f'printed row {k} to debug')
        except:
            status('try again')
    elif k == 't' and DBG:
        # debug teleport
        k = ''
        while 1:
            k+=win.getkey()
            status(k)
            win2.refresh()
            if k.endswith(' '):
                try:
                    x,y=k[:-1].split(',')
                    hero.tele(Loc(int(x), int(y)))
                except Exception as e:
                    print(e)
                break

    # -----------------------------------------------------------------------------------------------

    elif k == 'u':
        hero.use()

    elif k == 'E':
        Misc.B.display(str(Misc.B.get_all(hero.loc)))
    elif k == 'i':
        txt = []
        for id, n in hero.inv.items():
            item = objects[id]
            if item and n:
                txt.append(f'{item.name} {n}')
        Misc.B.display(txt)

    Misc.B.draw(win)
    win2.addstr(0,0, f'[Gold:{Misc.player.gold}]')
    win2.refresh()
    return 1


def editor(stdscr, _map):
    Misc.is_game = 0
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    curses.curs_set(True)
    loc = Loc(40, 8)
    brush = None
    written = 0
    Boards.b_1 = B = Board(Loc(0,0), _map)
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

def status(msg):
    Windows.win2.addstr(2,0,msg)

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
