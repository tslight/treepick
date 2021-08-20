# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import curses

from pdu import du
from .screen import Screen


class Draw(Screen):
    def __init__(self, screen, picked, expanded, sized):
        Screen.__init__(self, screen, picked)
        self.expanded = expanded
        self.sized = sized
        self.curline = 0
        self.line = 0

    def getnode(self):
        if not os.path.isdir(self.name):
            return '    ' + os.path.basename(self.name)
        elif self.name in self.expanded:
            return '[-] ' + os.path.basename(self.name) + '/'
        elif self.getpaths():
            return '[+] ' + os.path.basename(self.name) + '/'
        elif self.children is None:
            return '[?] ' + os.path.basename(self.name) + '/'
        else:
            return '[ ] ' + os.path.basename(self.name) + '/'

    def mkline(self, depth, width):
        pad = ' ' * 4 * depth
        path = self.getnode()
        node = pad + path
        if os.path.abspath(self.name) in self.sized:
            size = self.sized[os.path.abspath(self.name)]
        else:
            size = ''
        if self.name in self.picked:
            mark = ' *'
        else:
            mark = '  '
        node = node + mark
        sizelen = len(size)
        sizepad = width - sizelen
        nodestr = '{:<{w}}{:>}'.format(node, size, w=sizepad)
        return sizelen, sizepad, nodestr + ' ' * (width - len(nodestr))

    def drawline(self, depth, line, win):
        max_y, max_x = win.getmaxyx()
        offset = max(0, self.curline - max_y + 3)
        y = line - offset
        x = 0
        sizelen, sizepad, string = self.mkline(depth - 1, max_x)
        if 0 <= line - offset < max_y - 1:
            try:
                win.addstr(y, x, string)  # paint str at y, x co-ordinates
                if sizelen > 0 and line != self.curline:
                    win.chgat(y, sizepad, sizelen,
                              curses.A_BOLD | curses.color_pair(5))
            except curses.error:
                pass

    def drawtree(self):
        '''
        Loop over the object, process path attribute sets, and drawlines based
        on their current contents.
        '''
        self.win.erase()
        self.line = 0
        for child, depth in self.traverse():
            child.curline = self.curline
            child.picked = self.picked
            child.expanded = self.expanded
            child.sized = self.sized
            if depth == 0:
                continue
            if self.line == self.curline:
                self.color.curline(child.name, child.picked)
                children = child.children
                name = child.name
            else:
                self.color.default(child.name, child.picked)
            if child.name in self.sized and not self.sized[child.name]:
                self.sized[child.name] = " [" + du(child.name) + "]"
            child.drawline(depth, self.line, self.win)
            self.line += 1
        self.win.refresh()
        self.mkheader(name)
        self.mkfooter(name, children)
