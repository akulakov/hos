#!/usr/bin/env python
from bearlibterminal import terminal as blt
import os
import sys
import math
from random import choice, randrange, random
from collections import defaultdict
from textwrap import wrap
from time import sleep
import string
import shelve
from copy import copy  #, deepcopy
from enum import Enum, auto

"""
HoS
"""

HEIGHT = 16
WIDTH = 38
AUTO_BATTLE = 11
END_MOVE=900

SLP = 0.01
SEQ_TYPES = (list, tuple)
debug_log = open('debug', 'w')
board_grid = []
castle_boards = {}
ai_heroes = []
ai_buildings = []
player_heroes = []
player_buildings = []
players = []
castles = []

keymap = dict(
    [
    [ blt.TK_ESCAPE, 'ESCAPE' ],
    [ blt.TK_RETURN, 'ENTER' ],
    [ blt.TK_PERIOD, "." ],
    [ blt.TK_SHIFT, 'SHIFT' ],
    [ blt.TK_UP, "UP" ],
    [ blt.TK_DOWN, "DOWN" ],
    [ blt.TK_RIGHT, "RIGHT" ],
    [ blt.TK_LEFT, "LEFT" ],

    [ blt.TK_MOUSE_LEFT, "CLICK" ],

    [ blt.TK_Q, 'q' ],
    [ blt.TK_W, 'w' ],
    [ blt.TK_E, 'e' ],
    [ blt.TK_R, 'r' ],
    [ blt.TK_T, 't' ],
    [ blt.TK_Y, 'y' ],
    [ blt.TK_U, 'u' ],
    [ blt.TK_I, 'i' ],
    [ blt.TK_O, 'o' ],
    [ blt.TK_P, 'p' ],
    [ blt.TK_A, 'a' ],
    [ blt.TK_S, 's' ],
    [ blt.TK_D, 'd' ],
    [ blt.TK_F, 'f' ],
    [ blt.TK_G, 'g' ],
    [ blt.TK_H, 'h' ],
    [ blt.TK_J, 'j' ],
    [ blt.TK_K, 'k' ],
    [ blt.TK_L, 'l' ],
    [ blt.TK_Z, 'z' ],
    [ blt.TK_X, 'x' ],
    [ blt.TK_C, 'c' ],
    [ blt.TK_V, 'v' ],
    [ blt.TK_B, 'b' ],
    [ blt.TK_N, 'n' ],
    [ blt.TK_M, 'm' ],

    [ blt.TK_1, '1' ],
    [ blt.TK_2, '2' ],
    [ blt.TK_3, '3' ],
    [ blt.TK_4, '4' ],
    [ blt.TK_5, '5' ],
    [ blt.TK_6, '6' ],
    [ blt.TK_7, '7' ],
    [ blt.TK_8, '8' ],
    [ blt.TK_9, '9' ],
    [ blt.TK_0, '0' ],

    [ blt.TK_COMMA, ',' ],
    [ blt.TK_SPACE, ' ' ],
    [ blt.TK_MINUS, '-' ],
    [ blt.TK_EQUALS, '=' ],
    [ blt.TK_SLASH, '/' ],
    ]
    )

noto_tiles = """fountain
sailboat
snowman
snowflake
water
tree1
tree2
palm
cactus
flower1
flower2
flower3
flower4
flower5
leaf1
leaf2
leaf3
guitar
trumpet
monkey
elephant
soldier
card
chair
PC
sharp-rock1
sharp-rock2
book1
book2
book3
book4
book5
key
seal
truck
ship
flag
man
girl
door
bull
cow
""".split()
noto_tiles = {k: 0xe300+n for n,k in enumerate(noto_tiles)}

class ObjectsClass:
    def __init__(self):
        self.objects = {}

    def __setitem__(self, k, v):
        self.objects[getattr(ID, k)] = v

    def __getitem__(self, k):
        return self.objects[getattr(ID, k)]

    def __getattr__(self, k):
        return self.objects[getattr(ID, k)]

    def get(self, k, default=None):
        id = getattr(ID, k, None)
        return self.objects.get(id)

    def get_by_id(self, id):
        return self.objects.get(id)

    def set_by_id(self, id, v):
        self.objects[id] = v

Objects = ObjectsClass()

class ID(Enum):
    castle1 = auto()
    castle2 = auto()
    castle3 = auto()
    castle4 = auto()
    castle5 = auto()

    hero1 = auto()
    hero2 = auto()
    hero3 = auto()
    hero4 = auto()
    hero5 = auto()
    hero6 = auto()
    hero7 = auto()
    hero8 = auto()
    hero9 = auto()
    hero10 = auto()

    power_bolt = auto()
    shield_spell = auto()

    gold = auto()
    wood = auto()
    ore = auto()
    mercury = auto()
    sulphur = auto()

    raised_platform = auto()

hero_names = {ID.hero1:'Arcachon', ID.hero2:'Carcassonne', ID.hero3:'Troyes', ID.hero4:'Sault'}

class Player:
    resources = {
        ID.gold: 3000,
        ID.wood: 20,
        ID.ore: 20,
        ID.mercury: 0,
        ID.sulphur: 0,
    }

    def __init__(self, name, is_ai, color):
        self.name, self.is_ai, self.color = name, is_ai, color
        self.is_human = not is_ai
        self._heroes = []
        self._castles = []

    def __repr__(self):
        return f'<P: {self.name}>'

    @property
    def heroes(self):
        l = (Objects.get_by_id(id) for id in self._heroes)
        return (h for h in l if h.alive)

    @property
    def castles(self):
        return (Objects.get_by_id(id) for id in self._castles)


class Type(Enum):
    door1 = auto()
    container = auto()
    blocking = auto()
    gate = auto()
    castle = auto()
    peasant = auto()
    pikeman = auto()
    cavalier = auto()
    archer = auto()
    griffin = auto()
    centaur = auto()

    melee_attack = auto()
    magic_attack = auto()

    hero = auto()
    building = auto()
    raised_platform = auto()

class Blocks:
    """All game tiles."""
    jousting_ground = '\u25ed'
    archers_tower = '\u0080'
    griffin_tower = '\u0081'
    centaur_stables = '\u0082'

    cavalier_l = '\u0007'
    cavalier_r = '\u0008'
    archer_r = '\u000c'
    archer_l = '\u000b'
    griffin_r = '\u000e'
    griffin_l = '\u000f'

    centaur_l = '\u0011'
    centaur_r = '\u0012'

    arrow_r = '\u20e9'
    arrow_l = '\u20ea'
    gold = '\u009e'
    sawmill = '\u0239'

    large_circle = '\u20dd'
    shield_spell = '\u0709'
    button_platform = '\u20e3'

    bricks = '\u2687'

    blank = '.'
    rock = '█'
    door = '⌸'
    water = '≋'
    tree1 = '\u2689'
    tree2 = '\u268a'
    rock2 = '▅'
    rock3 = '░'
    peasant = '\u23f2'
    pikeman = '\u23f3'
    hero1_l = '\u0003'
    hero1_r = '\u0004'
    rubbish = '⛁'
    cursor = '𐌏'
    hut = '△'
    guardhouse = '⌂'
    sub_plus = '\u208a'

    sub = [
            '\u2080',
            '₁',
            '₂',
            '₃',
            '₄',
            '₅',
            '₆',
            '₇',
            '₈',
            '₉'
          ]

    sub2 = [
           '\u20bb',
           '\u20bc',
           '\u20bd',
           '\u20be',
           '\u20bf',
           '\u20c0',
           '\u20c1',
           '\u20c2',
           '\u20c3',
           '\u20c4',
          ]

    list_select = '▶'
    hero_select = '\u2017'

    # spells
    bolt1 = '\u16ca'
    bolt2 = '\u16cb'
    spell_select = '\u229b'

BLOCKING = [Blocks.rock, Type.door1, Type.blocking, Type.gate, Type.castle]

class Misc:
    day = 1
    week = 1
    status = []
    current_unit = None
    player = None
    hero = None

def mkcell():
    return [Blocks.blank]

def mkrow():
    return [mkcell() for _ in range(WIDTH)]

def first(x):
    x=tuple(x)
    return x[0] if x else None
def last(x):
    x=tuple(x)
    return x[-1] if x else None

def chk_oob(loc, x=0, y=0):
    return _chk_oob(loc,x,y)[0]

def _chk_oob(loc, x=0, y=0):
    """Returns OOB, and also which axis is OOB (returns False for OOB, True for ok)."""
    Y, X = (0 <= loc.y+y <= HEIGHT-1,
            0 <= loc.x+x <= WIDTH-1)
    return X and Y, X, Y

def chk_b_oob(loc, x=0, y=0):
    h = len(board_grid)
    w = len(board_grid[0])
    newx, newy = loc.x+x, loc.y+y
    return 0 <= newy <= h-1 and 0 <= newx <= w-1

def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

def blt_put_obj(obj, loc=None):
    x,y=loc or obj.loc
    x = x*2 +(0 if y%2==0 else 1)
    blt.clear_area(x,y,1,1)
    puts(x, y, obj)
    refresh()

def pad_none(lst, size):
    return lst + [None]*(size-len(lst))

def dist(a,b):
    a = getattr(a,'loc',a)
    b = getattr(b,'loc',b)
    return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.x-b.x)*(a.y-b.y))

def getitem(it, ind=0, default=None):
    try: return it[ind]
    except IndexError: return default

def puts(x, y, text):
    _puts(x, y, text)

def puts2(x, y, text):
    _puts(x, y+HEIGHT, text)

def _puts(x,y,a):
    if isinstance(a,str):
        blt.puts(x,y,a)
    elif a._str:
        # combined glyps
        for _s in a._str():
            if a.color:
                _s = f'[color={a.color}]{_s}[/color]'
            blt.puts(x,y,_s)
    else:
        if a.color:
            a = f'[color={a.color}]{a}[/color]'
        blt.puts(x,y,str(a))

def refresh():
    blt.refresh()

def get_and_parse_key():
    while 1:
        k = parsekey(blt.read())
        if k!='SHIFT':
            return k

def parsekey(k):
    b=blt
    valid = (b.TK_RETURN, b.TK_SHIFT, b.TK_ESCAPE, b.TK_UP, b.TK_DOWN, b.TK_RIGHT, b.TK_LEFT, b.TK_MOUSE_LEFT)
    if k and blt.check(blt.TK_WCHAR) or k in valid:
        k = keymap.get(k)
        if k and blt.state(blt.TK_SHIFT):
            k = k.upper()
            if k=='-': k = '_'
            if k=='/': k = '?'
            if k=='=': k = '+'
        return k

def get_mouse_pos():
    return blt.state(blt.TK_MOUSE_X), blt.state(blt.TK_MOUSE_Y)

def board_setup():
    Boards.b_1 = Board(Loc(0,0), '1')
    Boards.b_1.board_1()
    Boards.b_2 = Board(Loc(1,0), '2')
    Boards.b_2.board_2()

    Boards.b_3 = Board(Loc(0,1), '3')
    Boards.b_3.board_3()
    Boards.b_4 = Board(Loc(1,1), '4')
    Boards.b_4.board_4()

    board_grid[:] = [
        ['1', '2', None],
        ['3', '4', None],
    ]
    Misc.B = Boards.b_1


def manage_castles():
    l = [Objects.get_by_id(id) for id in castles]
    p_castles = [c for c in l if c.player==Misc.player]
    if not p_castles:
        Misc.hero.talk(Misc.hero, 'You have no castles!')
        return
    x, y = 5, 1
    ascii_letters = string.ascii_letters

    lst = []
    for n, c in enumerate(p_castles):
        lst.append(f' {ascii_letters[n]}) {c.name}')
    w = max(len(l) for l in lst)
    blt.clear_area(x, y, w+2, len(lst))
    for n, l in enumerate(lst):
        puts(x, y+n, l)

    refresh()
    ch = get_and_parse_key()
    if ch and ch in ascii_letters:
        try:
            castle = p_castles[string.ascii_letters.index(ch)]
        except IndexError:
            return
        castle.town_ui()


def stats(castle=None, battle=False):
    pl = Misc.player
    if not pl: return
    h = Misc.hero
    if battle and Misc.current_unit:
        u = Misc.current_unit
        move, speed = u.cur_move, u.speed
    elif h:
        move, speed = h.cur_move, h.speed
    res = pl.resources
    s=''
    for r in 'gold wood ore mercury sulphur'.split():
        id = getattr(ID, r)
        s+= f'[{r.title()}:{res.get(id)}]'
    st = s + f' | Move {move}/{speed} | {Misc.B._map}'
    x = len(st)+2
    puts2(1,0,blt_esc(st))
    puts2(x,0, h.name)
    x+= len(h.name) + 2
    y = 1
    if castle:
        x = 1
        for a in castle.army:
            puts2(x+1 if a else x,
                  y,
                  a or blt_esc('[ ]')
                 )
            x+=3
        y+=1

    x = 1
    for a in h.army:
        puts2(x+1 if a else x,
              y,
              a or blt_esc('[ ]'))
        x+=3
    puts2(x+2, y, f'w{Misc.week}/d{Misc.day}')
    refresh()

def status(msg):
    Misc.status.append(msg)

def blt_esc(txt):
    return txt.replace('[','[[').replace(']',']]')

def prompt():
    mp = ''
    status('> ')
    blt.refresh()
    while 1:
        k = get_and_parse_key()
        if not k: continue
        if k=='ENTER':
            return mp
        mp += k
        status('> '+mp)
        blt.refresh()
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

    def __hash__(self):
        return hash(tuple(self))

    def mod(self, x=0, y=0):
        new = copy(self)
        new.y += y
        new.x += x
        return new

    def mod_r(self, n=1):
        return self.mod(n, 0)

    def mod_l(self, n=1):
        return self.mod(-n, 0)

    def mod_d(self, n=1):
        return self.mod(0, n)

    def mod_u(self, n=1):
        return self.mod(0, -n)


class Board:
    """Game board (single screen)."""
    def __init__(self, loc, _map):
        self.clear()
        self.labels = []
        self.loc = loc
        self._map = str(_map)

    def __repr__(self):
        return f'<B: {self._map}>'

    def __getitem__(self, loc):
        o = self.B[loc.y][loc.x][-1]
        if isinstance(o,int):
            o = Objects.get_by_id(o)
        return o

    def __iter__(self):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                yield Loc(x,y), cell

    def gen_graph(self, tgt):
        self.g = {}
        for loc, _ in self:
            if not self.is_blocked(loc):
                self.g[loc] = [n for n in self.neighbours(loc)
                               if (not self.is_blocked(n) and not self.get_being(n))
                                   or n==tgt
                              ]

    def next_move_to(self, src, tgt):
        p = self.find_path(src, tgt)
        return first(p)

    def find_path(self, src, tgt):
        """Greedy"""
        self.gen_graph(tgt)
        cur = src
        path = []
        visited = set([src])
        while 1:
            nbr = [n for n in self.g[cur] if n not in visited]
            next = first(sorted([(dist(n,tgt), id(n), n) for n in nbr]))
            if not next:
                break
            next = next[2]
            path.append(next)
            visited.add(next)
            cur = next
            if cur == tgt:
                return path
        return []


    def random_empty(self):
        while 1:
            loc = choice(list(self))[0]
            if self[loc] is Blocks.blank:
                return loc

    def random_rocks(self, n=1):
        for _ in range(n):
            Item(Blocks.rock, '', self.random_empty(), self._map, type=Type.blocking)

    def clear(self):
        self.B = [mkrow() for _ in range(HEIGHT)]

    def found_type_at(self, type, loc):
        def get_obj(x):
            return Objects.get_by_id(x) or x
        return any(
            get_obj(x).type==type for x in self.get_all_obj(loc)
        )

    def get_all(self, loc):
        return [n for n in self.B[loc.y][loc.x]
                if n!=Blocks.blank
               ]

    def remove(self, obj, loc=None):
        loc = loc or obj.loc
        cell = self.B[loc.y][loc.x]
        cell.remove(obj if obj in cell else obj.id)

    def get_all_obj(self, loc):
        return [Objects.get_by_id(n) or n for n in self.B[loc.y][loc.x]
                if not isinstance(n, str)
               ]

    def get_being(self, loc):
        return first(o for o in self.get_all_obj(loc) if isinstance(o, Being) and o.alive)

    def load_map(self, map_num, for_editor=0, castle=None):
        _map = open(f'maps/{map_num}.map').readlines()
        self.containers = containers = []
        self.doors = doors = []
        self.specials = specials = defaultdict(list)
        self.buildings = []
        BL=Blocks

        for y in range(HEIGHT):
            for x in range(WIDTH):
                char = _map[y][x*2 + (0 if y%2==0 else 1)]
                loc = Loc(x,y)
                if char != BL.blank:
                    if char==BL.rock:
                        Item(Blocks.rock, '', loc, self._map, type=Type.blocking)

                    elif char==Blocks.door:
                        d = Item(Blocks.door, 'door', loc, self._map)
                        doors.append(d)

                    elif char==Blocks.rock3:
                        Item(Blocks.rock3, 'rock', loc, type=Type.blocking, board_map=self._map)

                    elif char==Blocks.water:
                        Item(Blocks.water, 'water', loc, type=Type.water, board_map=self._map)

                    # elif char in (BL.book1, BL.book2):
                    #     Item(char, 'books', loc, self._map)

                    elif char in (Blocks.tree1, Blocks.tree2):
                        col = '#ff33%s%s' % (
                            hex(randrange(60,255))[2:],
                            hex(randrange(10,140))[2:],
                        )
                        Item(char, 'tree', loc, self._map, type=Type.blocking, color=col)

                    elif char == Blocks.bricks:
                        x = randrange(50,100)
                        col = '#ff%s%s%s' % (
                            hex(x)[2:], hex(x)[2:], hex(x)[2:],
                        )
                        Item(char, '', loc, self._map, type=Type.blocking, color=col)

                    elif char==Blocks.rock2:
                        Item(char, '', loc, self._map)

                    # elif char==Blocks.soldier:
                    #     Being(loc, name='Soldier', char=BL.soldier, board_map=self._map)

                    elif char in '0123456789':
                        specials[int(char)] = loc
                        if for_editor:
                            self.put(char, loc)
        return containers, doors, specials

    def board_1(self):
        self.load_map('1')
        Hero(self.specials[1], '1', name=hero_names[ID.hero1], char=Blocks.hero1_l, id=ID.hero1, player=Misc.player,
             army=[Archer(n=12), Pikeman(n=11), Griffin(n=13), Pikeman(n=14), Pikeman(n=15)])

        # Hero(self.specials[5], '1', name=hero_names[ID.hero3], char=Blocks.hero1_r, id=ID.hero3, player=Misc.player,
             # army=[Pikeman(n=3), Pikeman(n=4), Cavalier(n=2)])

        # Hero(self.specials[4], '1', name=hero_names[ID.hero2], char=Blocks.hero1_l, id=ID.hero2, player=Misc.blue_player,
        #      army=[Pikeman(n=1), Pikeman(n=1)])

        # Hero(self.specials[4].mod_r(2), '1', name=hero_names[ID.hero4], char=Blocks.hero1_l, id=ID.hero4, player=Misc.blue_player,
        #      army=[Pikeman(n=2), Peasant(n=5)])

        ResourceItem(Blocks.gold, 'gold', self.specials[6], self._map, id=ID.gold, n=100, color='yellow')
        Sawmill(self.specials[7], '1', player=Misc.player)

        Castle('Castle 1', self.specials[2], self._map, id=ID.castle1, player=Misc.blue_player, town_type=CastleTownType,
              army=[])
        Castle('Rampart Castle', self.specials[3], self._map, id=ID.castle2, player=Misc.blue_player, army=[],
               town_type=RampartTownType)

        IndependentArmy(Loc(11,10), '1', army=[Peasant(n=5)])
        IndependentArmy(Loc(11,12), '1', army=[Pikeman(n=5), Peasant(n=9)])

    def board_2(self):
        self.load_map('2')
        Castle('Castle 3', self.specials[1], self._map, id=ID.castle3, player=Misc.blue_player, army=[Peasant(n=1)],
               town_type=CastleTownType)

    def board_3(self):
        self.load_map('3')
        Castle('Castle 4', self.specials[1], self._map, id=ID.castle4, player=Misc.blue_player, army=[Peasant(n=5)],
               town_type=CastleTownType)

    def board_4(self):
        self.load_map('4')
        Castle('Castle 5', self.specials[1], self._map, id=ID.castle5, player=Misc.blue_player, army=[Pikeman(n=8)],
               town_type=CastleTownType)

    def board_siege(self):
        self.load_map('siege')
        sp = self.specials
        RaisedPlatform(Blocks.button_platform, '', sp[3], self._map)
        Gate(sp[8], name='Gate', board_map=self._map)
        Gate(sp[9], name='Gate', board_map=self._map)

    def screen_loc_to_map(self, loc):
        x,y=loc
        if y%2==1:
            x-=1
        x = int(round(x/2))
        return Loc(x,y)

    def draw(self, battle=False, castle=None):
        blt.clear()
        blt.color("white")
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                # tricky bug: if an 'invisible' item put somewhere, then a being moves on top of it, it's drawn, but
                # when it's moved out, the invisible item is drawn, but being an empty string, it doesn't draw over the
                # being's char, so the 'image' of the being remains there, even after being moved away.
                cell = [c for c in cell if getattr(c,'char',None)!='']
                a = last(cell)
                x*=2
                if y%2==1:
                    x+=1
                if isinstance(a, str):
                    puts(x,y,a)
                    continue
                if isinstance(a, ID):
                    a = Objects.get_by_id(a)
                puts(x,y,a)

        for y,x,txt in self.labels:
            puts(x,y,txt)
        stats(castle, battle=battle)
        for n, msg in enumerate(Misc.status):
            puts2(1, 2+n, msg)
            Misc.status = []
        refresh()

    def neighbours(self, loc):
        l = [loc.mod_r(), loc.mod_l(), loc.mod_u(), loc.mod_d()]
        if loc.y%2==0:
            l.extend([loc.mod_u().mod_l(), loc.mod_d().mod_l()])
        else:
            l.extend([loc.mod_u().mod_r(), loc.mod_d().mod_r()])
        return [loc for loc in l if chk_oob(loc)]

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
                x = Objects.get_by_id(x)
            if x in BLOCKING or getattr(x, 'type', None) in BLOCKING:
                return True
        return False


class Boards:
    @staticmethod
    def get_by_map(map):
        return getattr(Boards, 'b_'+map)

    @staticmethod
    def get_by_loc(loc):
        return board_grid[loc.y][loc.x]

class BeingItemCastleBase:
    is_player = 0
    is_hero = 0
    state = 0
    color = None
    _str = None
    castle = None
    player = None
    id = None
    hero = None

    def __init__(self, char, name, loc=None, board_map=None, put=True, id=None, type=None, color=None, n=0):
        self.char, self.name, self.loc, self.board_map, self.id, self.type, self.color, self.n = \
                char, name, loc, board_map, id, type, color, n
        if id:
            Objects.set_by_id(id, self)
        if board_map and put:
            self.B.put(self)

    def __str__(self):
        c=self.char
        if isinstance(c, int):
            c = '[U+{}]'.format(hex(c)[2:])
        return c

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
        to_B = getattr(Boards, 'b_'+_map)
        if specials_ind is not None:
            loc = to_B.specials[specials_ind]
        self.B.remove(self)
        self.loc = loc
        to_B.put(self)
        self.board_map = to_B._map
        return to_B

    def set_player(self, player):
        self.player = player
        if player:
            self.color = player.color
            if self in player_buildings:
                player_buildings.remove(self)
            if self.type==Type.building:
                player.resources[self.resource] += self.available
                self.available = 0
                (ai_buildings if self.player.is_ai else player_buildings).append(self)

    @property
    def B(self):
        if self.castle:
            return castle_boards[self.castle.name]
        if self.board_map:
            return getattr(Boards, 'b_'+self.board_map)


class Item(BeingItemCastleBase):
    board_map = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inv = defaultdict(int)

    def __repr__(self):
        return f'<I: {self.char}>'

    def move(self, dir, n=1):
        my,mx = dict(h=(0,-1), l=(0,1), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1))[dir]
        if mx==1 and my and self.loc.y%2==0:
            mx=0
        if mx==-1 and my and self.loc.y%2==1:
            mx=0
        m = my,mx
        for _ in range(n):
            new = self.loc.mod(m[1],m[0])
            self.B.remove(self)
            self.loc = new
            self.B.put(self)

class ResourceItem(Item):
    n = 0

class Arrow(Item):
    char = Blocks.arrow_l

class RaisedPlatform(Item):
    char = Blocks.button_platform
    id = ID.raised_platform

class TownType:
    building_types = None

class ArmyMixin:
    def total_strength(self):
        return sum(u.n*u.health for u in self.live_army())

    def army_is_dead(self):
        return all(not u or u.dead for u in self.army)

    def live_army(self):
        return list(u for u in filter(None, self.army) if u.alive)

class Castle(ArmyMixin, BeingItemCastleBase):
    weekly_income = 250
    current_hero = None
    type = Type.castle
    town_type = None

    def __init__(self, *args, player=None, army=None, town_type=None, **kwargs):
        super().__init__(Blocks.door, *args, **kwargs)
        self.army = pad_none(army or [], 6)
        self.town_type = town_type
        self.set_player(player)
        if player:
            player._castles.append(self.id)
        castles.append(self.id)
        self.type = Type.castle
        board = Board(None, 'town_ui')
        castle_boards[self.name] = board
        # this should happen after board is in `castle_boards` because buildings will get the board from there
        board.load_map('town_ui')

    def __repr__(self):
        return f'<C: {self.name}>'

    def is_ai(self):
        return not self.player or self.player.is_ai

    def ai_cast_spell(self, *args, **kwargs):
        pass

    def handle_day(self):
        if self.player:
            self.player.resources[ID.gold] += self.weekly_income
        if Misc.day==1:
            for b in self.board.buildings:
                b.available += b.growth

    @property
    def board(self):
        return castle_boards[self.name]

    def town_ui(self, hero=None):
        self.current_hero = hero
        while 1:
            self.board.draw(castle=self)
            # stats(self)
            k = get_and_parse_key()
            if k in ('q', 'ESCAPE'):
                break
            elif k=='r':
                self.recruit_ui()
            elif k=='R':
                self.recruit_all()
            elif k=='H':
                self.recruit_hero()
            elif k=='t':
                self.troops_ui()
            elif k=='b':
                BuildUI().go(self)

    def recruit_hero(self):
        if self.B.found_type_at(Type.hero, self.loc):
            h = self.current_hero
            h.talk(h, 'Cannot recruit a new hero: there is already a hero in this castle!')
            return

        lst = []
        for id, n in hero_names.items():
            if not Objects.get_by_id(id):
                lst.append((id, n))

        if not lst:
            Misc.hero.talk(Misc.hero, 'No more heroes for hire.')
            return
        x, y = 5, 1
        ascii_letters = string.ascii_letters

        new = []
        for n, (id, name) in enumerate(lst):
            new.append(f' {ascii_letters[n]}) {name}')

        w = max(len(l) for l in new)
        blt.clear_area(x, y, w+2, len(new))
        for n, l in enumerate(new):
            puts(x, y+n, l)

        refresh()
        ch = get_and_parse_key()
        if ch and ch in ascii_letters:
            try:
                id, name = lst[string.ascii_letters.index(ch)]
            except IndexError:
                return

            h = Hero(self.loc, self.B._map, name=name, char=Blocks.hero1_l, id=id, player=self.player)
            (ai_heroes if self.player.is_ai else player_heroes).append(h)

    def troops_ui(self):
        i = 0
        self.board.draw(castle=self)

        while 1:
            stats(self)
            blt.clear_area(5,5,60,10)
            h = self.current_hero

            puts(9 + i*3, 6, Blocks.cursor)

            x = y = 8
            for a in self.army:
                puts(x+1 if a else x,
                      y,
                      a or blt_esc('[ ]')
                     )
                x+=3
            y+=2

            x = 8
            for a in h.army:
                puts(x+1 if a else x,
                      y,
                      a or blt_esc('[ ]'))
                x+=3
            refresh()
            k = get_and_parse_key()
            if k in ('q', 'ESCAPE'):
                break
            elif k == 'DOWN' and self.army[i]:
                if blt.state(blt.TK_SHIFT):
                    self.army = self.merge_into_army(self.army, h.army)
                else:
                    self.army[i] = self.merge_into_army([self.army[i]], h.army)
            elif k == 'UP' and h.army[i]:
                if blt.state(blt.TK_SHIFT):
                    h.army = self.merge_into_army(h.army, self.army)
                else:
                    x = self.merge_into_army([h.army[i]], self.army)
                    h.army[i] = x

            elif k == 'LEFT':
                i-=1
                if i<0: i = 5
            elif k == 'RIGHT':
                i+=1
                if i>5: i = 0
        h.set_army_ownership()

    def merge_into_army(self, A, B):
        """Merge army A into B."""
        remains = []
        for a in filter(None, A):
            same_type = first([b for b in B if b and b.type==a.type])
            empty = first([n for n, b in enumerate(B) if not b])
            if same_type:
                same_type.n+= a.n
            elif empty is not None:
                B[empty] = a
            else:
                remains.append(a)

        if len(A)==1:
            return first(remains)
        else:
            return pad_none(remains, 6)


    def recruit_all(self):
        hero = self.current_hero
        for b in self.board.buildings:
            recruited = 0
            for _ in range(b.available):
                if not b.available or self.player.resources[ID.gold] < b.units.cost or not hero.can_merge(b.units.type):
                    break
                b.available-=1
                recruited+=1
                self.player.resources[ID.gold] -= b.units.cost
            self.merge_into_army([b.units(n=recruited)], hero.army)
        hero.set_army_ownership()

    def recruit_ui(self):
        recruited = defaultdict(int)
        # recruited = {}
        curs = 0
        self.board.draw(castle=self)
        B = self.board
        while 1:
            lst = [('', 'Unit', 'Available', 'Recruited')]
            for n, b in enumerate(B.buildings):
                x = Blocks.cursor if n==curs else ''
                lst.append((x, b.units.__name__, b.available, recruited[n]))

            x = Blocks.cursor if curs==len(self.board.buildings) else ''
            lst.append((x, 'ACCEPT', '', ''))
            blt.clear_area(5,5,60, len(B.buildings)+5)
            for n, (a,b,c,d) in enumerate(lst):
                puts(6, 6+n, a)
                puts(9, 6+n, str(b))
                puts(9+15, 6+n, str(c))
                puts(9+15+12, 6+n, str(d))
            refresh()

            k = get_and_parse_key()
            bld = getitem(B.buildings, curs)
            gold = self.player.resources[ID.gold]
            unit_cost = bld.units.cost if bld else 0

            if k in ('q', 'ESCAPE'):
                break

            elif k == 'DOWN':
                curs+=1
            elif k == 'UP':
                curs-=1

            elif not bld and k=='ENTER':
                for bld_n, n in recruited.items():
                    bld = B.buildings[bld_n]
                    if n:
                        for m, slot in enumerate(self.army):
                            if not slot:
                                self.army[m] = bld.units(n=n)
                                recruited[bld_n] = 0
                                break
                            elif slot.type==type:
                                slot.n+=n
                                recruited[bld_n] = 0
                                break

                # silently revert recruits who didn't fit in the slots
                for bld_n, n in recruited.items():
                    bld = B.buildings[bld_n]
                    if n:
                        bld.available += n
                        gold += bld.units.cost * n
                self.player.resources[ID.gold] = gold
                break

            elif k == 'LEFT' and bld and recruited[curs]:
                bld.available += 1
                recruited[curs] -= 1
                gold += unit_cost

            elif k == 'RIGHT' and bld and bld.available and unit_cost<=gold:
                bld.available -= 1
                recruited[curs] += 1
                gold -= unit_cost

            if curs<0:
                curs = len(B.buildings)
            if curs>len(B.buildings):
                curs = 0


class BuildUI:
    def go(self, castle):
        existing = [b.__class__ for b in castle.board.buildings]
        available = [b for b in castle.town_type.building_types if b not in existing]
        pl = castle.player
        new = []
        for b in available:
            req = ', '.join(f'{id.name}:{amt}' for id,amt in b.cost.items())
            new.append(f'{b.__name__}  {req}')

        if not available:
            Misc.hero.talk(Misc.hero, 'No buildings may be built.')
            return
        x, y = 5, 1
        ascii_letters = string.ascii_letters

        lst = []
        for n, b in enumerate(new):
            lst.append(f' {ascii_letters[n]}) {b}')
        w = max(len(l) for l in lst)
        blt.clear_area(x, y, w+2, len(lst))
        for n, l in enumerate(lst):
            puts(x, y+n, l)

        refresh()
        ch = get_and_parse_key()
        if ch and ch in ascii_letters:
            try:
                b = available[string.ascii_letters.index(ch)]
            except IndexError:
                return
            for id,amt in b.cost.items():
                if amt > pl.resources[id]:
                    Misc.hero.talk(Misc.hero, 'Not enough resources for this building')
                    return
            loc = castle.board.random_empty()
            bld = b(loc, 'town_ui', castle)
            castle.board.buildings.append(bld)


class BattleUI:
    def __init__(self, B):
        self.B=B

    def auto_battle(self, a, b):
        a_str = a.total_strength()
        b_str = b.total_strength()
        winner, loser, hp = (a,b,b_str) if a_str>b_str else (b,a,a_str)
        if winner.is_hero:
            winner.xp += loser.total_strength()//2
        for u in winner.live_army():
            if u.total_health < hp:
                u.n=0
                hp-=u.total_health
            else:
                n, health = divmod(hp, u.max_health)
                u.health = health
                u.n = n+1
        loser.army = pad_none([], 6)

    def go(self, a, b):
        self._go(a,b)
        a.army = pad_none(a.live_army(), 6)
        b.army = pad_none(b.live_army(), 6)
        Misc.B = self.B

    def _go(self, a, b):
        if a.is_hero: a.reset_mana()
        if b.is_hero: b.reset_mana()
        a._strength = a.total_strength()
        b._strength = b.total_strength()
        B = Misc.B = Boards.b_battle = Board(None, 'battle')
        if b.type == Type.castle:
            B.board_siege()
        else:
            B.load_map('battle')

        loc = B.specials[1]
        for u in a.live_army():
            B.put(u, loc)
            loc = loc.mod_d(2)
        loc = B.specials[2]
        for u in b.live_army():
            B.put(u, loc)
            loc = loc.mod_d(2)

        if b.type != Type.castle:
            B.random_rocks(20)

        B.draw(battle=1)
        while 1:
            self.cast_spell(B, a, b)
            B.draw(battle=1)
            for u in a.live_army():
                rv = self.handle_unit_turn(B, a, b, u)
                if rv==AUTO_BATTLE:
                    break
            self.handle_modifiers_turn(a)
            if self.check_for_win(a,b):
                break
            self.cast_spell(B, b, a)
            for u in b.live_army():
                rv = self.handle_unit_turn(B, b, a, u)
                if rv==AUTO_BATTLE:
                    break
            self.handle_modifiers_turn(b)
            if self.check_for_win(a,b):
                break

    def handle_modifiers_turn(self, hero):
        """Time-out modifiers."""
        for u in hero.live_army():
            rm = []
            for k, mod in u.modifiers.items():
                if mod[0] <= 0:
                    rm.append(k)
                else:
                    mod[0] -= 1
            for k in rm:
                del u.modifiers[k]

    def cast_spell(self, B, a, b):
        if a.is_ai():
            a.ai_cast_spell(B, b.live_army())
        else:
            a.cast_spell(B)

    def check_for_win(self, a, b):
        for hero, other in [(a,b),(b,a)]:
            if hero.army_is_dead():
                x = hero if hero.is_hero else other
                x.talk(x, f'{other} wins, gaining {hero._strength}XP!')     # `hero` may be a castle here
                if hero.is_hero:
                    # we don't remove if it's a castle
                    self.B.remove(hero)
                    hero.alive = 0

                if not hero.player or hero.player.is_ai:
                    other.add_xp(hero._strength)
                for u in other.live_army():
                    u.modifiers = defaultdict(lambda:[1,1])
                return True

    def handle_unit_turn(self, B, a, b, unit):
        h,u = a, unit
        hh = a if (a.player and not a.player.is_ai) else b
        Misc.current_unit = u   # for stats()
        while 1:
            if not u.alive:
                break
            if not h.is_ai():
                u.color = 'lighter blue'
                blt_put_obj(u)
                ok = handle_ui(u, hero=h)
                u.color = None
                if not ok:
                    return
                if ok==END_MOVE:
                    u.cur_move = u.speed
                    u.color=None
                    blt_put_obj(u)
                    break
                if ok==AUTO_BATTLE:
                    self.auto_battle(a, b)
                    return AUTO_BATTLE
            else:
                tgt = u.closest(hh.live_army())

                if tgt:
                    u.color = 'lighter blue'
                    blt_put_obj(u)
                    sleep(0.25)
                    path = u.path.get(tgt) or B.find_path(u.loc, tgt.loc)
                    if len(path)==1:
                        u.hit(tgt)
                    elif path:
                        u.move(loc=first(path))
                        u.path[tgt] = path[1:]
                    else:
                        return

                    # u.attack(tgt)
                    B.draw(battle=1)
                    if u.cur_move==0:
                        u.cur_move = u.speed
                        u.color=None
                        blt_put_obj(u)
                        break


class LoadBoard:
    def __init__(self, new, b_new):
        self.new, self.b_new = new, b_new

class Being(BeingItemCastleBase):
    n = None
    health = 1
    health = 1
    max_health = 1
    is_being = 1
    type = None
    char = None
    speed = None
    range_weapon_str = None
    modifiers = None
    path = None

    def __init__(self, loc=None, board_map=None, put=True, id=None, name=None, state=0, n=1, char='?',
                 color=None):
        self.id, self.loc, self.board_map, self._name, self.state, self.n, self.color  = id, loc, board_map, name, state, n, color
        self.char = self.char or char
        self.inv = defaultdict(int)
        self.cur_move = self.speed
        if id:
            Objects.set_by_id(id, self)
        if board_map and put:
            self.B.put(self)
        self.max_health = self.health
        self.modifiers = defaultdict(lambda:[1,1])
        self.path = {}


    def __str__(self):
        return super().__str__() if self.n>0 else Blocks.rubbish

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def talk(self, being, dialog=None, yesno=False, resp=False):
        """Messages, dialogs, yes/no, prompt for responce, multiple choice replies."""
        if isinstance(being, int):
            being = Objects.get(being)
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
            if yesno:
                txt += ' [[Y/N]]'
            lines = (len(txt) // w) + 4
            txt_lines = wrap(txt, w)
            txt = '\n'.join(txt_lines)
            offset_y = lines if loc.y<8 else -lines

            y = max(0, loc.y+offset_y)
            W = max(len(l) for l in txt_lines)
            blt.clear_area(x+1, y+1, W, len(txt_lines))
            puts(x+1,y+1, txt)
            refresh()

            if yesno:
                # TODO in some one-time dialogs, may need to detect 'no' explicitly
                k = get_and_parse_key()
                return k in 'Yy'

            elif multichoice:
                for _ in range(2):
                    k = get_and_parse_key()
                    try:
                        k=int(k)
                    except ValueError:
                        k = 0
                    if k in range(1, multichoice+1):
                        return k

            if resp and m==len(dialog)-1:
                i=''
                puts(0,1, '> ')
                refresh()
                for _ in range(10):
                    k = get_and_parse_key()
                    if k==' ': break
                    i+=k
                    puts(0,1, '> '+i)
                    refresh()
                return i

            refresh()
            k=None
            while k!=' ':
                k = get_and_parse_key()
            self.B.draw()


    def _move(self, dir):
        my,mx = dict(h=(0,-1), l=(0,1), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[dir]
        if mx==1 and my and self.loc.y%2==0:
            mx=0
        if mx==-1 and my and self.loc.y%2==1:
            mx=0
        m = mx,my

        # Here if for example we're going in down-right dir, and we're OOB in downwards direction, we want to switch to
        # the board below; if going in the same dir but we're OOB only in rightward dir, we want to switch to the board
        # to the right. If OOB in both dirs, go to the board to the down-right dir.
        ok, keepX, keepY = _chk_oob(self.loc, *m)
        if ok:
            return True, self.loc.mod(*m)
        else:
            if keepX: mx = 0
            if keepY: my = 0
            if chk_b_oob(self.B.loc, mx, my):
                x, y = self.loc.mod(mx, my)
                if keepY:
                    x = 0 if mx==1 else (WIDTH-1)
                if keepX:
                    y = 0 if my==1 else (HEIGHT-1)

                return LoadBoard(Loc(x,y), self.B.loc.mod(mx,my))
        return 0, 0

    def move(self, dir=None, attack=True, loc=None):
        if self.cur_move==0: return None, None
        B = self.B
        if dir:
            rv = self._move(dir)
            if isinstance(rv, LoadBoard):
                return rv
            new = rv[1]
        else:
            new = loc

        if new:
            being = B.get_being(new)
            if being and being.alive:
                if not attack:
                    return None

                self.handle_directional_turn(dir, new)
                if self.hero != being.hero or (self.is_hero and self.player!=being.player):
                    self.attack(being)
                if self.cur_move:
                    self.cur_move -= 1
                return True, True

        if new and B.found_type_at(Type.building, new):
            b = B[new]
            b.set_player(self.player)

        if new and B.found_type_at(Type.castle, new):
            cas = Objects.get_by_id(B[new])
            if cas.player==self.player or not cas.live_army():
                cas.set_player(self.player)
                if self.player.is_human:
                    cas.town_ui(self)
                else:
                    # enter town gate
                    B.remove(self)
                    self.put(new)
                    self.cur_move=0
            else:
                BattleUI(B).go(self, cas)
            return None, None

        if new and B.is_blocked(new):
            new = None

        if new:
            B.remove(self)
            if new[0] is None:
                return new
            self.handle_directional_turn(dir, new)
            self.loc = new
            self.put(new)
            refresh()
            if self.cur_move:
                self.cur_move -= 1
            if self.is_hero and self.player and not self.player.is_ai:
                self.handle_player_move(new)

            return True, True
        return None, None

    def handle_directional_turn(self, dir, loc):
        """Turn char based on which way it's facing."""
        if isinstance(self, (ArmyUnit, Hero)):
            name = self.__class__.__name__.lower()
            if self.is_hero: name = name+'1'
            if hasattr(Blocks, name+'_r'):
                to_r = False
                if loc:
                    to_r = loc.x>self.loc.x or (loc.x==self.loc.x and loc.y%2==1)
                to_l = not to_r
                if dir and dir in 'hyb' or to_l:
                    self.char = getattr(Blocks, name+'_l')
                else:
                    self.char = getattr(Blocks, name+'_r')

    def handle_player_move(self, new):
        B=self.B
        pick_up = [ID.gold]
        items = B.get_all_obj(new)
        top_obj = last(items)
        if top_obj:
            # why does this work with unicode offsets? maybe it doesn't..
            if isinstance(top_obj, int):
                top_obj = Objects[top_obj.id]

        for x in reversed(items):
            if x.id in pick_up:
                if self.player:
                    self.player.resources[x.id] += x.n
                B.remove(x, new)

        names = [o.name for o in B.get_all_obj(new) if o.name and o!=self]
        plural = len(names)>1
        names = ', '.join(names)
        if names:
            a = ':' if plural else ' a'
            status(f'You see{a} {names}')

    def dist_to(self, obj):
        pass

    def attack(self, obj):
        if obj.loc in self.B.neighbours(self.loc):
            if self.is_hero:
                BattleUI(self.B).go(self, obj)
                Misc.B = self.B
                self.cur_move = 0
            else:
                self.hit(obj)

    def get_dir(self, b):
        a = self.loc
        b = getattr(b, 'loc', None) or b
        if a.x<=b.x and a.y<b.y: return 'n'
        elif a.x<=b.x and a.y>b.y: return 'u'
        elif a.x>=b.x and a.y<b.y: return 'b'
        elif a.x>=b.x and a.y>b.y: return 'y'
        elif a.x<b.x: return 'l'
        elif a.x>b.x: return 'h'

    def hit(self, obj, ranged=False, dmg=None, mod=1, type=None, descr=''):
        if dmg:
            a = dmg
        else:
            str = self.strength if not ranged else self.range_weapon_str
            hero_mod = 1
            if self.hero:
                hero_mod += (self.hero.level * 5)/100

            a = int(round((str * self.n * hero_mod * mod)/3))

        b = obj.health + obj.max_health*(obj.n-1)
        a = obj.defend(a, type)
        c = b - a

        if descr:
            descr = f' with {descr}'
        if a:
            status(f'{self} hits {obj}{descr} for {a} HP')
        else:
            status(f'{self} fails to hit {obj}{descr}')

        if c <= 0:
            status(f'{obj} dies')
            obj.n = obj.health = 0
        else:
            n, health = divmod(c, obj.max_health)
            obj.health = health
            obj.n = n+1

        self.cur_move = 0

    def defend(self, dmg, type):
        x = 0
        if type==Type.melee_attack:
            x = self.n * self.modifiers['defense'][1]
        return dmg - x

    def action(self):
        def is_near(id):
            return getattr(ID, id) in self.B.get_ids(self.neighbours() + [self.loc])

    def use(self):
        """For spells maybe?"""
        ascii_letters = string.ascii_letters
        for n, (id,qty) in enumerate(self.inv.items()):
            item = Objects[id]
            puts(0,n, f' {ascii_letters[n]}) {item.name:4} - {qty} ')
        ch = get_and_parse_key()
        item = None
        if ch in ascii_letters:
            try:
                item_id = list(self.inv.keys())[string.ascii_letters.index(ch)]
            except IndexError:
                return
        if not item_id: return

        status('Nothing happens')

    def closest(self, objs):
        return first( sorted(objs, key=lambda x: dist(self.loc, x.loc)) )

    @property
    def alive(self):
        return self.n>0

    @property
    def dead(self):
        return not self.alive


class Gate(Being):
    """Being because it has HP and can be attacked."""
    health = 15
    char = Blocks.door


class Spell:
    id = None
    dmg = None
    _name = None

    def __init__(self):
        Objects.set_by_id(self.id, self)

    @property
    def name(self):
        if self._name:
            return self._name
        chars = self.__class__.__name__
        n=chars[0]
        for c in chars[1:]:
            if c.isupper():
                n+=' '
            n += c
        return n

    def select_target(self, B):
        x=None
        while x not in ('CLICK', ' ', blt.TK_ESCAPE):
            B.draw()
            loc = Loc(*get_mouse_pos())
            puts(loc.x, loc.y, Blocks.spell_select)
            refresh()
            x = get_and_parse_key()
        if x=='CLICK':
            loc = Loc(*get_mouse_pos())
            return B.screen_loc_to_map(loc)

    def ai_cast(self, B, hero, targets):
        self.apply(hero, choice(targets))

    def cast(self, B, hero):
        B.draw()
        loc = self.select_target(B)
        if loc:
            being = B.get_being(loc)
            if being:
                self.apply(hero, being)

    def apply(self, hero, being):
        pass


class ShieldSpell(Spell):
    cost = 4
    id = ID.shield_spell

    def apply(self, hero, being):
        loc = being.loc
        status(f'{being} is shielded for one turn')
        blt_put_obj(Blocks.shield_spell, loc)
        sleep(0.25)
        blt_put_obj(being, loc)
        hero.mana -= self.cost
        being.modifiers['defense'] = [1, 1*hero.magic_power]


class PowerBolt(Spell):
    dmg = 5
    cost = 4
    id = ID.power_bolt

    def apply(self, hero, being):
        loc = being.loc
        dmg = self.dmg * hero.magic_power
        hero.hit(being, dmg=dmg, type=Type.magic_attack, descr=self.name)
        blt_put_obj(Blocks.bolt1, loc)
        sleep(0.25)
        blt_put_obj(Blocks.bolt2, loc)
        sleep(0.25)
        blt_put_obj(being, loc)
        hero.mana -= self.cost


all_spells = (PowerBolt(), ShieldSpell())

class Hero(ArmyMixin, Being):
    xp = 0
    is_hero = 1
    speed = 5
    alive = 1
    selected = 0
    level = 1
    type = Type.hero
    mana = 20
    level_tiers = enumerate((500,2000,5000,10000,15000,25000,50000,100000,150000))
    magic_power = 2

    def __init__(self, *args, player=None, army=None, spells=None, **kwargs ):
        super().__init__(*args, **kwargs)
        self.player = player
        if player:
            self.color = player.color
            player._heroes.append(self.id)
            if player.is_ai:
                ai_heroes.append(self)
        if army:
            self.army = pad_none(army, 6)
        else:
            self.army = [None]*6
        self.set_army_ownership()
        self.spells = [ID.power_bolt, ID.shield_spell] + (spells or [])

    def set_army_ownership(self):
        for u in self.army:
            if u:
                u.hero = self

    def __str__(self):
        if not self.player:
            # Independent army
            u = first(self.live_army())
            return u.char if u else ' '
        return super().__str__()

    def _str(self):
        if self.selected:
            return str(self), Blocks.hero_select
        return str(self)

    def __repr__(self):
        return f'<H: {self.name} ({self.player})>'

    def in_castle(self):
        self.B.found_type_at(Type.castle, self.loc)

    def is_ai(self):
        return not self.player or self.player.is_ai

    def ai_cast_spell(self, B, targets):
        lst = []
        for id in self.spells:
            lst.append(Objects.get_by_id(id))
        lst = [s for s in lst if s.cost>=self.mana]
        if lst:
            choice(lst).ai_cast(B, self, targets)

    def cast_spell(self, B):
        lst = []
        for id in self.spells:
            lst.append(Objects.get_by_id(id))
        lst = [s for s in lst if s.cost<=self.mana]

        if not lst:
            self.talk(self, 'Cannot cast a spell: no spells or not enough mana!')
            return
        x, y = 5, 1
        ascii_letters = string.ascii_letters

        new = []
        for n, spell in enumerate(lst):
            new.append(f' {ascii_letters[n]}) {spell.name}')

        w = max(len(l) for l in new)
        blt.clear_area(x, y, w+2, len(new))
        for n, l in enumerate(new):
            puts(x, y+n, l)

        refresh()
        ch = get_and_parse_key()
        if ch and ch in ascii_letters:
            try:
                spell = lst[string.ascii_letters.index(ch)]
            except IndexError:
                B.draw()
                return
            spell.cast(B, self)
        if not ch:
            B.draw()


    def add_xp(self, xp):
        self.xp+=xp
        for lev, xp in self.level_tiers:
            if xp > self.xp:
                break
            self.level = lev

    def reset_mana(self):
        self.mana = 20 + self.level*5

    def ai_move(self):
        """This method is only for ai move by Heroes on the main map, NOT by IndependentArmy or units."""
        B = self.B
        castles = [c for c in self.player.castles if c.board_map==self.board_map and not B.get_being(c.loc)]
        for player in [p for p in players if p!=self.player]:
            for hero in [h for h in player.heroes if h.board_map==self.board_map]:
                if dist(self.loc, hero.loc) < 7:
                    mod = 1.3   # don't be a wuss
                    dst = None
                    if self.total_strength()*mod < hero.total_strength():
                        if not self.in_castle():
                            dst = self.closest(castles)
                    else:
                        dst = hero

                    while dst and self.cur_move and self.loc!=dst.loc and self.alive:
                        loc = B.next_move_to(self.loc, dst.loc)
                        if not loc: break
                        self.move(loc=loc)
                        sleep(0.25)
                        B.draw()
                    self.cur_move = self.speed

    def can_merge(self, type):
        return any(s is None or s.type==type for s in self.army)


class IndependentArmy(Hero):
    is_hero = 0

class ArmyUnit(Being):
    _name = None
    last_dir = 'l'
    shots = None

    def __init__(self, *args, hero=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hero = hero

    def _str(self):
        rv = [str(self)]
        if self.n>99:
            rv.append(Blocks.sub_plus)
        elif self.n<10:
            rv.append(getitem(Blocks.sub, self.n))
        else:
            rv.append(getitem(Blocks.sub, self.n//10))
            rv.append(getitem(Blocks.sub2, self.n%10))
        return rv

    def __repr__(self):
        return f'<Unit: {self.name}, {self.char}, {self.n}>'

    @property
    def total_health(self):
        return self.n * self.health

class Peasant(ArmyUnit):
    strength = 1
    defense = 1
    health = 5
    speed = 4
    cost = 15
    char = Blocks.peasant
    type = Type.peasant

class Pikeman(ArmyUnit):
    strength = 4
    defense = 5
    health = 10
    speed = 4
    cost = 25
    char = Blocks.pikeman
    type = Type.pikeman

class Griffin(ArmyUnit):
    strength = 8
    defense = 8
    health = 25
    speed = 6
    cost = 200
    char = Blocks.griffin_r
    type = Type.griffin

    def defend(self, dmg, type):
        dmg = super().defend(dmg, type)
        if type==Type.magic_attack and random()>.8:
            status('Griffin defends against magic attack')
            dmg = 0
        return dmg


class Archer(ArmyUnit):
    strength = 6
    defense = 3
    health = 10
    speed = 4
    cost = 30
    range_weapon_str = 1
    range = 7
    char = Blocks.archer_r
    type = Type.archer
    shots = 12

    def fire(self, B, hero):
        char = Blocks.arrow_l if self.char==Blocks.archer_l else Blocks.arrow_r
        a = Arrow(char, '', loc=self.loc)
        B.put(a)
        mod = 1
        for _ in range(self.range):
            a.move(self.last_dir)
            if B.found_type_at(Type.blocking, a.loc):
                mod = 0.5
            being = B.get_being(a.loc)
            if being and being.alive and being.hero!=hero:
                self.hit(being, ranged=1, mod=mod)
                B.remove(being)     # shuffle on top of arrow
                B.put(being)
                break
            blt_put_obj(a)
            sleep(0.15)

class Cavalier(ArmyUnit):
    strength = 5
    defense = 4
    health = 9
    speed = 7
    cost = 55
    char = Blocks.cavalier_r
    type = Type.cavalier

class Centaur(ArmyUnit):
    strength = 5
    defense = 3
    health = 8
    speed = 6
    cost = 70
    char = Blocks.centaur_r
    type = Type.centaur

class Building(BeingItemCastleBase):
    available = 0
    _name = None
    type = Type.building

    def __init__(self, loc=None, board_map=None, castle=None, player=None):
        self.loc, self.board_map, self.castle, self.player = loc, board_map, castle, player
        if board_map:
            self.B.put(self)

    def __repr__(self):
        char = super().__repr__()
        return f'<{char}: {self.name} ({self.player})>'

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def _str(self):
        return str(self), getitem(Blocks.sub, self.available, '+')

class Sawmill(Building):
    resource = ID.wood
    available = 4
    growth = 2
    char = Blocks.sawmill


class Hut(Building):
    cost = {ID.gold: 250}
    units = Peasant
    char = Blocks.hut
    available = 5
    growth = 4

class Guardhouse(Building):
    cost = {ID.gold: 500, ID.ore: 10}
    units = Pikeman
    char = Blocks.guardhouse
    available = 10
    growth = 14

class ArchersTower(Building):
    cost = {ID.gold: 500, ID.wood:5, ID.ore:5}
    units = Archer
    char = Blocks.archers_tower
    available = 6
    growth = 9

class GriffinTower(Building):
    cost = {ID.gold: 1000, ID.ore:5}
    units = Griffin
    char = Blocks.griffin_tower
    available = 6
    growth = 7

class JoustingGround(Building):
    cost = {ID.gold: 750, ID.wood: 5}
    units = Cavalier
    char = Blocks.jousting_ground
    available = 2
    growth = 2

class CentaurStables(Building):
    cost = {ID.gold: 500, ID.wood: 5}
    units = Centaur
    char = Blocks.centaur_stables
    available = 10
    growth = 14

class CastleTownType(TownType):
    building_types = (Hut, Guardhouse, ArchersTower, JoustingGround)

class RampartTownType(TownType):
    building_types = (CentaurStables,)

class Saves:
    saves = {}
    loaded = 0

    def load(self, name):
        global Objects, done_events
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        self.saves = sh['saves']
        s = self.saves[name]
        board_grid[:] = s['boards']
        Objects = s['objects']
        done_events = s['done_events']
        player = Objects[ID.player]
        bl = s['cur_brd']
        B = board_grid[bl.y][bl.x]
        return player, B

    def save(self, cur_brd, name=None):
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        s = {}
        s['boards'] = board_grid
        s['cur_brd'] = cur_brd
        s['objects'] = Objects
        s['done_events'] = done_events
        player = Objects.player
        bl = cur_brd
        B = board_grid[bl.y][bl.x]
        sh['saves'] = {name: s}
        sh.close()
        return B.get_all(player.loc), name


def main(load_game):
    blt.open()
    blt.set("window: resizeable=true, size=80x25, cellsize=auto, title='Heroes of Sorcery'; font: FreeMono.ttf, size=24")
    blt.set("input.filter={keyboard, mouse+}")
    blt.color("white")
    blt.composition(True)

    blt.set("U+E300: NotoEmoji-Regular.ttf, size=32x32, spacing=3x2, codepage=notocp.txt, align=top-left")  # GOOGLE
    blt.set("U+E400: FreeMono.ttf, size=32x32, spacing=3x2, codepage=monocp.txt, align=top-left")          # GNU

    blt.clear()
    if not os.path.exists('saves'):
        os.mkdir('saves')
    Misc.is_game = 1

    Misc.player = Player('green', False, color='green')
    Misc.blue_player = Player('blue', True, color='lighter blue')
    players.extend([Misc.player, Misc.blue_player])

    ok=1
    board_setup()

    hero = Misc.hero = Objects.hero1
    while ok:
        for hero in [h for h in Misc.player.heroes if h.alive]:
            hero.mana+=1
            while ok and ok!=END_MOVE and hero.alive:
                hero.B.draw()
                Misc.hero = hero
                hero.selected = 1
                blt_put_obj(hero)
                ok = handle_ui(hero)
                if ok=='q': return
                if ok==END_MOVE:
                    hero.selected = 0
                    blt_put_obj(hero)
                    hero.cur_move = hero.speed
            ok=1
        for h in ai_heroes:
            if h.alive:
                h.mana+=1
                h.ai_move()
        for b in player_buildings + ai_buildings:
            b.available += b.growth

        Misc.day+=1
        if Misc.day==8:
            Misc.week+=1
            Misc.day = 1
        for id in castles:
            Objects.get_by_id(id).handle_day()


def handle_ui(unit, hero=None, only_allow=None):
    if not unit.cur_move:
        return END_MOVE
    k = None
    while not k or (only_allow and k and k not in only_allow):
        k = get_and_parse_key()
    puts(0,1, ' '*78)
    B = unit.B if unit.is_hero else Misc.B
    if k=='q':
        return 'q'
    elif k in 'yubnhlHL':
        if k in 'HL':
            k = k.lower()
            unit.last_dir = k
            for _ in range(5):
                rv = unit.move(k)
                if not rv:
                    return END_MOVE
                if isinstance(rv, LoadBoard):
                    break
        else:
            rv = unit.move(k)
            unit.last_dir = k
            if not rv:
                return END_MOVE

        unit.last_dir = k
        if isinstance(rv, LoadBoard):
            loc = rv.b_new
            if chk_b_oob(loc) and board_grid[loc.y][loc.x]:
                Misc.B = unit.move_to_board(Boards.get_by_loc(loc), loc=rv.new)
        stats()

    elif k == '.':
        pass
    elif k == 'f':
        if isinstance(unit, Archer):
            unit.fire(B, hero)
    elif k == 'o':
        name = prompt()
        Misc.hero, B = Saves().load(name)
    elif k == 's':
        if hero:
            hero.cast_spell(B)
    elif k == 'a':
        if Misc.B == Boards.b_battle:
            return AUTO_BATTLE
    elif k == 'S':
        name = prompt()
        Saves().save(Misc.B.loc, name)
        status(f'Saved game as "{name}"')
        refresh()
    elif k == 'v':
        status(str(unit.loc))
    elif k == ' ':
        unit.cur_move=0
    elif k == '5' and DBG:
        k = get_and_parse_key()
        k2 = get_and_parse_key()
        if k and k2:
            try:
                print(B.B[int(k+k2)])
                status(f'printed row {k+k2} to debug')
            except:
                status('try again')

    elif k == 't' and DBG:
        # debug teleport
        mp = ''
        while 1:
            k = get_and_parse_key()
            if not k: break
            mp+=k
            status(mp)
            refresh()
            if mp.endswith(' '):
                try:
                    x,y=mp[:-1].split(',')
                    unit.tele(Loc(int(x), int(y)))
                except Exception as e:
                    print(e)
                break

    elif k == 'u':
        unit.use()

    elif k == 'E':
        B.display(str(B.get_all(unit.loc)))
    elif k == 'm':
        manage_castles()

    elif k == 'i':
        txt = []
        for id, n in Misc.hero.inv.items():
            item = Objects[id]
            if item and n:
                txt.append(f'{item.name} {n}')
        B.display(txt)

    B.draw(battle = (not unit.is_hero))
    return 1


def editor(_map):
    blt.open()
    blt.set("window: resizeable=true, size=80x25, cellsize=auto, title='Editor'; font: FreeMono.ttf, size=20")
    blt.color("white")
    blt.composition(True)
    blt.set("U+E300: NotoEmoji-Regular.ttf, size=32x32, spacing=3x2, codepage=notocp.txt, align=top-left")  # GOOGLE

    blt.clear()
    Misc.is_game = 0
    loc = Loc(20, 8)
    brush = None
    written = 0
    fname = f'maps/{_map}.map'
    if not os.path.exists(fname):
        with open(fname, 'w') as fp:
            for n in range(HEIGHT):
                prefix = '' if n%2==0 else ' '
                fp.write(prefix + (Blocks.blank + ' ')*WIDTH + '\n')
    B = Board(None, _map)
    setattr(Boards, 'b_'+_map, B)
    B.load_map(_map, 1)
    B.draw()

    while 1:
        k = get_and_parse_key()
        if k=='Q': break
        elif k and k in 'hlyubnHL':
            n = 1
            if k in 'HL':
                n = 5
            my,mx = dict(h=(0,-1), l=(0,1), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]
            if mx==1 and my and loc.y%2==0:
                mx=0
            if mx==-1 and my and loc.y%2==1:
                mx=0

            for _ in range(n):
                if brush:
                    if brush=='T':
                        B.B[loc.y][loc.x] = [choice((Blocks.tree1, Blocks.tree2))]
                    else:
                        B.B[loc.y][loc.x] = [brush]
                if chk_oob(loc.mod(mx,my)):
                    loc = loc.mod(mx,my)

        elif k == ' ':
            brush = None
        elif k == 'e':
            brush = Blocks.blank
        elif k == 'r':
            brush = Blocks.rock
        elif k and k in '0123456789':
            B.put(k, loc)
        elif k == 'w':
            Item(B, Blocks.water, 'water', loc)
        elif k == 'B':
            B.put(Blocks.bricks, loc)
            brush = Blocks.bricks
        elif k == 't':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
            brush = 'T'
        elif k == 'o':
            cmds = ''.split()
            cmd = ''
            while 1:
                k = get_and_parse_key()
                if k:
                    cmd += k
                elif any(c.startswith(cmd) for c in cmds):
                    continue
                break

        elif k == 'E':
            puts(2,2, 'Are you sure you want to clear the map? [Y/N]')
            y = get_and_parse_key()
            if y=='Y':
                for row in B.B:
                    for cell in row:
                        cell[:] = [Blocks.blank]
                B.B[-1][-1].append('_')
        elif k == 'f':
            B.put(Blocks.shelves, loc)
        elif k == 'W':
            # val_to_k = {v:k for k,v in Blocks.__dict__.items()}
            with open(f'maps/{_map}.map', 'w') as fp:
                for n, row in enumerate(B.B):
                    if n%2==1:
                        fp.write(' ')
                    for cell in row:
                        a = cell[-1]
                        fp.write(str(a) + ' ')
                    fp.write('\n')
            written=1

        B.draw()
        x = loc.x*2 + (0 if loc.y%2==0 else 1)
        blt.clear_area(x,loc.y,1,1)
        puts(x, loc.y, Blocks.cursor)
        if brush==Blocks.blank:
            tool = 'eraser'
        elif brush==Blocks.rock:
            tool = 'rock'
        elif not brush:
            tool = ''
        else:
            tool = brush
        puts(73,1, tool)
        puts(0 if loc.x>20 else 35,
             0, str(loc))
        refresh()
        if written:
            puts(65,2, 'map written')
            written=0
        # win.move(loc.y, loc.x)
    blt.set("U+E100: none; U+E200: none; U+E300: none; zodiac font: none")
    blt.composition(False)
    blt.close()

if __name__ == "__main__":
    argv = sys.argv[1:]
    load_game = None
    for a in argv:
        if a == '-d':
            DBG = True
        if a and a.startswith('-l'):
            load_game = a[2:]
    if first(argv) == 'ed':
        editor(argv[1])
    else:
        main(load_game)
