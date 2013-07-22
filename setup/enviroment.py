# -*- coding: utf-8 -*-

# epub-search - ePub content searching program
# Copyright (C) 2013 Garrett Regier
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os

from failablebuildext import Extension


class ExtensionError(Exception):
    pass


extensions = []


expat_include_dirs = ('/usr/include', '/usr/local/include')
expat_library_dirs = ('/lib', '/usr/lib', '/usr/local/lib')

if all(not os.path.exists(x + '/expat.h') for x in expat_include_dirs):
    extensions.append(Extension(error='Not building expat extension: %s' %
                                      ('Failed to find includes')))

else:
    extensions.append(Extension('epub_search._speedups_expat',
                                ['epub_search/speedups/expat.c'],
                                libraries=['expat'],
                                library_dirs=expat_library_dirs,
                                include_dirs=expat_include_dirs))


# Not really worth it right now
#try:
#    extensions.append(Extension('epub_search.speedups.libxml',
#                      ['epub_search/speedups/libxml.c'],
#                       libraries=pkgconfig_libs('libxml-2.0'),
#                       library_dirs=pkgconfig_lib_dirs('libxml-2.0'),
#                       include_dirs=pkgconfig_include_dirs('libxml-2.0')))

#except ExtensionError as e:
#    extensions.append(Extension('Not building libxml2 extension: %s' % (e)))

# ex:et:ts=4:
