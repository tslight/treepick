# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
from .actions import Actions
from os import environ
environ.setdefault('ESCDELAY', '12')  # otherwise it takes an age!


class Keys(Actions):

    def getpadkeys(self):
        self.screen.refresh()
        self.pad.refresh(self.pos, 0, 0, 0, self.y - 2, self.x - 1)
        while True:
            key = self.screen.getch()
            keys = {
                27: self.quit,
                curses.KEY_DOWN: self.pad_dn,
                curses.KEY_UP: self.pad_up,
                curses.KEY_NPAGE: self.pad_pgup,
                curses.KEY_PPAGE: self.pad_pgdn,
                curses.KEY_RESIZE: self.resize,
                ord('q'): self.quit,
                ord('j'): self.pad_dn,
                ord('k'): self.pad_up,
                ord('f'): self.pad_pgdn,
                ord('b'): self.pad_pgup,
            }
            try:
                if keys[key]():
                    break
            except KeyError:
                pass
            self.pad.refresh(self.pos, 0, 0, 0, self.y - 2, self.x - 1)
        self.screen.erase()
        self.screen.refresh()

    def parse_curline(self, action):
        line = 0
        for child, depth in self.traverse():
            if depth == 0:
                continue
            if line == self.curline:
                {
                    'expand': lambda: child.expand(self),
                    'expand_all': lambda: child.expand_all(self),
                    'toggle_expand': child.toggle_expand,
                    'collapse': child.collapse,
                    'collapse_all': lambda: child.collapse_all(self, depth),
                    'toggle_pick': lambda: child.pick(self),
                    'nextparent': lambda: child.nextparent(self, depth),
                    'prevparent': lambda: child.prevparent(self, depth),
                    'getsize': lambda: child.getsize(self),
                }[action]()
                break
            line += 1

    def getkeys(self):
        while True:
            self.drawtree()
            key = self.screen.getch()
            keys = {
                27: self.quit,
                curses.KEY_F1: self.mkkeypad,
                curses.KEY_F2: self.mkpickpad,
                curses.KEY_F5: self.reset_all,
                curses.KEY_F4: self.reset_picked,
                curses.KEY_UP: self.up,
                curses.KEY_DOWN: self.dn,
                curses.KEY_PPAGE: self.pgup,
                curses.KEY_NPAGE: self.pgdn,
                curses.KEY_LEFT: lambda: self.parse_curline('collapse'),
                curses.KEY_RIGHT: lambda: self.parse_curline('expand'),
                curses.KEY_SRIGHT: lambda: self.parse_curline('expand_all'),
                curses.KEY_SLEFT: lambda: self.parse_curline('collapse_all'),
                curses.KEY_HOME: self.top,
                curses.KEY_END: self.bottom,
                curses.KEY_RESIZE: self.resize,
                ord('q'): self.quit,
                ord('?'): self.mkkeypad,
                ord('p'): self.mkpickpad,
                ord('R'): self.reset_all,
                ord('r'): self.reset_picked,
                ord('j'): self.dn,
                ord('k'): self.up,
                ord('b'): self.pgup,
                ord('f'): self.pgdn,
                ord('l'): lambda: self.parse_curline('expand'),
                ord('h'): lambda: self.parse_curline('collapse'),
                ord('L'): lambda: self.parse_curline('expand_all'),
                ord('H'): lambda: self.parse_curline('collapse_all'),
                ord('g'): self.top,
                ord('G'): self.bottom,
                ord('\t'): lambda: self.parse_curline('toggle_expand'),
                ord('\n'): lambda: self.parse_curline('toggle_expand'),
                ord(' '): lambda: self.parse_curline('toggle_pick'),
                ord('J'): lambda: self.parse_curline('nextparent'),
                ord('K'): lambda: self.parse_curline('prevparent'),
                ord('s'): lambda: self.parse_curline('getsize'),
                ord('S'): self.getsizeall,
                ord('.'): self.toggle_hidden,
                ord('/'): self.find,
                ord('n'): self.findnext,
                ord('N'): self.findprev,
                ord('v'): self.pickall,
                ord(':'): self.pickglobs,
            }
            try:
                if keys[key]():
                    return self.picked
            except KeyError:
                pass
            self.curline %= self.line
