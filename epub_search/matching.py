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

import re


class Matcher(object):
    def __init__(self, to_match, ignore_case, use_regex):
        self.to_match = to_match
        self.ignore_case = ignore_case
        self.use_regex = use_regex

        if not use_regex:
            self.__is_regex = False

        else:
            # List of special characters taken from re's docs
            self.__is_regex = any(True for x in to_match
                                  if x in set('.^$*+?{}\\[]|()'))

        self.__pattern = self.__get_pattern()

    def __get_pattern(self):
        pattern = self.to_match

        if not self.__is_regex:
            if not self.ignore_case:
                return pattern

            return pattern.lower()

        # Matching is done with the whole file not
        # line by line so allow proper use of ^ and $
        flags = re.MULTILINE

        if self.ignore_case:
            flags |= re.IGNORECASE

        return re.compile(pattern, flags)

    def count(self, string):
        if not isinstance(string, basestring):
            raise TypeError('\'basestring\' argument expected, got %r.' %
                            (type(string).__name__))

        # Regular expressions are compiled to be case insensitive
        if not self.__is_regex:
            return string.count(self.__pattern)

        if self.ignore_case:
            string = string.lower()

        return len(self.__pattern.findall(string))

# ex:et:ts=4:
