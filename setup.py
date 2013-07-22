import sys

from setuptools import setup

import epub_search
from setup.enviroment import extensions
from setup.failablebuildext import BuildFailed, FailableBuildExt


if sys.version_info < (2, 7, 0):
    sys.stderr.write('epub-search requires Python 2.7 or newer.\n')
    sys.exit(1)


def run_setup(with_extensions):
    setup(name='epub-search',
          version=epub_search.__version__,
          description=epub_search.__doc__,
          long_description=open('README', 'r').read(),
          license=epub_search.__license__,
          keywords='epub search',
          author=epub_search.__author__,
          author_email='garrettregier@gmail.com',
          url='http://github.com/gregier/epub-search',
          install_requires=['lxml'],
          packages=['epub_search'],
          ext_modules=[] if not with_extensions else extensions,
          cmdclass={'build_ext': FailableBuildExt},
          entry_points={
              'console_scripts': [
                  'epub-search = epub_search.__main__:main']},
          platforms=['any'],
          classifiers=[
              'Development Status :: 3 - Alpha',
              'Topic :: Utilities',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: 2.7',
              'License :: OSI Approved :: '
              'GNU General Public License v2 or later (GPLv2+)'])


# TODO: use itertools.combinations() to try building any extensions
try:
    run_setup(True)

except BuildFailed:
    sys.stderr.write('\n%s\n'
                     'WARNING: The C extension could not be compiled, '
                     'speedups are not enabled.\n'
                     'Failure information, if any, is above.\n'
                     'I\'m retrying the build without the C extension now.\n'
                     '%s\n\n' % (('*' * 75,) * 2))

    run_setup(False)

    sys.stderr.write('\n%s\n'
                     'WARNING: The C extension could not be compiled, '
                     'speedups are not enabled.\n'
                     'Plain-Python build succeeded.\n'
                     '%s\n' % (('*' * 75,) * 2))


# ex:et:ts=4:
