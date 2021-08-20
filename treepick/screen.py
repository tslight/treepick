# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import curses
import getpass
import grp
import os
import pwd
import socket

from .color import Color


class Screen:
    def __init__(self, screen, picked):
        curses.curs_set(0)  # get rid of cursor
        self.screen = screen
        self.y, self.x = self.screen.getmaxyx()
        self.header = curses.newwin(0, self.x, 0, 0)
        self.win = curses.newwin(self.y - 3, self.x, 2, 0)
        self.footer = curses.newwin(0, self.x, self.y - 1, 0)
        self.screen.refresh()
        self.win.refresh()
        self.pad = curses.newpad(self.y, self.x)
        self.footer.refresh()
        self.header.refresh()
        self.picked = picked
        self.color = Color(self.win)
        self.lc, self.pos = (0,)*2

    def resize(self):
        self.screen.erase()
        self.y, self.x = self.screen.getmaxyx()
        self.header.resize(1, self.x)
        self.win.resize(self.y - 3, self.x)
        if self.lc:
            self.pad.resize(self.lc + 2, self.x)
        self.footer.mvwin(self.y - 1, 0)
        self.footer.resize(1, self.x)
        self.screen.refresh()
        self.header.refresh()
        self.win.refresh()
        self.footer.refresh()

    def mkheader(self, path):
        user = getpass.getuser()
        host = socket.gethostname()
        userhost = user + "@" + host
        msg = userhost + " " + path
        msg = (msg[:self.x - 3] + '..') if len(msg) > self.x - 3 else msg
        try:
            self.header.addstr(0, 0, msg)
            self.header.clrtoeol()  # more frugal than erase. no flicker.
            self.header.chgat(0, 0, len(userhost),
                              curses.A_BOLD | curses.color_pair(2))
            self.header.chgat(0, len(userhost) + 1,
                              curses.A_BOLD | curses.color_pair(3))
        except curses.error:
            pass
        self.header.refresh()

    def mkfooter(self, path, children=None):
        from datetime import datetime
        user = pwd.getpwuid(os.stat(path).st_uid)[0]
        group = grp.getgrgid(os.stat(path).st_gid)[0]
        usergroup = user + " " + group

        mtime = os.path.getmtime(path)
        mdate = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

        mode = oct(os.stat(path).st_mode)[-3:]

        if children:
            children = len(children)
        else:
            children = 0

        msg = usergroup + " " + mdate + " " + mode + " " + str(children)
        msg = (msg[:self.x - 3] + '..') if len(msg) > self.x - 3 else msg
        try:
            self.footer.addstr(0, 0, msg)
            self.footer.clrtoeol()  # more frugal than erase. no flicker.
            self.footer.chgat(0, 0, len(usergroup), curses.A_BOLD |
                              curses.color_pair(2))
            self.footer.chgat(0, len(usergroup) + 1, len(mdate),
                              curses.A_BOLD | curses.color_pair(3))
            self.footer.chgat(0, len(usergroup) + len(mdate) + 2, len(mode),
                              curses.A_BOLD | curses.color_pair(6))
            self.footer.chgat(0, len(usergroup) + len(mdate) + len(mode) + 2,
                              curses.A_BOLD | curses.color_pair(5))
        except curses.error:
            pass
        self.footer.refresh()

    def mktb(self, prompt):
        from curses.textpad import Textbox
        length = len(prompt)
        self.footer.erase()
        self.footer.addstr(prompt)
        self.footer.chgat(0, 0, length, curses.A_BOLD | curses.color_pair(3))
        curses.curs_set(1)
        self.footer.refresh()
        tb = self.footer.subwin(self.y - 1, length)
        box = Textbox(tb)
        box.edit()
        curses.curs_set(0)
        result = box.gather()
        self.footer.erase()
        return result

    def mkpadfooter(self):
        footstr = "[j,k,f,b] or [DOWN, UP, PGUP, PGDN] to scroll."
        footstr += " [q] or [ESC] to return."
        startch = [i for i, ltr in enumerate(footstr) if ltr == "["]
        endch = [i for i, ltr in enumerate(footstr) if ltr == "]"]
        self.footer.addstr(0, 0, footstr)
        for i in range(len(startch)):
            self.footer.chgat(0, startch[i], endch[i] - startch[i] + 1,
                              curses.A_BOLD | curses.color_pair(3))
        self.screen.refresh()
        self.footer.refresh()

    def mkkeypad(self):
        from textwrap import dedent
        msg = '''
            UP, k             : Step up one line.
            DOWN, j           : Step down one line.
            K                 : Jump to previous parent directory.
            J                 : Jump to next parent directory.
            PGDN, f           : Jump down a page of lines.
            PGUP, b           : Jump up a page of lines.
            HOME, g           : Jump to first line.
            END, G            : Jump to last line.
            RIGHT, l          : Expand and step into directory.
            TAB, RET          : Toggle expansion/collapse of directory.
            LEFT, h           : Collapse directory.
            SHIFT RIGHT, L    : Expand directory and child directories.
            SHIFT LEFT, H     : Jump to parent directory and collapse all.
            SPC               : Toggle picking of paths.
            v                 : Toggle picking of all currently expanded paths.
            :                 : Toggle picking of paths based on entered globs.
            p                 : View a list of all picked paths.
            /                 : Search for an entered string.
            n                 : Jump to next occurrence of last search string.
            N                 : Jump to prev occurrence of last search string.
            .                 : Toggle display of dotfiles.
            s                 : Display total size of path, recursively
            S                 : Display totol size of all expanded paths.
            F4, r             : Reset picked paths.
            F5, R             : Reset picked paths, expansion and size display.
            F1, ?             : View this help page.
            q, ESC            : Quit and display all marked paths.
            '''
        msg = dedent(msg).strip()
        self.lc = len(msg.splitlines())
        self.screen.erase()
        self.pad.erase()
        self.pad.resize(self.lc + 2, self.x)
        try:
            self.pad.addstr(0, 0, msg)
            self.pad.scrollok(1)
            self.pad.idlok(1)
            self.mkpadfooter()
        except curses.error:
            pass
        self.getpadkeys()

    def mkpickpad(self):
        self.screen.erase()
        self.pad.erase()
        self.pad.resize(len(self.picked) + 2, self.x)
        try:
            if self.picked:
                self.pad.addstr(0, 0, "\n".join(self.picked))
            else:
                self.pad.addstr(0, 0, "You haven't picked anything yet!")
                self.pad.chgat(0, 0, curses.color_pair(1) | curses.A_BOLD)
            self.mkpadfooter()
        except curses.error:
            pass
        self.lc = len(self.picked)
        self.getpadkeys()
