.. -*- mode: rst; coding: utf-8; -*-

=========
jag-tipdf
=========
:Author: Jaroslav Gresula
:Contact: jarda@jagpdf.org
:Version: 0.1-alpha
:Date: $Date:$
:License: `MIT License <http://www.opensource.org/licenses/mit-license.php>`_

.. contents::

Introduction
------------

Overview
~~~~~~~~

jag-tipdf is a command line utility that combines plain text and images into a
single PDF. It is written in Python and it uses the `JagPDF library
<http://jagpdf.org>`_ under the hood. It runs on x86/Linux and x86/Windows.

Features
~~~~~~~~

- General

  - page dimensions, margins, and color,
  - bookmarks,
  - n-up imposition,
  - encryption - user permissions, owner and user passwords,
  - initial document view,
  - `form feed <http://en.wikipedia.org/wiki/Form_feed#Form_feed>`_ support,

- Text

  - font face, size, and color,
  - text encoding support,
  - character and line spacing,
  - syntax highlighting (requires Pygments_),
  - encoding detection from a file variable (-\*- coding: -\*-),
  - zebra,

- Images

  - PNG and JPEG images, PIL_ or imagemagick_ are used for conversion from other
    image types (if available),
  - image alignment


.. _PIL: http://www.pythonware.com/products/pil/
.. _imagemagick: http://www.imagemagick.org/script/index.php
.. _Pygments: http://pygments.org

Download
~~~~~~~~

The software is in an alpha state, the development branch is available at
`GitHub <http://github.com/jgresula/jag-tipdf>`_.

To clone the branch, do:

 .. sourcecode:: console

   $ git clone git://github.com/jgresula/jag-tipdf.git    


Installation
~~~~~~~~~~~~

To install jag-tipdf, run

 .. sourcecode:: console

   $ python setup.py install

If JagPDF is not installed on your system, you can use ``--fetch-jagpdf``, which
downloads and installs prebuilt JagPDF (Linux only). Otherwise you have to
install JagPDF `manually <http://www.jagpdf.org/doc/jagpdf/installation.htm>`_.

Optionally, you can run tests:

 .. sourcecode:: console
 
   $ python setup.py test


Examples
--------

The following commands send PDF to stdout.

 .. sourcecode:: console

   $ lynx -nolist -dump http://www.catb.org/~esr/faqs/smart-questions.html | jag-tipdf -
   $ find . -name '*.txt' -print0 | xargs -0 ./jag-tipdf --bookmark=%basename
   $ < /dev/urandom tr -dc '!-~' | head -c1048576 | fold | jag-tipdf - 
   $ find /usr/share/man/man1 -name '*.gz' | \
   >     sort | \
   >     xargs ./jag-tipdf \
   >     --shell="man \`basename %filestem | cut -d. -f1\` | col -b" \
   >     --bookmark=%filestem





