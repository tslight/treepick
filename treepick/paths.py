# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import os

from .keys import Keys


class Paths(Keys):
    def __init__(self,
                 screen,
                 name,
                 hidden,
                 picked=[],
                 expanded=set(),
                 sized=dict()):
        Keys.__init__(self,
                      screen,
                      name,
                      hidden,
                      picked,
                      expanded,
                      sized)
        self.paths = None
        self.children = self.getchildren()

    def listdir(self, path):
        '''
        Return a list of all non dotfiles in a given directory.
        '''
        for f in os.listdir(path):
            if not f.startswith('.'):
                yield f

    def getchildren(self):
        '''
        Create list of absolute paths to be used to instantiate path objects
        for traversal, based on whether or not hidden attribute is set.
        '''
        try:
            if self.hidden:
                return [os.path.join(self.name, child)
                        for child in sorted(self.listdir(self.name))]
            else:
                return [os.path.join(self.name, child)
                        for child in sorted(os.listdir(self.name))]
        except OSError:
            return None  # probably permission denied

    def getpaths(self):
        '''
        If we have children, use a list comprehension to instantiate new paths
        objects to traverse.
        '''
        self.children = self.getchildren()
        if self.children is None:
            return
        if self.paths is None:
            self.paths = [Paths(self.screen,
                                os.path.join(self.name, child),
                                self.hidden,
                                self.picked,
                                self.expanded,
                                self.sized)
                          for child in self.children]
        return self.paths

    def traverse(self):
        '''
        Recursive generator that lazily unfolds the filesystem.
        '''
        yield self, 0
        if self.name in self.expanded:
            for path in self.getpaths():
                for child, depth in path.traverse():
                    yield child, depth + 1
