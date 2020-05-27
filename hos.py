#!/usr/bin/env python
from bearlibterminal import terminal as blt
import os
import sys
from random import choice
from collections import defaultdict
from textwrap import wrap
import string
# import shelve
from copy import copy  #, deepcopy
from enum import Enum, auto

HEIGHT = 16
WIDTH = 38
debug_log = open('debug', 'w')
LOAD_BOARD = 999
SLP = 0.01
SEQ_TYPES = (list, tuple)
board_grid = []

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
funfrock
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
        id = getattr(ID, k)
        return self.objects[getattr(ID, k)]

    def get(self, k, default=None):
        return self.objects.get(getattr(ID, k, None))

    def get_by_id(self, id):
        return self.objects.get(id)

    def set_by_id(self, id, v):
        self.objects[id] = v

Objects = ObjectsClass()

class Player:
    gold = 250
    wood = 0
    rock = 0
    mercury = 0
    sulphur = 0

    def __init__(self, name, is_ai):
        self.name, self.is_ai = name, is_ai

    def __repr__(self):
        return f'<P: {self.name}>'

class Type(Enum):
    door1 = auto()
    container = auto()
    blocking = auto()
    gate = auto()
    castle = auto()
    peasant = auto()
    pikeman = auto()

class Blocks:
    """All game tiles."""
    blank = '.'
    rock = '█'
    platform = '⎽'
    stand = '≖'
    door = '⌸'
    water = '≋'
    fountain = '␣'
    tree1 = noto_tiles['tree1']
    tree2 = noto_tiles['tree2']
    rock2 = '▅'
    rock3 = '░'
    cactus = noto_tiles['cactus']
    tulip = noto_tiles['flower1']
    snowman = '☃'
    snowflake = noto_tiles['snowflake']
    book1 = noto_tiles['book1']
    book2 = noto_tiles['book2']
    lever = '╖'
    sharp_rock = noto_tiles['sharp-rock1']
    statue = 'Ộ'
    hexagon = '⎔'
    soldier = '⍾'
    peasant = '\u23f2'
    pikeman = '\u23f3'
    hero1 = noto_tiles['man']
    gold = '☉'
    rubbish = '⛁'
    cursor = '𐌏'
    hut = '△'
    barracks = '⌂'
    sub_1 = '₁'
    sub_2 = '₂'
    sub_3 = '₃'
    sub_4 = '₄'
    sub_5 = '₅'
    sub_6 = '₆'
    sub_7 = '₇'
    sub_8 = '₈'
    sub_9 = '₉'
    sub = [None,
           sub_1,
           sub_2,
           sub_3,
           sub_4,
           sub_5,
           sub_6,
           sub_7,
           sub_8,
           sub_9,
          ]
    list_select = '▶'

BLOCKING = [Blocks.rock, Type.door1, Type.blocking, Type.gate, Type.castle]

class ID:
    castle1 = 1
    hero1 = 2

class Misc:
    pass

def mkcell():
    return [Blocks.blank]

def mkrow():
    return [mkcell() for _ in range(WIDTH)]

def first(x):
    return x[0] if x else None
def last(x):
    return x[-1] if x else None

def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= WIDTH-1

def chk_b_oob(loc, y=0, x=0):
    h = len(board_grid)
    w = len(board_grid[0])
    newx, newy = loc.x+x, loc.y+y
    return 0 <= newy <= h-1 and 0 <= newx <= w-1

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

    def load_map(self, map_num, for_editor=0):
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

                    elif char==Blocks.hut:
                        h=Hut(loc, self._map)
                        self.put(h)
                        self.buildings.append(h)

                    elif char==Blocks.barracks:
                        a=Barracks(loc, self._map)
                        self.put(a)
                        self.buildings.append(a)

                    elif char==Blocks.fountain:
                        Item(Blocks.fountain, 'water fountain basin', loc, self._map)

                    elif char in (BL.book1, BL.book2):
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
        Hero(self.specials[1], '1', name='Ardor', char=Blocks.hero1, id=ID.hero1, player=Misc.player)
        c = Castle('Castle 1', self.specials[2], self._map, id=ID.castle1, player=Misc.player)

    def draw(self):
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
                if isinstance(a, int) and a<500:
                    a = Objects.get_by_id(a)
                if a.color:
                    a = f'[color={a.color}]{a}[/color]'
                puts(x,y,a)

        for y,x,txt in self.labels:
            puts(x,y,txt)
        refresh()

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

def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

class Boards:
    pass

class BeingItemTownMixin:
    is_player = 0
    state = 0
    color = None
    _str = None

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
            return getattr(Boards, 'b_'+self.board_map)


class Item(BeingItemTownMixin):
    board_map = None

    def __init__(self, char, name, loc=None, board_map=None, put=True, id=None, type=None, color=None):
        self.char, self.name, self.loc, self.board_map, self.id, self.type, self.color = \
                char, name, loc, board_map, id, type, color
        self.inv = defaultdict(int)
        if id:
            Objects.set_by_id(id, self)
        if board_map and put:
            self.B.put(self)

    def __repr__(self):
        return f'<I: {self.char}>'

    def move(self, dir, n=1):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        for _ in range(n):
            new = self.loc.mod(*m)
            self.B.remove(self)
            self.loc = new
            self.B.put(self)


class Castle(Item):
    weekly_income = 250
    current_hero = None

    def __init__(self, *args, player=None, **kwargs):
        self.army = [None] * 6
        self.player = player
        super().__init__(Blocks.door, *args, **kwargs)
        self.type = Type.castle

    def __repr__(self):
        return f'<C: {self.name}>'

    def town_ui(self, hero):
        self.current_hero = hero
        while 1:
            Boards.b_town_ui.draw()
            stats(self)
            k = get_and_parse_key()
            if k in ('q', 'ESCAPE'):
                break
            elif k=='r':
                self.recruit_ui()
            elif k=='t':
                self.troops_ui()

    def troops_ui(self):
        army_size = 6
        i = 0
        Boards.b_town_ui.draw()

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
                    h.army[i] = self.merge_into_army([h.army[i]], self.army)

            elif k == 'LEFT':
                i-=1
                if i<0: i = 5
            elif k == 'RIGHT':
                i+=1
                if i>5: i = 0

    def merge_into_army(self, A, B):
        """Merge army x into y."""
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
            return remains + [None]*(6-len(remains))


    def recruit_ui(self):
        recruited = defaultdict(int)
        curs = 0
        # empty_slots = [n for n, s in enumerate(self.current_hero.army) if not s]
        B = Boards.b_town_ui
        B.draw()
        refresh()
        stats(self)
        while 1:
            lst = [('', 'Unit', 'Available', 'Recruited')]
            for n, b in enumerate(B.buildings):
                x = Blocks.cursor if n==curs else ''
                lst.append((x, b.units.__name__, b.available, recruited[b.units.type]))

            x = Blocks.cursor if curs==len(B.buildings) else ''
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
            gold = self.player.gold
            unit_cost = bld.units.cost if bld else 0
            if k in ('q', 'ESCAPE'):
                break
            elif k == 'DOWN': curs+=1
            elif k == 'UP': curs-=1
            elif not bld and k=='ENTER':
                self.player.gold = gold
                # Hope there's enough empty slots!
                for type, n in recruited.items():
                    for m, slot in enumerate(self.army):
                        if not slot:
                            self.army[m] = cls_by_type[type.name](n=n)
                            break
                        elif slot.type==type:
                            slot.n+=n
                            break
                break
            elif k == 'ENTER': select = curs
            elif k == 'LEFT' and bld and recruited[bld.units.type]:
                bld.available+=1
                recruited[bld.units.type]-=1
                self.player.gold += unit_cost
            elif k == 'RIGHT' and bld and bld.available and unit_cost<=gold:
                bld.available-=1
                recruited[bld.units.type]+=1
                self.player.gold -= unit_cost

            if curs<0:
                curs = len(B.buildings)
            if curs>len(B.buildings):
                curs = 0

class BattleUI:
    def __init__(self, B):
        self.B=B

    def go(self):
        pass


class Being(BeingItemTownMixin):
    n = None
    health = 1
    max_health = 1
    is_being = 1
    type = None
    char = None

    def __init__(self, loc=None, board_map=None, put=True, id=None, name=None, state=0, n=1, char='?', color=None):
        self.id, self.loc, self.board_map, self._name, self.state, self.n, self.color  = id, loc, board_map, name, state, n, color
        self.char = self.char or char
        self.inv = defaultdict(int)
        if id:
            Objects.set_by_id(id, self)
        if board_map and put:
            self.B.put(self)

    def __str__(self):
        return super().__str__() if self.health>0 else Blocks.rubbish

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def talk(self, being, dialog=None, yesno=False, resp=False):
        """Messages, dialogs, yes/no, prompt for responce, multiple choice replies."""
        if isinstance(dialog, int):
            dialog = conversations.get(dialog)
        being = objects.get(being) or being
        loc = being.loc
        if isinstance(dialog, str):
            dialog = [dialog]
        dialog = dialog or conversations[being.id]
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
        # m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[dir]
        my,mx = dict(h=(0,-1), l=(0,1), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[dir]
        if mx==1 and my and self.loc.y%2==0:
            mx=0
        if mx==-1 and my and self.loc.y%2==1:
            mx=0
        m = my,mx
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

        if new and B.found_type_at(Type.castle, new):
            cas = B[new]
            if cas.player == self.player:
                cas.town_ui(self)
            else:
                cas.battle_ui()
            return None, None

        if new and B.is_blocked(new):
            new = None

        if new:
            B.remove(self)
            if new[0] == LOAD_BOARD or new[0] is None:
                return new
            self.loc = new
            self.put(new)
            refresh()
            return True, True
        return None, None

    def handle_player_move(self, new):
        B=self.B
        pick_up = []
        top_obj = B.get_top_obj(new)
        items = B.get_all_obj(new)
        if top_obj:
            # why does this work with unicode offsets? maybe it doesn't..
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
        a = self.strength * self.n
        b = obj.health * obj.n
        c = b - a
        status(f'{self} hits {obj} for {a} HP')
        if c <= 0:
            status(f'{obj} dies')
        else:
            obj.n, obj.health = divmod(c, obj.max_health)

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

    def use(self):
        """For spells maybe?"""
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
    army = [None] * 6
    def __init__(self, *args, player=None ,**kwargs ):
        super().__init__(*args, **kwargs)
        self.player = player

    def __repr__(self):
        return f'<H: {self.name} ({self.player})>'

    def real_army(self):
        return list(filter(None, self.army))

class ArmyUnit(Being):
    _name = None

    def _str(self):
        return str(self), getitem(Blocks.sub, self.n, '+')

class Peasant(ArmyUnit):
    strength = 1
    defence = 1
    cost = 15
    char = Blocks.peasant
    type = Type.peasant

class Pikeman(ArmyUnit):
    strength = 3
    defence = 4
    cost = 25
    char = Blocks.pikeman
    type = Type.pikeman

cls_by_type = {
    Type.peasant.name: Peasant,
    Type.pikeman.name: Pikeman,
}

class Building(BeingItemTownMixin):
    available = 0
    _name = None

    def __init__(self, loc=None, board_map=None):
        self.loc, self.board_map = loc, board_map
        # if board_map:
            # self.B.put(self)

    def __repr__(self):
        char = super().__repr__()
        return f'<H: {self.name} ({self.player})>'

    @property
    def name(self):
        return self._name or self.__class__.__name__

    def _str(self):
        return str(self), getitem(Blocks.sub, self.available, '+')

def getitem(it, ind=0, default=None):
    try: return it[ind]
    except IndexError: return default

class Hut(Building):
    units = Peasant
    char = Blocks.hut
    available = 5

class Barracks(Building):
    units = Pikeman
    char = Blocks.barracks
    available = 3

class Saves:
    saves = {}
    loaded = 0

    def load(self, name):
        global Objects, done_events
        fn = f'saves/{name}.data'
        sh = shelve.open(fn, protocol=1)
        self.saves = sh['saves']
        s = self.saves[name]
        boards[:] = s['boards']
        Objects = s['objects']
        done_events = s['done_events']
        player = objects[ID.player]
        loc = player.loc
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        return player, B

    def save(self, cur_brd, name=None):
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
            blt.puts(x,y,_s)
    else:
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
    if k and blt.check(blt.TK_WCHAR) or k in (blt.TK_RETURN,blt.TK_SHIFT,blt.TK_ESCAPE,blt.TK_UP,blt.TK_DOWN,b.TK_RIGHT,b.TK_LEFT):
        k = keymap.get(k)
        if k and blt.state(blt.TK_SHIFT):
            k = k.upper()
            if k=='-': k = '_'
            if k=='/': k = '?'
            if k=='=': k = '+'
        return k

def board_setup():
    Boards.b_town_ui = Board(Loc(0,0), 'town_ui')
    Boards.b_town_ui.load_map('town_ui')
    Boards.b_1 = Board(Loc(0,2), '1')
    Boards.b_1.board_1()
    board_grid[:] = [
        ['town_ui'],
        [None],
        ['1'],
    ]
    Misc.B = Boards.b_1

def main(load_game):
    blt.open()
    blt.set("window: resizeable=true, size=80x25, cellsize=auto, title='Heroes of Sorcery'; font: FreeMono2.ttf, size=24")
    blt.color("white")
    blt.composition(True)

    blt.set("U+E300: NotoEmoji-Regular.ttf, size=32x32, spacing=3x2, codepage=notocp.txt, align=top-left")  # GOOGLE
    blt.set("U+E400: FreeMono2.ttf, size=32x32, spacing=3x2, codepage=monocp.txt, align=top-left")          # GNU

    blt.clear()
    if not os.path.exists('saves'):
        os.mkdir('saves')
    Misc.is_game = 1

    Misc.player = Player('green', False)

    ok=1
    board_setup()
    Misc.hero = Objects.hero1
    Misc.B.draw()
    while ok:
        ok=handle_ui()

def handle_ui():
    k = get_and_parse_key()
    puts(0,1, ' '*78)
    hero = Misc.hero
    if k=='q':
        return 0

    elif k in 'yubnhlHL':
        if k in 'HL':
            k = k.lower()
            for _ in range(5):
                rv = hero.move(k)
                if rv[0] == LOAD_BOARD:
                    break
        else:
            rv = hero.move(k)

        if rv[0] == LOAD_BOARD:
            loc = rv[1]
            x, y = hero.loc
            if k=='l': x = 0
            if k=='h': x = 37
            if k in 'yu': y = 15
            if k in 'bn': y = 0

            # ugly but....
            p_loc = Loc(x, y)
            if chk_b_oob(loc) and board_grid[loc.y][loc.x]:
                Misc.B = hero.move_to_board(board_grid[loc.y][loc.x]._map, loc=p_loc)

    elif k == '.':
        pass
    elif k == 'o':
        name = prompt(win2)
        hero, B = Saves().load(name)
    elif k == 's':
        name = prompt(win2)
        Saves().save(Misc.B.loc, name)
        status(f'Saved game as "{name}"')
        refresh()
    elif k == 'v':
        status(str(hero.loc))
    elif k == ' ':
        hero.action()
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
            Windows.refresh()
            if mp.endswith(' '):
                try:
                    x,y=mp[:-1].split(',')
                    print(Loc(int(x), int(y)))
                    player.tele(Loc(int(x), int(y)))
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

    Misc.B.draw()
    stats()
    return 1

def stats(castle=None):
    pl = Misc.player
    h = Misc.hero
    n = len(h.real_army())
    st = f'[Gold:{pl.gold}][Wood:{pl.wood}][Rock:{pl.rock}][Mercury:{pl.mercury}][Sulphur:{pl.sulphur}] |'
    x = len(st)+2
    puts2(1,0,blt_esc(st))
    puts2(x,0, h.name)
    x+= len(h.name) + 2
    # for x2 in range(n-1): puts2(x+x2*4,0,'|')
    y = 1
    if castle:
        x = 1
        for a in castle.army:
            puts2(x+1 if a else x,
                  y,
                  a or blt_esc('[ ]')
                 )
            # if a: x+=1
            x+=3
        y+=1

    x = 1
    for a in h.army:
        puts2(x+1 if a else x,
              y,
              a or blt_esc('[ ]'))
        x+=3
    refresh()

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


def status(msg):
    puts(0,2,msg)


def editor(_map):
    blt.open()
    blt.set("window: resizeable=true, size=80x25, cellsize=auto, title='Little Adventure'; font: FreeMono2.ttf, size=24")
    blt.color("white")
    blt.composition(True)

    # blt.set("U+E200: Tiles.png, size=24x24, align=top-left")
    # blt.set("U+E300: fontawesome-webfont.ttf, size=16x16, spacing=3x2, codepage=fontawesome-codepage.txt")
    # blt.set("U+E300: fontello.ttf, size=16x16, spacing=3x2, codepage=cp.txt")
    blt.set("U+E300: NotoEmoji-Regular.ttf, size=32x32, spacing=3x2, codepage=notocp.txt, align=top-left")  # GOOGLE
    blt.set("U+E400: FreeMono2.ttf, size=32x32, spacing=3x2, codepage=monocp.txt, align=top-left")           # GNU

    blt.clear()
    Misc.is_game = 0
    begin_x = 0; begin_y = 0; width = 80
    loc = Loc(20, 8)
    brush = None
    written = 0
    fname = f'maps/{_map}.map'
    if not os.path.exists(fname):
        with open(fname, 'w') as fp:
            for n in range(HEIGHT):
                prefix = '' if n%2==0 else ' '
                # print(prefix + (Blocks.blank + ' ')*WIDTH + '\n')
                fp.write(prefix + (Blocks.blank + ' ')*WIDTH + '\n')
    B = Board(None, _map)
    setattr(Boards, 'b_'+_map, B)
    B.load_map(_map, 1)
    B.draw()

    while 1:
        k = get_and_parse_key()
        if k=='Q': break
        # elif k and k in 'hjklyubnHL':
        elif k and k in 'hlyubnHL':
            n = 1
            if k in 'HL':
                n = 5
            # m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]
            my,mx = dict(h=(0,-1), l=(0,1), y=(-1,-1), u=(-1,1), b=(1,-1), n=(1,1), H=(0,-1), L=(0,1))[k]
            if mx==1 and my and loc.y%2==0:
                mx=0
            if mx==-1 and my and loc.y%2==1:
                mx=0

            print("brush", brush)
            for _ in range(n):
                if brush:
                    B.B[loc.y][loc.x] = [brush]
                if chk_oob(loc.mod(my,mx)):
                    loc = loc.mod(my,mx)

        elif k == ' ':
            brush = None
        elif k == 'e':
            brush = Blocks.blank
        elif k == 'r':
            brush = Blocks.rock
        elif k == 's':
            B.put(Blocks.steps_r, loc)
            brush = Blocks.steps_r
        elif k == '/':
            B.put(Blocks.angled1, loc)
            brush = Blocks.angled1
        elif k == '\\':
            B.put(Blocks.angled2, loc)
            brush = Blocks.angled2
        elif k == 'S':
            B.put(Blocks.steps_l, loc)
            brush = Blocks.steps_l
        elif k == 'M':
            B.put(Blocks.smoke_pipe, loc)
        elif k == 'd':
            B.put('d', loc)
        elif k and k in '0123456789':
            B.put(k, loc)
        elif k == 'w':
            Item(B, Blocks.water, 'water', loc)
        elif k == 't':
            B.put(Blocks.stool, loc)
        elif k == 'a':
            B.put(Blocks.ladder, loc)
        elif k == 'c':
            B.put(Blocks.cupboard, loc)
        elif k == 'B':
            B.put(Blocks.dock_boards, loc)
        elif k == 'p':
            B.put(Blocks.platform_top, loc)
        elif k == 'g':
            B.put(Blocks.grill, loc)
        elif k == 'F':
            B.put(Blocks.ferry, loc)
        elif k == 'A':
            B.put(Blocks.bars, loc)
        elif k == 'R':
            B.put(Blocks.rubbish, loc)

        # NPCs
        elif k == 'G':
            B.put(Blocks.elephant, loc)
        elif k == 'O':
            B.put(Blocks.soldier, loc)

        elif k == 'T':
            B.put(choice((Blocks.tree1, Blocks.tree2)), loc)
        elif k == 'z':
            B.put(Blocks.guardrail_m, loc)
            brush = Blocks.guardrail_m
        elif k == 'x':
            B.put(Blocks.rock2, loc)
            brush = Blocks.rock2
        elif k == 'X':
            B.put(Blocks.shelves, loc)
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
                k = get_and_parse_key()
                if k:
                    cmd += k
                if cmd == 'l':  B.put(BL.locker, loc)
                elif cmd == 'B':  B.put(BL.books, loc)
                elif cmd == 'ob': B.put(BL.open_book, loc)
                elif cmd == 't':  B.put('t', loc)
                elif cmd == 'f':  B.put(BL.fountain, loc)
                elif cmd == 'p':  B.put(BL.platform2, loc)

                elif cmd == 'm': B.put(BL.monkey, loc)
                elif cmd == 'v': B.put(BL.lever, loc)
                elif cmd == 's': B.put(BL.sharp_rock, loc)
                elif cmd == 'r': B.put(BL.rock3, loc)
                elif cmd == 'd': B.put('d', loc)     # drawing
                elif cmd == 'R': B.put(Blocks.rabbit, loc)
                elif cmd == 'h': B.put(Blocks.hut, loc)
                elif cmd == 'b': B.put(Blocks.barracks, loc)

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
                        # char = getattr(a, 'char', None)
                        # if char and isinstance(char,int) and char>500:
                        #     k = val_to_k[char]
                        #     a = getattr(OLDBlocks, k)
                        fp.write(str(a) + ' ')
                    fp.write('\n')
            written=1

        B.draw()
        x = loc.x*2 + (0 if loc.y%2==0 else 1)
        blt.clear_area(x,loc.y,1,1)
        puts(x, loc.y, Blocks.cursor)
        refresh()
        if brush==Blocks.blank:
            tool = 'eraser'
        elif brush==Blocks.rock:
            tool = 'rock'
        elif not brush:
            tool = ''
        else:
            tool = brush
        puts(73,1, tool)
        puts(0 if loc.x>40 else 70,
             0, str(loc))
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
