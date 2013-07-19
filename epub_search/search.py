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

from collections import namedtuple

from epub_search import epub


_search_result_fields = ('path', 'title', 'author',
                         'n_matches', 'error', 'warnings')


class SearchResult(namedtuple('SearchResult', _search_result_fields)):
    """Represents a result from search()

    Only the path field is always available. The error field will not
    be None when parsing the ePub fails.

    path: path of the ePub
    title: the ePub's title
    author: the author of the ePub
    n_matches: the numer of matches
    error: error message if parsing failed
    warnings: warnings gernerated while parsing the ePub
    """

    # namedtuple requires all fields
    def __new__(cls, path, title=None, author=None, n_matches=0,
                error=None, warnings=None):
        return super(SearchResult, cls).__new__(cls, path, title, author,
                                                n_matches, error, warnings)


def _search_epub(path, to_match):
    if isinstance(path, epub.Epub):
        epub_file = path
        path = epub_file.path

    else:
        try:
            epub_file = epub.Epub(path)

        except epub.BadEpubError as e:
            # For bad ePubs, return a SearchResult with the error set
            return SearchResult(path=path, error=str(e))

    with epub_file:
        n_matches = 0

        for content in epub_file.contents:
            n_matches += content.text.count(to_match)

        return SearchResult(path=path, title=epub_file.title,
                            author=epub_file.author, n_matches=n_matches,
                            warnings=epub_file.warnings)


def search(paths, to_match):
    for path in paths:
        yield _search_epub(path, to_match)

# ex:et:ts=4:
