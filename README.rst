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
- font face, size, and color,
- character and line spacing,
- encryption - user permissions, owner and user passwords,
- page dimensions, margins, and color,
- initial document view,
- n-up imposition,
- bookmarks,
- zebra,
- PNG and JPEG images, PIL_ or imagemagick_ is used for other image types (if
  available),
- syntax highlighting (requires Pygments_)
- `form feed <http://en.wikipedia.org/wiki/Form_feed#Form_feed>`_ support,

.. _PIL: http://www.pythonware.com/products/pil/
.. _imagemagick: http://www.imagemagick.org/script/index.php
.. _Pygments: http://pygments.org


Installation
~~~~~~~~~~~~

[TBD]

Download
~~~~~~~~

The software is in an alpha state, the develepment branch is available at
`GitHub <http://github.com/jgresula/jag-tipdf>`_.

To clone the branch, do: ::

 $ git clone git://github.com/jgresula/jag-tipdf.git    

Examples
-------------------

::

 $ lynx -nolist -dump http://www.catb.org/~esr/faqs/smart-questions.html | jag-tipdf.py -
 $ find . -name '*.txt' -print0 | xargs -0 ./jag-tipdf.py --bookmark=%basename -
 $ < /dev/urandom tr -dc '!-~' | head -c1048576 | fold | jag-tipdf.py - 

Manual
------

[TBD]


