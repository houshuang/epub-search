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


class Match(object):
    __slots__ = ('text', 'match_positions')

    def __init__(self, text, match_positions):
        self.text = text
        # Prevent modification
        self.match_positions = tuple(match_positions)

    def __match_parts(self):
        current_position = 0

        # All matching functions find only non-overlapping occurrences
        for start, end in self.match_positions:
            yield False, self.text[current_position:start]
            yield True, self.text[start:end]

            current_position = end

        yield False, self.text[current_position:]

    def __len__(self):
        return len(self.match_positions)

    def __str__(self):
        return self.text

    def escape(self, escape_func):
        escaped = []
        match_positions = []
        current_position = 0

        for is_match, part in self.__match_parts():
            escaped_part = escape_func(part)
            len_escaped_part = len(escaped_part)

            if is_match:
                match_positions.append((current_position,
                                        current_position + len_escaped_part))

            escaped.append(escaped_part)
            current_position += len_escaped_part

        return Match(''.join(escaped), match_positions)

    def format(self, start_match_text, end_match_text):
        formatted = []

        for is_match, part in self.__match_parts():
            if not is_match:
                formatted.append(part)
                continue

            formatted.extend((start_match_text, part, end_match_text))

        return ''.join(formatted)


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

    def __str_context_match(self, string):
        start = 0
        pattern_len = len(self.__pattern)

        while 1:
            match = string.find(self.__pattern, start)
            if match == -1:
                break

            start = match + pattern_len

            yield match, start

    def __regex_context_match(self, string):
        for match in self.__pattern.finditer(string):
            yield match.start(0), match.end(0)

    def match(self, string):
        if not isinstance(string, basestring):
            raise TypeError('\'basestring\' argument expected, got %r.' %
                            (type(string).__name__))

        # Must always keep orignal for matching with ignore case,
        # otherwise the returned paragraph matched would be all lower case
        orig_string = string

        if self.__is_regex:
            match_func = self.__regex_context_match
        else:
            # Regular expressions are compiled to be case insensitive
            if self.ignore_case:
                string = string.lower()

            match_func = self.__str_context_match

        match = None
        start_para = 0
        end_para = -1

        for start, end in match_func(string):
            if end <= end_para:
                match[1].append((start - start_para, end - start_para))
                continue

            if match is not None:
                yield Match(*match)

            start_para = string.rfind('\n', 0, start) + 1
            end_para = string.find('\n', end, -1)

            # Only end_para has this corner case, it is
            # required for combining multiple matches at the end
            if end_para == -1:
                end_para = len(string)

            while start_para < start and string[start_para].isspace():
                start_para += 1

            # Due to how slicing works we want to check
            # the character prior to the current end_para
            while end_para > end and string[end_para - 1].isspace():
                end_para -= 1

            match = (orig_string[start_para:end_para],
                     [(start - start_para, end - start_para)])

        # Make sure we yield the final match
        if match is not None:
            yield Match(*match)

# ex:et:ts=4:
