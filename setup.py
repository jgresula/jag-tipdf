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
from cStringIO import StringIO
from subprocess import Popen, PIPE
from string import Template


jagpdf_server = '192.168.1.138:8000'
jagpdf_server = 'jagpdf.org'
jagpdf_version_URL = 'http://' +  jagpdf_server + '/version'
jagpdf_downloads_URL = 'http://' + jagpdf_server + '/downloads/'

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
    except (HTTPError, URLError), why:
        on_error(why)

        
def verify_checksum(tarball_url, tarball_data):
    """Fetches a checksum for given url and uses it to verify data"""
    try:
        import hashlib
        md5_creator = hashlib.md5
    except ImportError:
        import md5
        md5_creator = md5.new
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

    
def get_platform_info():
    """Retrieves (processor, operating-system) tuple"""
    import struct
    if struct.calcsize('P') > 4:
        report_err("Prebuilt JagPDF is available for 32-bit Python only.")
    processor = platform.machine()
    if not processor:
        try:
            processor = os.environ['PROCESSOR_ARCHITECTURE']
        except KeyError:
            report_err("Cannot determine your processor type.")
    if processor.endswith('86'):
        processor = 'x86'
    if sys.platform.startswith('linux'):
        op_sys = 'linux'
    else:
        op_sys = sys.platform.lower()
    return processor, op_sys


class JagPDFDownloader:
    """Base class for downloading and installing JagPDF"""
    def __init__(self, url):
        self.tarball_url = url

    def fetch(self):
        self.data = fetch_file(self.tarball_url, """
This might indicate, that prebuilt JagPDF is not available for your
platform. For more information, please visit the JagPDF homepage at
http://jagpdf.org.""")
        verify_checksum(self.tarball_url, self.data)


class JagPDFDownloaderWin(JagPDFDownloader):
    """Downloads and installs JagPDF on Windows."""
    def __init__(self, stem):
        JagPDFDownloader.__init__(self, jagpdf_downloads_URL + stem + '.zip')

    def unpack(self, site_packages):
        import zipfile
        zip = zipfile.ZipFile(StringIO(self.data), 'r')
        rex = re.compile('(_jagpdf[^/]*.pyd$)|(/jagpdf.py$)')
        jagpdf_files = [f for f in zip.namelist() if rex.search(f)]
        assert len(jagpdf_files) == 2
        for f in jagpdf_files:
            base = os.path.basename(f)
            dest = os.path.join(site_packages, base)
            print 'copying %s -> %s' % (base, dest)
            data = zip.read(f)
            open(dest, 'wb').write(data)
            

class JagPDFDownloaderLinux(JagPDFDownloader):
    """Downloads and installs JagPDF on Linux"""
    def __init__(self, stem):
        JagPDFDownloader.__init__(self, jagpdf_downloads_URL + stem + '.tar.bz2')
        self.stem = stem

    def unpack(self, site_packages):
        import tarfile
        import shutil
        try:
            print "unbzipping"
            bzcat = Popen(["bzcat"], stdin=PIPE, stdout=PIPE)
            out, err = bzcat.communicate(self.data)
        except OSError:
            report_err("bzcat not found. Cannot continue.")
        tar = tarfile.open("nonexistent", 'r', StringIO(out))
        rex = re.compile('(_jagpdf[^/]*.so$)|(/jagpdf.py$)')
        jagpdf_files = [f for f in tar.getmembers() if rex.search(f.name)]
        assert len(jagpdf_files) == 2
        tar.extractall(members=jagpdf_files)
        tar.close()
        for f in jagpdf_files:
            print 'copying %s -> %s' % (os.path.basename(f.name), site_packages)
            shutil.move(f.name, site_packages)
        print 'cleanup'
        shutil.rmtree(self.stem)

        
def fetch_jagpdf():
    """Fetches the prebuilt JagPDF library from http://jagpdf.org"""
    # check write access to site_packages/ early to avoid repetitive library
    # downloads if the user forgets to run this script with administrative
    # privileges
    from distutils.sysconfig import get_python_lib
    site_packages = get_python_lib(prefix=prefix)
    if not os.path.isdir(site_packages):
        try:
            os.makedirs(site_packages)
        except (OSError, IOError), why:
            report_err("cannot create %s, %s" % (site_packages, str(why)))
    elif not os.access(site_packages, os.W_OK):
        report_err("%s not writable." % site_packages)
    processor, op_sys = get_platform_info()
    py_version = "%d%d" % sys.version_info[0:2]
    print 'determining the latest JagPDF version'
    version = fetch_file(jagpdf_version_URL, \
                         "Cannot determine JagPDF version").strip()
    print version
    # download and install proper prebuilt package
    if op_sys.startswith('win'):
        down_cls = JagPDFDownloaderWin
    else:
        down_cls = JagPDFDownloaderLinux
    stem = 'jagpdf-%s.%s.%s.py%s' % (version, op_sys, processor, py_version)
    downloader = down_cls(stem)
    print "fetching JagPDF for your platform (%s.%s)" % (processor, op_sys)
    downloader.fetch()
    downloader.unpack(site_packages)
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


def run_tests():
    """Run tests defined in file 'tests'"""
    dev_nul=os.devnull
    jag_tipdf = 'python jag-tipdf'
    sys.argv.remove('test')
    retcode = 0
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
                else:
                    assert 'unknown meta command'
        line = Template(line).substitute(locals())
        print line
        p = Popen(line, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if not check_returncode(p.returncode):
            print >>sys.stderr, 'FAILED:\n', err
            retcode = 1
    return retcode



from distutils.core import setup
import distutils.sysconfig
prefix = distutils.sysconfig.get_config_var('prefix')
for arg in sys.argv:
    if arg.startswith('--prefix='):
        prefix = arg.split('=')[1]
        break

if 'install' in sys.argv:
    custom_install()

if 'test' in sys.argv:
    sys.exit(run_tests())
    

if platform.system() == 'Linux':
    MANDIR = os.path.join(prefix, 'share/man/man1')
    DOCDIR = os.path.join(prefix, 'share/doc/jag-tipdf')
    data_files = [(DOCDIR, ['README.rst'] + glob.glob('doc/*')),
                  (MANDIR, glob.glob('doc/jag-tipdf.1.gz'))]
else:
    data_files = []

#
# standard distutils code
#
    
setup(name='jag-tipdf',
      version='0.1.0',
      description='Combines plain text and images into a single PDF.',
      author='Jaroslav Gresula',
      author_email='jarda@jagpdf.org',
      scripts=['jag-tipdf'],
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
#    - compile to pyc during install
#  tests - figure out python interpreter path (see var jag_tipdf)
#  setup(url='http://www.jagpdf.org/?')

