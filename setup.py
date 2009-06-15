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
import re
import os
import glob
import platform


jagpdf_server = '192.168.1.138:8000'
jagpdf_server = 'jagpdf.org'
jagpdf_version_URL = 'http://' +  jagpdf_server + '/version'
jagpdf_downloads_URL = 'http://' + jagpdf_server + '/downloads/'

# check: 2.4 <= version < 3.0
py_major, py_minor = sys.version_info[0:2]
if py_major != 2 or py_minor < 4:
    print >> sys.stderr, 'jag-tipdf requires Python version 2.4 or higher.'
    sys.exit(2)

def fetch_file(url, err_msg=''):
    """Retrieves a resource from given url. Aborts on failure."""
    from urllib2 import urlopen, HTTPError, URLError
    def on_error(why):
        print >>sys.stderr, "\nERROR: Cannot retrieve", url
        print >>sys.stderr, "Reason:", str(why)
        if err_msg:
            print >>sys.stderr, err_msg
        sys.exit(3)
    try:
        return urlopen(url).read()
    except HTTPError, why:
        on_error(why)
    except URLError, why:
        on_error(why)

def verify_checksum(tarball_url, tarball_data):
    if py_minor < 5:
        import md5
        md5_creator = md5.new
    else:
        import hashlib
        md5_creator = hashlib.md5
    print "fetching checksum"
    md5_data = fetch_file(tarball_url + '.md5')
    expected_digest = md5_data.split()[0]
    md5_obj = md5_creator()
    md5_obj.update(tarball_data)
    if expected_digest != md5_obj.hexdigest():
        print >>sys.stderr, "Checksum failed, aborting."
    print "checksum ok"

def report_err(msg, what=''):
    """Prints an erorr message to stderr and exits."""
    print >> sys.stderr, 'ERROR:', msg, what
    sys.exit(2)
        
def fetch_jagpdf():
    """Fetches the JagPDF library from http://jagpdf.org"""
    # check write access to site_packages/ early to avoid repetitive library
    # downloads if the user forgets to run this script with administrative
    # privileges
    from distutils.sysconfig import get_python_lib
    prefix = None
    for arg in sys.argv:
        if arg.startswith('--prefix='):
            prefix = arg.split('=')[1]
            break
    site_packages = get_python_lib(prefix=prefix)
    if not os.access(site_packages, os.W_OK):
        report_err("%s not writable." % site_packages)
    processor = platform.machine()
    if processor.endswith('86'):
        processor = 'x86'
    if sys.platform.startswith('linux'):
        op_sys = 'linux'
    else:
        op_sys = sys.platform.lower()
    py_version = "%d%d" % sys.version_info[0:2]
    print 'determining the latest JagPDF version'
    version = fetch_file(jagpdf_version_URL, \
                         "Cannot determine JagPDF version").strip()
    print version
    stem = 'jagpdf-%s.%s.%s.py%s' % (version, op_sys, processor, py_version)
    from cStringIO import StringIO
    if op_sys.startswith('win'):
        print >>sys.stderr, '--fetch-jagpdf not implemented on windows yet'
        sys.exit(1)
        import zipfile
        tarball_url = jagpdf_downloads_URL + stem + '.zip'
        zip = zipfile.ZipFile(StringIO(urlopen(tarball_url).read()), 'r')
    else:
        import tarfile
        import shutil
        from subprocess import Popen, PIPE
        tarball_url = jagpdf_downloads_URL + stem + '.tar.bz2'
        print "fetching JagPDF for your platform (%s.%s)" % (processor, op_sys)
        data = fetch_file(tarball_url, """
This might indicate, that JagPDF is not available for your platform. Please
check JagPDF homepage at http://jagpdf.org.""")
        verify_checksum(tarball_url, data)
        try:
            print "unbzipping"
            bzcat = Popen(["bzcat"], stdin=PIPE, stdout=PIPE)
            out, err = bzcat.communicate(data)
        except OSError:
            report_err("bzcat not found. Cannot continue.")
        tar = tarfile.open("nonexistent", 'r', StringIO(out))
        rex = re.compile('(_jagpdf[^/]*.so$)|(/jagpdf.py$)')
        jagpdf_files = [f for f in tar.getmembers() if rex.search(f.name)]
        assert len(jagpdf_files) == 2
        print 'copying JagPDF files to', site_packages
        tar.extractall(members=jagpdf_files)
        tar.close()
        for f in jagpdf_files:
            shutil.move(f.name, site_packages)
        print 'cleanup'
        shutil.rmtree(stem)
        print 'JagPDF installation done.'

def custom_install():
    """Checks for JagPDF, download and install it optionally."""
    # should be JagPDF fetched automatically?
    if '--fetch-jagpdf' in sys.argv:
        fetch_jagpdf_flag = True
        sys.argv.remove('--fetch-jagpdf')
    else:
        fetch_jagpdf_flag = False
    # try to import jagpdf
    try:
        if not fetch_jagpdf_flag:
            import jagpdf
    except ImportError:
        quest = """
jag-tipdf requires the JagPDF library, which is not installed on your system.
Do you want to download it and install it now?
(y/n/q)[Enter] """
        response = ''
        while (not response) or (response not in 'YyNnQq'):
            response = raw_input(quest)
            if not response:
                continue
            if response in 'Yy':
                fetch_jagpdf_flag = True
            elif response in 'Nn':
                notice = """
The installation will continue but you have to install JagPDF later. Otherwise
jag-tipdf will not work. See JagPDF installation instructions at
http://www.jagpdf.org/doc/jagpdf/installation.htm
[Enter] """
                raw_input(notice)
            elif response in 'Qq':
                sys.exit(1)
    if fetch_jagpdf_flag:
        fetch_jagpdf()
        try:
            print "trying to import japgdf:",
            import jagpdf
            print "ok"
        except ImportError:
            print "FAILED\nAborting."
            sys.exit(3)

if 'install' in sys.argv:
    custom_install()

#
# standard distutils code
#
from distutils.core import setup

if platform.system() == 'Linux':
    data_files = [('/usr/local/share/doc/jag-tipdf', ['README.rst'] + glob.glob('doc/*')),
                  ('/usr/local/share/man/man1', glob.glob('doc/jag-tipdf.1.gz'))]
else:
    data_files = []
    
setup(name='jag-tipdf',
      version='0.1.0',
      description='Combines plain text and images into a single PDF.',
      author='Jaroslav Gresula',
      author_email='jarda@jagpdf.org',
      scripts=['jag-tipdf.py'],
      license="License :: OSI Approved :: MIT License",
      data_files = data_files,
      classifiers=["Development Status :: 3 - Alpha",
                   "License :: OSI Approved :: MIT License",
                   "Environment :: Console",
                   "Operating System :: Microsoft :: Windows :: Windows NT/2000"
                   "Operating System :: POSIX :: Linux",
                   "Programming Language :: Python",
                   "Topic :: Multimedia :: Graphics :: Graphics Conversion",
                   "Topic :: Utilities",
                   "Topic :: Text Processing"])


#
# TBD
# -----
#  --fetch-jagpdf
#    - implement on windows
#    - compile to pyc during install
#  setup(url='http://www.jagpdf.org/?')

