import sys
from setuptools import setup

import epub_search


if sys.version_info < (2, 7, 0):
    sys.stderr.write('epub-search requires Python 2.7 or newer.\n')
    sys.exit(1)


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

# ex:et:ts=4:
