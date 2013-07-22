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

import xml.parsers.expat

from lxml import etree as ElementTree

try:
    from epub_search import _speedups_expat

except ImportError:
    _speedups_expat = None


class TagStripError(Exception):
    """The error raised when stripping tags fails."""


class _TagStripperBase(object):
    __NEWLINE_TAGS = set(('p', 'div', 'br',
                          'h1', 'h2', 'h3', 'h4', 'h5', 'h6'))

    def __call__(self, xhtml):
        parts = []
        parts_append = parts.append
        newline_tags = self.__NEWLINE_TAGS

        def end_element_handler(name):
            if name in newline_tags:
                parts_append('\n')

        def start_element_handler(name, attrs):
            if name == 'body':
                self.set_start_element_handler(None)
                self.set_end_element_handler(end_element_handler)
                self.set_character_handler(parts_append)

        self.set_start_element_handler(start_element_handler)
        self.set_end_element_handler(None)
        self.set_character_handler(None)

        self.parse(xhtml)

        return ''.join(parts)


if _speedups_expat is not None:
    class _ExpatTagStripper(object):
        __slots__ = ()

        @staticmethod
        def __call__(xhtml):
            try:
                return _speedups_expat.strip_tags(xhtml)

            except ValueError as e:
                raise TagStripError(e)

else:
    class _ExpatTagStripper(_TagStripperBase):
        __slots__ = ('__parser',)

        def __init__(self):
            self.__parser = xml.parsers.expat.ParserCreate()

            # Avoid join()ing thousands of strings
            # a decent buffer size is used
            self.__parser.buffer_text = True

            # Faster to parse str than unicode
            self.__parser.returns_unicode = False

        def parse(self, xhtml):
            try:
                self.__parser.Parse(xhtml, True)

            except xml.parsers.expat.ExpatError as e:
                raise TagStripError(e)

        def set_start_element_handler(self, value):
            self.__parser.StartElementHandler = value

        def set_end_element_handler(self, value):
            self.__parser.EndElementHandler = value

        def set_character_handler(self, value):
            self.__parser.CharacterDataHandler = value


class _LxmlTagStripper(_TagStripperBase):
    __slots__ = ('__parser', '__target')

    class __LxmlTarget(object):
        __slots__ = ('data_handler', 'end_handler', 'start_handler')

        @staticmethod
        def __get_tag(tag):
            return tag.split('}', 1)[1] if '}' in tag else tag

        def start(self, tag, attrs):
            if self.start_handler is not None:
                self.start_handler(self.__get_tag(tag), attrs)

        def end(self, tag):
            if self.end_handler is not None:
                self.end_handler(self.__get_tag(tag))

        def data(self, string):
            if self.data_handler is not None:
                self.data_handler(string)

        def close(self):
            pass

    def __init__(self):
        self.__target = self.__LxmlTarget()
        self.__parser = ElementTree.XMLParser(recover=True,
                                              target=self.__target)

    def parse(self, xhtml):
        try:
            ElementTree.fromstring(xhtml, parser=self.__parser)

        except ElementTree.ParseError as e:
            raise TagStripError(e)

    def set_start_element_handler(self, value):
        self.__target.start_handler = value

    def set_end_element_handler(self, value):
        self.__target.end_handler = value

    def set_character_handler(self, value):
        self.__target.data_handler = value


class TagStripper(object):
    """Strips the tags from an XHTML string.

    Supports a fast mode for properly formatted XHTML with fallbacks
    for broken XHTML. Once a fallback method has been used it will
    continue to be used by subsequent calls on that instance.
    """

    def __init__(self):
        self.__tag_stipper = _ExpatTagStripper()
        self.__tag_stippers = (_LxmlTagStripper,)

    def __call__(self, xhtml):
        while 1:
            try:
                return self.__tag_stipper(xhtml.replace('\n', ' '))

            except TagStripError:
                if not self.__tag_stippers:
                    raise

                self.__tag_stipper = self.__tag_stippers[0]()
                self.__tag_stippers = self.__tag_stippers[1:]

# ex:et:ts=4:
