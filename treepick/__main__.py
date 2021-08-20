# Copyright (c) 2018, Toby Slight. All rights reserved.
# ISC License (ISCL) - see LICENSE file for details.

import argparse
import curses
import cgitb
import os

from .paths import Paths
# Get more detailed traceback reports
cgitb.enable(format="text")  # https://pymotw.com/2/cgitb/


def chkpath(path):
    """
    Checks if a path exists.
    """
    if os.path.exists(path):
        return path
    else:
        msg = "{0} does not exist.".format(path)
        raise argparse.ArgumentTypeError(msg)


def getargs():
    """
    Return a list of valid arguments.
    """
    parser = argparse.ArgumentParser(description='\
    Select paths from a directory tree.')
    parser.add_argument("-a", "--hidden", action="store_false",
                        help="Show all hidden paths too.")
    parser.add_argument("-r", "--relative", action="store_true",
                        help="Output relative paths.")
    parser.add_argument("path", type=chkpath, nargs='?',
                        default=".", help="A valid path.")
    return parser.parse_args()


def get_picked(relative, root, picked):
    if relative:
        if root.endswith(os.path.sep):
            length = len(root)
        else:
            length = len(root + os.path.sep)
        return [p[length:] for p in picked]
    return picked


def pick(screen, root, hidden=True, relative=False, picked=[]):
    picked = [root + p for p in picked]
    parent = Paths(screen, root, hidden, picked=picked, expanded=set([root]))
    picked = parent.getkeys()
    return get_picked(relative, root, picked)


def main(picked=[]):
    args = getargs()
    root = os.path.abspath(os.path.expanduser(args.path))
    hidden = args.hidden
    relative = args.relative
    paths = curses.wrapper(pick, root, hidden, relative)
    print("\n".join(paths))


if __name__ == '__main__':
    main()
