.. -*- mode: rst; coding: utf-8; -*-

.. To be able to process this file without Pygments, syntax higlighting is not
.. enabled by default. So a modified syntax is used for code blocks:
..  .. sourcecode <lang>
..  <empty-line>
..  ::
.. To enable syntax highlighting, the file must be preprocessed with the
.. following sed expressions:
..   s/.. sourcecode/.. sourcecode::/g
..   s/^::$$//g

.. The manual page is generated from this file as well. Its start is marked with
.. the 'manpage-start' label. When generating the manpage, the contents of
.. this file is skipped up to that label is skipped and replaced with man.rst.



=========
jag-tipdf
=========
:Author: Jaroslav Gresula
:Contact: jarda@jagpdf.org
:Version: 0.1-alpha
:Date: $Date:$
:License: `MIT License <http://www.opensource.org/licenses/mit-license.php>`_

.. contents::

What is it?
~~~~~~~~~~~

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


Obtaining
~~~~~~~~~

The software is in an alpha state, the development branch is available at
`GitHub <http://github.com/jgresula/jag-tipdf>`_.

To clone the branch, do:

 .. sourcecode console

::

   $ git clone git://github.com/jgresula/jag-tipdf.git    


Installation
~~~~~~~~~~~~

To install jag-tipdf, run

 .. sourcecode console

::

   $ python setup.py install

If JagPDF is not installed on your system, you can use ``--fetch-jagpdf``, which
downloads and installs prebuilt JagPDF (Linux only). Otherwise you have to
install JagPDF `manually <http://www.jagpdf.org/doc/jagpdf/installation.htm>`_.

Optionally, you can run tests:

 .. sourcecode  console

::

   $ python setup.py test


Examples
~~~~~~~~

The following commands send PDF to stdout.

 .. sourcecode console

::

   $ lynx -nolist -dump http://www.catb.org/~esr/faqs/smart-questions.html | jag-tipdf -
   $ find . -name '*.txt' -print0 | xargs -0 jag-tipdf --bookmark=%basename
   $ < /dev/urandom tr -dc '!-~' | head -c1048576 | fold | jag-tipdf - 
   $ find /usr/share/man/man1 -name '*.gz' | \
   >     sort | \
   >     xargs jag-tipdf \
   >     --shell="man \`basename %filestem | cut -d. -f1\` | col -b" \
   >     --bookmark=%filestem


Manual
~~~~~~

This is the the html version of the man page.

.. manpage-start

SYNOPSIS
^^^^^^^^
**jag-tipdf** [*global-options*] [[*input-options*] *INPUT*] ...

DESCRIPTION
^^^^^^^^^^^

**jag-tipdf** sequentially appends *INPUT*\ s (or standard input if the file
name - is given) to a PDF file. By default, **jag-tipdf** sends the PDF file to
standard output. The *INPUT* can be either a path to a local file or a URL.

The PDF file is initially configured according to *global-options*. Then for
each *INPUT* its *input-options* are applied and the *INPUT* is appended to the
PDF file.

The *INPUT* can be either plain text or an image. **jag-tipdf** natively
supports JPEG and PNG image formats. Where available, other formats are
supported through conversion to PNG using PIL (Python Imaging Library) or
imagemagick.

OPTIONS
^^^^^^^

Once an *input-option* is specified, its value remains valid accross the
following *INPUT*\s. All *global-options* must precede the first *INPUT*,
otherwise they will have no effect.

There are several option argument types:

* LIST comma separated list of items
* COLOR hexadecimal *rrggbb* value 
* STRING a string that can contain the following variables
  * %basename 
  * %path
  * %page
  * %filestem

* UNITS 1/72 inch

General Options
...............

-h, --help
 show a help message and exit

--version
 show program's version number and exit


Common Input Options
....................

--input-type=TYPE
  Set the type of the *INPUT*. If *TYPE* set to **auto** and the file has a known
  image extension then **jag-tipdf** treats the *INPUT* as an image, otherwise as
  plain text. The option arguments **text** and **image** explicitly set the
  type of the input. You might need to use this option if an image comes from
  stdin, or if the file has a non-standard extension. Default value: **auto**.

--page=FORMAT
  Set the page size. *FORMAT* can be either **A4**, **Letter**, or *width*,\
  *height* in units. Default value: **A4**

--page-color=COLOR
  Set the page background color.

--margins=MARGINS
  Set page margins. *MARGINS* is a *top*,\ *right*,\ *bottom*,\ *left* list.

--bookmark=STRING
  Add a node labeled with *STRING* to the bookmark tree and associate it with
  the *INPUT*.

--separator=SPACE
  Separate the *INPUT* from the previous one by adding vertical *SPACE*. *SPACE*
  can be either a distance (even negative) expressed in units or **break** which
  inserts a page break. Default value: **break**.

--shell=CMD
  Execute *CMD* through the shell and use its stdout instead of the original
  *INPUT*.

Text Input Options
..................
--font=FONT
  Show text using *FONT*. *FONT* can be either a path to a font program or a
  core font name. Core names for monospaced fonts are: **Courier**,
  **Courier-Bold**, **Courier-Oblique**, and **Courier-BoldOblique**. Using core
  fonts usually leads to smaller PDFs. Default value: **Courier**.

--font-size=SIZE
  Set font size.

--text-color=COLOR
  Set text color.

--encoding=ENC
  Specify text encoding. If a file variable -\*- coding: -\*- is found in the
  first two lines of the input, then it overrides this option and its value is
  used instead. Default value: **iso-8859-1**.

--zebra=COLORS
  Paint a zebra with *COLORS*. *COLORS* is a list of colors.

--char-spacing=FACTOR
  Scale character spacing with *FACTOR*. Positive *FACTOR* values increase
  character spacing whereas negative values have the opposite effect. Default
  value is 0.

--line-spacing=FACTOR
  Scale character spacing with *FACTOR*. Positive *FACTOR* values increase the
  distance between individual lines of text whereas negative values have the
  opposite effect. Default value is 0.

--highlight, --no-highlight
  Turn syntax highlighting on/off. This feature requires Pygments
  (http://pygments.org). Default: turned off



Image Input Options
...................

--image-align=MODE
  Set the image alignment mode. *MODE* can be **left**, **center**, or
  **right**. Default value: **left**.

--image-fit-wide, --no-image-fit-wide
  Resize the image if it is wider than the page. Default: turned on

--image-dpi=DPI
  Use *DPI* instead of the dpi specified in the image.

Global Options
..............
-o, --output-file=FILE
  Send output to *FILE* instead of stdout.

--initial-dest=DEST
  Set the initial destination. This option determines how the resulting PDF is
  initially displayed. Possible values are **fitv** - fit page height to window,
  **fith** - fit page width to window, **fit** - fit page to window, or a number
  specifying the zoom factor - factor **1.0** corresponds to 100%.

--full-screen
  The resulting PDF will be initially displayed in full-screen mode.

--page-layout=LAYOUT
  Specify the initial page layout. *LAYOUT* can be **single**, **cont**, or
  **cont-facing**.

--owner-pwd=PWD
  Set the owner password.

--user-pwd=PWD
  Set the user password.

--user-perm=PERM
  Set access permissions. *PERM* can be a combination of **no_print**,
  **no_modify**, and **no_copy**.

--n-up=N
  Perform imposition of 2^\ *N* pages on a sheet. Default value: **0**

--doc-name=NAME
  Set the document name. The name is displayed in the document's window title
  bar. If not specified, then the name of the PDF file is displayed.




BUGS
^^^^
Report bugs to <jagpdf@googlegroups.com>.

AUTHOR
^^^^^^
Written by Jaroslav Gresula <jarda@jagpdf.org>.



