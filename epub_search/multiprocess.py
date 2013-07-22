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

import multiprocessing
import os
import sys


class TimeoutError(Exception):
    pass


def _process_init():
    # Disable printing in forked processes
    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')


def _process_call(all_args):
    # multiprocessing screws up and sends the args as a tuple
    func, args = all_args

    return func(*args)


class Job(object):
    # TODO: multiprocessing.freeze_support()

    try:
        __CPU_COUNT = multiprocessing.cpu_count()

    except NotImplementedError:
        # All recent processors have at least 2 cores
        __CPU_COUNT = 2

    def __init__(self, func, iterable):
        if not hasattr(iterable, '__iter__'):
            iterable = list(iterable)

        iterable = [(func, x) if hasattr(x, '__iter__') else (func, (x,))
                    for x in iterable]

        n_processes = min(self.__CPU_COUNT, len(iterable))

        # Prevent "No child processes" exception
        while 1:
            try:
                self.__pool = multiprocessing.Pool(processes=n_processes,
                                                   initializer=_process_init)
                break

            except OSError:
                continue

        # Chunksize is required to be 1 for next() to accept a timeout
        self.__results = self.__pool.imap_unordered(_process_call,
                                                    iterable, 1)

        self.__pool.close()

    def __iter__(self):
        return self

    def next(self, timeout=None):
        if self.__results is None:
            raise StopIteration

        # If a timeout is not used and the child processes
        # quits (KeyboardInterrupt), this would block forever
        real_timeout = timeout if timeout is not None else 600

        while 1:
            try:
                return self.__results.next(real_timeout)

            except multiprocessing.TimeoutError:
                if timeout is not None:
                    raise TimeoutError()

                continue

            except StopIteration:
                self.terminate()
                raise

    __next__ = next

    def terminate(self):
        if self.__results is not None:
            self.__pool.terminate()
            self.__results = None

# ex:et:ts=4:
