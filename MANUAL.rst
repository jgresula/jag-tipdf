Manual
------
.. manpage-start

=========
jag-tipdf
=========

combines plain text and images into PDF
---------------------------------------
:Manual section: 1

.. manpage-header-end

SYNOPSIS
~~~~~~~~
**jag-tipdf** [*global-options*] [[*input-options*] *INPUT*] ...

DESCRIPTION
~~~~~~~~~~~

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
~~~~~~~

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
  Add vertical *SPACE* after the *INPUT*. *SPACE* can be either a distance (even
  negative) expressed in units or **break** which inserts a page break. Default
  value: **break**.

--shell=CMD
  Execute *CMD* through the shell and use its stdout instead of the original
  *INPUT*.

 
 

Text Input Options
..................

Image Input Options
...................

Document Level Options
......................




BUGS
~~~~
Report bugs to <jagpdf@googlegroups.com>.

AUTHOR
~~~~~~
Written by Jaroslav Gresula <jarda@jagpdf.org>.
