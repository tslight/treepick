# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os
import fnmatch

from .draw import Draw


class Actions(Draw):
    def __init__(self,
                 screen,
                 name,
                 hidden,
                 picked=[],
                 expanded=set(),
                 sized=dict()):
        Draw.__init__(self, screen, picked, expanded, sized)
        self.name = name
        self.hidden = hidden
        self.globs, self.matches = (None,)*2
        self.lastpath, self.lasthidden = (None,)*2

    ###########################################################################
    #                          QUIT AND RESET METHODS                         #
    ###########################################################################

    def quit(self):
        return True

    def reset_all(self):
        self.curline = 0
        self.picked = []
        self.expanded = set([self.name])
        self.sized = {}

    def reset_picked(self):
        self.picked = []

    ###########################################################################
    #                          LINE MOVEMENT METHODS                          #
    ###########################################################################

    def dn(self):
        self.curline += 1

    def up(self):
        self.curline -= 1

    def pgdn(self):
        self.curline += self.y
        if self.curline >= self.line:
            self.curline = self.line - 1

    def pgup(self):
        self.curline -= self.y
        if self.curline < 0:
            self.curline = 0

    def top(self):
        self.curline = 0

    def bottom(self):
        self.curline = self.line - 1

    ###########################################################################
    #                           LINE JUMPING METHODS                          #
    ###########################################################################

    def nextparent(self, parent, depth):
        '''
        Add lines to current line by traversing the grandparent object again
        and once we reach our current line counting every line that is prefixed
        with the parent directory.
        '''
        if depth > 1:  # can't jump to parent of root node!
            pdir = os.path.dirname(self.name)
            line = 0
            for c, d in parent.traverse():
                if line > parent.curline and c.name.startswith(pdir):
                    parent.curline += 1
                line += 1
        else:  # otherwise just skip to next directory
            line = -1  # skip hidden parent node
            for c, d in parent.traverse():
                if line > parent.curline:
                    parent.curline += 1
                    if os.path.isdir(c.name) and c.name in parent.children[0:]:
                        break
                line += 1

    def prevparent(self, parent, depth):
        '''
        Subtract lines from our curline if the name of a node is prefixed with
        the parent directory when traversing the grandparent object.
        '''
        pdir = os.path.dirname(self.name)
        if depth > 1:  # can't jump to parent of root node!
            for c, d in parent.traverse():
                if c.name == self.name:
                    break
                if c.name.startswith(pdir):
                    parent.curline -= 1
        else:  # otherwise jus skip to previous directory
            pdir = self.name
            # - 1 otherwise hidden parent node throws count off & our
            # self.curline doesn't change!
            line = -1
            for c, d in parent.traverse():
                if c.name == self.name:
                    break
                if os.path.isdir(c.name) and c.name in parent.children[0:]:
                    parent.curline = line
                line += 1
        return pdir

    ###########################################################################
    #                       EXPAND AND COLLAPSE METHODS                       #
    ###########################################################################

    def expand(self, parent):
        self.expanded.add(self.name)
        parent.curline += 1

    def expand_all(self, parent):
        if os.path.isdir(self.name) and self.children:
            self.expanded.add(self.name)
            for c, d in self.traverse():
                if d < 2 and os.path.isdir(c.name) and c.children:
                    self.expanded.add(c.name)
            parent.curline += 1

    def toggle_expand(self):
        if self.name in self.expanded:
            self.expanded.remove(self.name)
        else:
            self.expanded.add(self.name)

    def collapse(self):
        if self.name in self.expanded:
            self.expanded.remove(self.name)

    def collapse_all(self, parent, depth):
        if depth > 1:
            p = self.prevparent(parent, depth)
            self.expanded.remove(p)
            for x in list(self.expanded):  # iterate over copy
                par = os.path.abspath(p)
                path = os.path.abspath(x)
                if path.startswith(par):
                    self.expanded.remove(x)
        else:
            self.collapse()

    ###########################################################################
    #                           PATH PICKING METHODS                          #
    ###########################################################################

    def pick(self, parent):
        if self.name in self.picked:
            self.picked.remove(self.name)
        else:
            self.picked.append(self.name)
        parent.curline += 1

    def pickall(self):
        for c, d in self.traverse():
            if d == 0:
                continue
            if c.name in self.picked:
                self.picked.remove(c.name)
            else:
                self.picked.append(c.name)

    def pickglobs(self):
        self.globs = self.mktb("Pick: ").strip().split()
        if self.globs:
            for c, d in self.traverse():
                for g in self.globs:
                    if (fnmatch.fnmatch(c.name, g) or
                            fnmatch.fnmatch(os.path.basename(c.name), g)):
                        if c.name in self.picked:
                            self.picked.remove(c.name)
                        else:
                            self.picked.append(c.name)

    ###########################################################################
    #                            SEARCHING METHODS                            #
    ###########################################################################

    def find(self):
        string = self.mktb("Find: ").strip()
        if string:
            self.matches = []
            line = -1
            for c, d in self.traverse():
                if string in os.path.basename(c.name):
                    self.matches.append(line)
                line += 1
            if self.matches:
                self.findnext()

    def findnext(self):
        for m in range(len(self.matches)):
            if self.curline == self.matches[len(self.matches) - 1]:
                self.curline = self.matches[0]
                break
            elif self.curline < self.matches[m]:
                self.curline = self.matches[m]
                break

    def findprev(self):
        for m in range(len(self.matches)):
            if self.curline <= self.matches[m]:
                self.curline = self.matches[m-1]
                break

    ###########################################################################
    #                         SIZE AND HIDING METHODS                         #
    ###########################################################################

    def getsize(self, parent):
        self.sized[os.path.abspath(self.name)] = None
        parent.curline += 1

    def getsizeall(self):
        for c, d in self.traverse():
            self.sized[os.path.abspath(c.name)] = None

    def toggle_hidden(self):
        self.paths = None

        if self.hidden:
            # keep two copies of record so we can restore from state when
            # re-hiding
            self.lastpath = self.children[self.curline]
            self.hidden = False
        else:
            # keep two copies of record so we can restore from state
            self.lasthidden = self.children[self.curline]
            self.hidden = True

        self.drawtree()

        if self.lasthidden in self.children:
            self.curline = self.children.index(self.lasthidden)
        elif self.lastpath in self.children:
            self.curline = self.children.index(self.lastpath)

    ###########################################################################
    #                           PAD MOVEMENT METHODS                          #
    ###########################################################################

    def pad_dn(self):
        if self.pos < self.lc - self.y + 1:
            self.pos += 1

    def pad_up(self):
        if self.pos > 0:
            self.pos -= 1

    def pad_pgdn(self):
        self.pos += self.y - 1
        if self.pos >= self.lc - self.y + 1:
            self.pos = self.lc - self.y + 1

    def pad_pgup(self):
        self.pos -= self.y - 1
        if self.pos < 0:
            self.pos = 0
