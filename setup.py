#!/usr/bin/env python
# -*- mode: python -*-
#
# Copyright (c) 2009 Jaroslav Gresula
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys

# check: 2.4 <= version < 3.0
py_major, py_minor = sys.version_info[0:2]
if sys.hexversion < 0x2040000:
    print >> sys.stderr, 'jag-tipdf requires Python version 2.4 or higher.'
    sys.exit(2)
 
import re
import os
import glob
import platform
from subprocess import Popen, PIPE
from string import Template


def program_exists(cmd):
    try:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        return p.returncode == 0
    except OSError:
        return False

def try_import(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False

def run_tests():
    """Run tests defined in file 'tests'"""
    dev_nul=os.devnull
    jag_tipdf = '"%s" jag-tipdf' % sys.executable
    txt = 'input/lipsum.txt'
    img = 'input/logo.png'
    sys.argv.remove('test')
    if not os.path.isdir('output'):
        os.mkdir('output')
    predicates = {'@req_convert': lambda: program_exists('convert -version'),
                  '@req_posix': lambda: os.name == 'posix',
                  '@req_pil': lambda: try_import('PIL'),
                  '@req_pygments': lambda: try_import('pygments')}
    retcode = 0
    nr_failures = 0
    for line in open('tests'):
        check_returncode = lambda x : x == 0
        line = line.strip()
        if not line or line[0] == '#':
            continue
        if line[0] == '@':
            meta, line = line.split(' ', 1)
            for m in meta.split(','):
                if m == '@fail':
                    check_returncode = lambda x: x != 0
                elif not predicates[m]():
                    line = None
                    break
        if not line:
            continue
        line = Template(line).substitute(locals())
        print line
        p = Popen(line, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if not check_returncode(p.returncode):
            print >>sys.stderr, 'FAILED:\n', err
            nr_failures += 1
            retcode = 1
    if nr_failures:
        print >>sys.stderr, '\nNUMBER OF FAILED TESTS:', nr_failures
    return retcode



from distutils.core import setup
import distutils.sysconfig
prefix = distutils.sysconfig.get_config_var('prefix')
for arg in sys.argv:
    if arg.startswith('--prefix='):
        prefix = arg.split('=')[1]
        break

if 'test' in sys.argv:
    sys.exit(run_tests())


is_sdist = 'sdist' in sys.argv
is_install = 'install' in sys.argv
system = platform.system()

scripts = ['jag-tipdf']
data_files = []

if is_sdist or (is_install and system == 'Linux'):
    MANDIR = os.path.join(prefix, 'share/man/man1')
    DOCDIR = os.path.join(prefix, 'share/doc/jag-tipdf')
    data_files = [(DOCDIR, ['README.rst'] + glob.glob('doc/*')),
                  (MANDIR, glob.glob('doc/jag-tipdf.1.gz'))]
    
if is_sdist or (is_install and system == 'Windows'):
    if is_install:
        import shutil
        if not os.path.isdir('tmp'):
            os.makedirs('tmp')
        shutil.copy('jag-tipdf', 'tmp/jag-tipdf.py')
        scripts.append('tmp/jag-tipdf.py')
    scripts.append('winlaunch/jag-tipdf.exe')
    

#
# standard distutils code
#
    
setup(name='jag-tipdf',
      version='0.2.0',
      description='Combines plain text and images into a single PDF.',
      author='Jaroslav Gresula',
      author_email='jarda@jagpdf.org',
      scripts=scripts,
      license="License :: OSI Approved :: MIT License",
      data_files = data_files,
      url='http://www.jagpdf.org/jag-tipdf',
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: MIT License",
                   "Environment :: Console",
                   "Operating System :: Microsoft :: Windows :: Windows NT/2000",
                   "Operating System :: POSIX :: Linux",
                   "Programming Language :: Python",
                   "Topic :: Multimedia :: Graphics :: Graphics Conversion",
                   "Topic :: Utilities",
                   "Topic :: Text Processing"])

# TBD
#  - setup(long_description="rst description")

