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

import argparse
import locale
import operator
import os
import sys

from epub_search import search
from epub_search import util


class LogLevel:
    (QUIET,
     DEFAULT,
     VERBOSE,
     DEBUG) = range(4)


class _EpubPathsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        paths = []

        for value in values:
            paths.extend(value)

        setattr(namespace, self.dest, paths)


def _epub_path(path):
    try:
        return util.epubs_in_path(path)

    except Exception as e:
        raise argparse.ArgumentTypeError(str(e))


def _parse_args(argv):
    parser = argparse.ArgumentParser(description='Search ePub contents.')
    parser.add_argument('-s', '--sort', default=None,
                        choices=['author', 'title'],
                        help='how the results should be sorted')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', action='store_true',
                       help='supress warning output')
    group.add_argument('-v', '--verbose', action='store_true',
                       help='output additional info')
    group.add_argument('--debug', action='store_true',
                       help=argparse.SUPPRESS)

    parser.add_argument('paths', metavar='PATH', nargs='+',
                        action=_EpubPathsAction, type=_epub_path,
                        help='list of epubs/paths to search in')
    parser.add_argument('pattern', metavar='PATTERN', action='store',
                        help='the text to search for')
    args = parser.parse_args(argv)

    if args.quiet:
        log_level = LogLevel.QUIET

    elif args.verbose:
        log_level = LogLevel.VERBOSE

    elif args.debug:
        log_level = LogLevel.DEBUG

    else:
        log_level = LogLevel.DEFAULT

    return args.pattern, tuple(util.unique(args.paths)), log_level, args.sort


def _result_name(result, sort):
    if sort is None:
        return os.path.basename(result.path)

    # Author is not required!
    author = result.author
    if author is None:
        author = 'Unknown'

    if sort == 'author':
        part_order = (author, result.title)

    else:
        part_order = (result.title, author)

    return ' - '.join(part_order)


def _epub_search(argv):
    # Required for formatting with thousand separator
    locale.setlocale(locale.LC_ALL, '')

    pattern, paths, log_level, sort = _parse_args(argv)

    results = []
    logged = False

    for result in search.search(paths, pattern):
        if result.error is not None:
            if log_level >= LogLevel.DEFAULT:
                logged = True
                sys.stderr.write("Error: %s\n" % (result.error))

        else:
            if result.warnings is not None and log_level >= LogLevel.VERBOSE:
                logged = True
                sys.stderr.write('Broken ePub file: %r\n\t%s\n' %
                                 (result.path,
                                  '\n\t'.join(result.warnings)))

            if result.n_matches > 0:
                results.append(result)

    # Separate the errors and warnings from the results
    if logged:
        print('\n')

    if not results:
        print('No matches found')

    else:
        if sort is None:
            # Sort by the order in which the paths were given
            key = lambda x: paths.index(x.path)

        else:
            key = lambda x: getattr(x, sort).lower()

        results = sorted(results, key=key)

        print('Matched {0:n} books out of {1:n}'.format(len(results),
                                                        len(paths)))

        max_matches = max(results, key=operator.attrgetter("n_matches"))
        max_matches_len = len('{0:n}'.format(max_matches.n_matches))

        # format() does not support providing the width in the arguments
        result_format = u'{0:>%in}  {1!s}' % (max_matches_len)

        for result in results:
            print(result_format.format(result.n_matches,
                                       _result_name(result, sort)))


def main(argv=None):
    try:
        _epub_search(argv)

    except KeyboardInterrupt:
        # Avoid printing a traceback
        return 1

    except SystemExit as e:
        # Return the exit code
        return e.code

    # Return success
    return 0


if __name__ == '__main__':
    sys.exit(main())

# ex:et:ts=4:
