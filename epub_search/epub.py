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

"""ePub metadata and content parsing."""

from collections import namedtuple
import posixpath
import urllib
import zipfile

from lxml import etree as ElementTree

from epub_search.tag_stripper import TagStripError, TagStripper


_Item = namedtuple('_Item', ('path', 'media_type'))

_CONTAINER_PATH = 'META-INF/container.xml'

_MIMETYPE_NCX = 'application/x-dtbncx+xml'
_MIMETYPE_OPF = 'application/oebps-package+xml'
_MIMETYPE_XHTML = 'application/xhtml+xml'

_NAMESPACES = {
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'ncx': 'http://www.daisy.org/z3986/2005/ncx/',
    'opf': 'http://www.idpf.org/2007/opf'}


def _XPATH(expr):
    try:
        xpath = ElementTree.XPath(expr, namespaces=_NAMESPACES,
                                  regexp=False, smart_strings=False)

    except ElementTree.XPathSyntaxError as e:
        raise Exception('Failed to parse %r: %s' % (expr, e))

    # Stupid lxml!
    if '[1]' in expr:
        def xpath_single_result(e):
            result = xpath(e)
            if not result:
                return None

            return result[0]

        return xpath_single_result

    return xpath


_XPATH_ROOT_FILES = _XPATH('./container:rootfiles/container:rootfile')
_XPATH_METADATA = _XPATH('./opf:metadata[1]')
_XPATH_METADATA_TITLE = _XPATH('./dc:title[1]/text()')
_XPATH_METADATA_CREATORS = _XPATH('./dc:creator')
_XPATH_CREATOR_IS_AUTHOR = _XPATH('./@opf:role="aut"')

_XPATH_ITEMS = _XPATH('./opf:manifest/opf:item[@id][@href][@media-type]')
_XPATH_TOC_ID = _XPATH('./opf:spine[1]/@toc')
_XPATH_IDREFS = _XPATH('./opf:spine/opf:itemref/@idref')

_XPATH_NAV_POINTS = _XPATH('./ncx:navMap/ncx:navPoint')
_XPATH_NAV_POINT_TEXT = _XPATH('./ncx:navLabel/ncx:text[1]/text()')
_XPATH_NAV_POINT_CONTENT_SRC = _XPATH('./ncx:content[1]/@src')


class BadEpubError(Exception):
    """The error raised for bad ePubs files."""


EpubContent = namedtuple('EpubContent', ('path', 'label', 'xhtml', 'text'))


class Epub(object):
    """Parses an ePub's metadata and content.

    This is not meant to be a full ePub parsing class, but
    a simple and fast solution for what is needed.
    """

    def __init__(self, path):
        self.__path = path

        self.__title = None
        self.__author = None
        self.__warnings = []
        self.__items = None
        self.__contents = []
        self.__tag_stripper = None

        # These are automatically closed by __epub_error()
        self.__epub_file = None
        self.__epub_zipfile = None

        try:
            # zipfile.ZipFile.open() will open the filename
            # per call unless a file object was passed in
            self.__epub_file = open(path, 'rb')

        except Exception as e:
            raise self.__epub_error(str(e))

        try:
            self.__epub_zipfile = zipfile.ZipFile(self.__epub_file, 'r')

        except zipfile.BadZipfile:
            raise self.__epub_error('File is not an ePub file')

        # Set the path prefix to the root
        # until real prefix is determined
        self.__path_prefix = ''

        content_path = self.__get_content_path()
        self.__opf = self.__open_and_parse(content_path)

        # All future paths will be in this prefix
        self.__path_prefix = posixpath.dirname(content_path)

        # Set the metadata fields
        self.__parse_metadata()

    def close(self):
        if self.__epub_file is not None:
            if self.__epub_zipfile is not None:
                self.__epub_zipfile.close()
                self.__epub_zipfile = None

            self.__epub_file.close()
            self.__epub_file = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def __epub_error(self, msg):
        self.close()

        # Return the exception so callers must raise
        # it and this causes the tracebacks to be correct
        return BadEpubError('Invalid ePub file: %r: %s' % (self.__path, msg))

    def __epub_warning(self, msg):
        self.__warnings.append(msg)

    def __open(self, path):
        full_path = posixpath.join(self.__path_prefix, path)

        try:
            return self.open(full_path)

        except Exception as e:
            raise self.__epub_error('Failed to open %r: %s' % (full_path, e))

    def __open_and_parse(self, path):
        xml = self.__open(path)

        try:
            return ElementTree.fromstring(xml)

        except Exception as e:
            full_path = posixpath.join(self.__path_prefix, path)
            raise self.__epub_error('Failed to parse %r: %s' % (full_path, e))

    def __get_content_path(self):
        container = self.__open_and_parse(_CONTAINER_PATH)

        rootfiles = _XPATH_ROOT_FILES(container)
        if not rootfiles:
            raise self.__epub_error('Failed to find rootfile in %r' %
                                    (_CONTAINER_PATH))

        content_path = None
        for rootfile in rootfiles:
            # First root file with the OPF
            # mime-type, any others are alternative views
            if rootfile.get('media-type', None) == _MIMETYPE_OPF:
                content_path = rootfile.get('full-path', None)
                break

        if content_path is None:
            raise self.__epub_error('Failed to find full-path for '
                                    'rootfile in %r' % (_CONTAINER_PATH))

        return content_path

    def __parse_metadata(self):
        metadata = _XPATH_METADATA(self.__opf)
        if metadata is None:
            raise self.__epub_error('Failed to find metadata')

        title = _XPATH_METADATA_TITLE(metadata)
        if title is None:
            raise self.__epub_error('Failed to find title')

        self.__title = title.strip()

        # Creator is not a required tag
        creators = _XPATH_METADATA_CREATORS(metadata)
        if creators:
            # Set the author to the first creator
            # in case the author role was not found
            self.__author = creators[0].text.strip()

            for i in xrange(1, len(creators)):
                if _XPATH_CREATOR_IS_AUTHOR(creators[i]):
                    self.__author = creators[i].text.strip()
                    break

    def __get_manifest(self):
        items = _XPATH_ITEMS(self.__opf)
        if not items:
            raise self.__epub_error('Failed to find items in %r' %
                                    (content_path))

        manifest = {}
        for item in items:
            # The XPath requires that these attributes exist
            item_id = item.get('id')
            item_href = item.get('href')
            item_media_type = item.get('media-type')

            manifest[item_id] = _Item(path=urllib.unquote(item_href),
                                      media_type=item_media_type)

        return manifest

    def __get_item_labels(self, manifest):
        toc_item = manifest.get(_XPATH_TOC_ID(self.__opf), None)
        if toc_item is None or toc_item.media_type != _MIMETYPE_NCX:
            return {}

        # TODO: maybe this should only warn?
        nav_points = _XPATH_NAV_POINTS(self.__open_and_parse(toc_item.path))
        if not nav_points:
            return {}

        item_labels = {}
        for nav_point in nav_points:
            text = _XPATH_NAV_POINT_TEXT(nav_point)
            src = _XPATH_NAV_POINT_CONTENT_SRC(nav_point)
            if text is None or src is None:
                continue

            item_labels[urllib.unquote(src)] = text.strip()

        return item_labels

    def __parse_items(self):
        manifest = self.__get_manifest()
        item_labels = self.__get_item_labels(manifest)

        idrefs = _XPATH_IDREFS(self.__opf)
        if not idrefs:
            self.__epub_warning('Failed to find contents')
            return

        for idref in idrefs:
            item = manifest.get(idref, None)
            if item is None or item.media_type != _MIMETYPE_XHTML:
                continue

            # This is exposed to the user so
            # must be capable of being open()'ed
            path = posixpath.join(self.__path_prefix, item.path)

            # Allow unknown labels
            label = item_labels.get(item.path, None)

            self.__items.append((path, label))

    def open(self, path):
        """Returns the data located by @path."""

        return self.__epub_zipfile.open(path).read()

    @property
    def path(self):
        """Returns the ePub's path."""

        return self.__path

    @property
    def title(self):
        """Returns the ePub's title."""

        return self.__title

    @property
    def author(self):
        """Returns the ePub's author, or None."""

        return self.__author

    @property
    def contents(self):
        """Returns the ePub's contents as EpubContent objects."""

        if self.__items is None:
            self.__items = []
            self.__tag_stripper = TagStripper()

            self.__parse_items()

        for content in self.__contents:
            yield content

        while self.__items:
            path, label = self.__items.pop(0)

            try:
                # path is the full path (with self.__path_prefix)
                xhtml = self.open(path)

            except Exception as e:
                self.__epub_warning('Failed to open %r: %s' % (path, e))
                continue

            try:
                text = self.__tag_stripper(xhtml)

            except TagStripError as e:
                self.__epub_warning('Failed to strip tags from %r: %s' %
                                    (path, e))
                text = None

            content = EpubContent(path, label, xhtml, text)

            # We must add the contents to the internal
            # list before yielding as we might stop generating
            self.__contents.append(content)

            yield content

    @property
    def warnings(self):
        """Returns the warnings generated while parsing the ePub.

        Because the ePub's contents are parsed lazily this
        may not represent all of the warnings.
        """

        if not self.__warnings:
            return None

        # Prevent callers from modifying
        return tuple(self.__warnings)

# ex:et:ts=4:
