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

**jag-tipdf** sequentially appends *INPUT*\s (or standard input if the file
name - is given) to a PDF file. By default, **jag-tipdf** sends the PDF file to
standard output. The *INPUT* can be either plain text or an image.

The PDF file is initially configured according to *global-options*. Then for
each *INPUT* its *input-options* are applied and the *INPUT* is appended to the
PDF file. 

OPTIONS
~~~~~~~

Once an *input-option* is specified, its value remains valid accross the
following *INPUT*\s. All *global-options* must precede the first *INPUT*,
otherwise they will have no effect.

Some options requires units which is 1/72 inch. There are several option value types:

* LIST comma separated list of items
* COLOR hexadecimal *rrggbb* value 
* STRING a string that contain variables

- %basename 
- %path
- %page
- %filestem

General Options
...............

-h, --help
 show a help message and exit

--version
 show program's version nubmer and exit


Common Input Options
....................

--margins=LIST
  tbd

-i, --image
  tbd

-t, --text
  tbd

--page=PAGE
  tbd

--page-color=COLOR
  tbd

--bookmark=STRING
  tbd

--separator=SEP
  tbd

--shell=CMD
  tbd

 

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
