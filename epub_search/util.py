# -*- coding: utf-8 -*-

# epub-search - ePub content searching program
# Copyright (C) 2013 Garrett Regier
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import itertools
import os
import zipfile


def epubs_in_path(path):
    # Must expand the path for os.path's functions to work
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        raise Exception('%r does not exist' % (path))

    if not os.path.isdir(path):
        if not zipfile.is_zipfile(path):
            raise Exception('%r is not an ePub' % (path))

        return [path]

    dir_paths = []
    for root, dirs, files in os.walk(path, followlinks=True):
        for child in files:
            if child.endswith('.epub'):
                # It is non-fatal if it is not actually
                # an ePub, a warning will be printed later
                dir_paths.append(os.path.join(root, child))

    dir_paths.sort(key=str.lower)
    return dir_paths


def unique(iterable):
    seen = set()
    seen_add = seen.add

    # Python 3 compat
    try:
        ifilterfalse = itertools.ifilterfalse
    except:
        ifilterfalse = itertools.filterfalse
    for element in ifilterfalse(seen.__contains__, iterable):
        seen_add(element)

        yield element

# ex:et:ts=4:
