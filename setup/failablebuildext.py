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

# Based on code found in simplejson:
# simplejson is dual-licensed software. It is available under the terms
# of the MIT license, or the Academic Free License version 2.1. The full
# text of each license agreement is included below. This code is also
# licensed to the Python Software Foundation (PSF) under a Contributor
# Agreement.

from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError
from distutils.errors import DistutilsExecError
from distutils.errors import DistutilsPlatformError

from setuptools import Extension as _Extension


class BuildFailed(Exception):
    pass


class FailableBuildExt(build_ext):
    """This class allows C extension building to fail."""

    BUILD_ERRORS = (CCompilerError, DistutilsExecError,
                    DistutilsPlatformError, IOError)

    def run(self):
        try:
            build_ext.run(self)

        except DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        if hasattr(ext, 'error'):
            sys.stderr.write(ext.error)
            return

        try:
            build_ext.build_extension(self, ext)

        except self.BUILD_ERRORS:
            raise BuildFailed()


class Extension(_Extension):
    def __init__(self, *args, **kwargs):
        if 'error' in kwargs:
            self.error = kwargs['error']
            del kwargs['error']

            args = ('Cannot be built', [])

        _Extension.__init__(self, *args, **kwargs)

# ex:et:ts=4:
