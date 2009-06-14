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

__version__ = "0.1-alpha"
__author__ = 'jgresula@jagpdf.org (Jaroslav Gresula)'
__doc__ = "Combines plain text and images into a single PDF."

import sys
try:
    import jagpdf
except ImportError:
    sys.stderr.write("""
This application requires the JagPDF library. It seems that it is not installed
on your system. The application cannot continue.
""")
    sys.exit(1)
from optparse import OptionParser, OptionValueError, OptionGroup
import re
import os
from urllib2 import urlopen, HTTPError, URLError


class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class Error(Exception):        
    def __init__(self, msg):
        self.msg = msg


class PDFStream(jagpdf.StreamOut):
    def __init__(self, opts):
        if opts.outfile == '-':
            self.out = sys.stdout
        else:
            self.out = open(opts.outfile, 'wb')
        jagpdf.StreamOut.__init__(self)
        
    def write(self, data):
        self.out.write(data)

    def close(self):
        self.out.close()



# ======================================================================
#                       Formatting

def enough_space_on_page(ctx, y):
    return ctx.y - y >= ctx.opts.margins.bottom()


def place_bookmark(ctx):
    if ctx.opts.bookmark:
        spec = 'mode=XYZ; top=%.02f' % ctx.y
        expanded = subst_template(ctx, ctx.opts.bookmark)
        ctx.doc.outline().item(expanded, spec)

def subst_template(ctx, text):
    s = {'%basename' : os.path.basename(ctx.input_name),
         '%path' : ctx.input_name,
         '%page' : str(ctx.paging.page_nr + 1)}
    def replace(match):
        return s[match.group(0)]
    rex_str = "|".join([k for k in s.iterkeys()])
    return re.compile(rex_str).sub(replace, text)

def insert_input_separator(ctx):
    if ctx.opts.separator == PageBreak:
        ctx.paging.next_page()
    elif ctx.opts.separator > 0.0:
        if enough_space_on_page(ctx, ctx.opts.separator):
            ctx.y -= ctx.opts.separator
        else:
            ctx.paging.next_page()
    else:
        ctx.y = min(ctx.y - ctx.opts.separator,
                    ctx.opts.page[1] - ctx.opts.margins.top())
    

#----------------------------------------------------------------------
#                         Images

def place_inline_image(ctx, img, w, h):
    if ctx.opts.image_fit_wider and w > ctx.opts.margins.canvas_width():
        fit_wider_image(ctx, img, w, h)
        return
    if not enough_space_on_page(ctx, h):
        ctx.paging.next_page()
    canvas = ctx.doc.page().canvas()
    if ctx.opts.image_align == 'left':
        offset = 0
    elif ctx.opts.image_align == 'center':
        offset = (ctx.opts.margins.canvas_width() - w) / 2.0
    elif ctx.opts.image_align == 'right':
        offset = ctx.opts.margins.canvas_width() - w
    place_bookmark(ctx)
    ctx.y -= h    
    canvas.image(img, ctx.opts.margins.left() + offset, ctx.y)

def fit_wider_image(ctx, img, w, h):
    scale = ctx.opts.margins.canvas_width() / w
    if not enough_space_on_page(ctx, scale*h):
        ctx.paging.next_page()
    canvas = ctx.doc.page().canvas()
    canvas.state_save()
    place_bookmark(ctx)
    ctx.y -= scale * h
    canvas.translate(ctx.opts.margins.left(), ctx.y)
    canvas.scale(scale, scale)
    canvas.image(img, 0, 0)
    canvas.state_restore()

def paint_image(ctx, stream):
    img = load_image(ctx, stream)
    w = img.width() / img.dpi_x() * 72
    h = img.height() / img.dpi_y() * 72
    place_inline_image(ctx, img, w, h)

def load_image_imagemagick(ctx, img_data):
    try:
        from subprocess import Popen, PIPE
        convert = Popen(["convert", "-", "png:-"], stdin=PIPE, stdout=PIPE)
        out, err = convert.communicate(img_data)
        if convert.returncode != 0:
            raise Error("convert failed with %d\n%s" % (convert.returncode, err))
        return load_image_to_document(ctx, out)
    except OSError:
        return None # imagemagick not found

def load_image_pil(ctx, img_data):
    try:
        from PIL import Image
        from cStringIO import StringIO
        pil_img = Image.open(StringIO(img_data))
        png = StringIO()
        pil_img.save(png, "PNG")
        return load_image_to_document(ctx, png.getvalue())
    except ImportError, exc:
        return None

def load_image_to_document(ctx, img_data):
    imgdef = ctx.doc.image_definition()
    if ctx.opts.image_dpi:
        imgdef.dpi(ctx.opts.image_dpi, ctx.opts.image_dpi)
    imgdef.data(img_data)
    return ctx.doc.image_load(imgdef)
    

def load_image(ctx, stream):
    if ctx.input_name in ctx.img_cache:
       return ctx.img_cache[ctx.input_name]
    try:
        img = load_image_to_document(ctx, stream.read())
    except jagpdf.Exception:
        # the input stream contains unsupported image format, try to convert it
        for load_method in [load_image_pil,
                            load_image_imagemagick]:
            img = load_method(ctx, img_data)
            if img:
                break
    if not img:
        raise Error("Unsupported image format.")
    ctx.img_cache[ctx.input_name] = img
    return img


# ----------------------------------------------------------------------
#                           Text

def show_text(ctx, stream):
    if ctx.opts.highlight:
        highlight_text(ctx, stream)
    else:
        iter_lines(ctx, stream)

def highlight_text(ctx, stream):
    try:
        import pygments
        from pygments import lex
        from pygments.lexers import get_lexer_for_filename
        from pygments.styles import get_style_by_name
        lexer = get_lexer_for_filename(ctx.input_name)
        lexer.encoding = ctx.opts.encoding
        lexer.tabsize = ctx.opts.tabsize
        token_iter = lex(stream.read(), lexer)
        print lexer
        style = get_style_by_name('default')
        driver = TxtDriver(ctx, style)
        for token in token_iter:
            print token
            if not enough_space_on_page(ctx, driver.line_height()):
                driver.on_next_page()
            if token[1].endswith('\n'):
                if len(token[1]) > 1:
                    driver.on_text(token[1][0:-1])
                driver.on_line_end()
            elif token[0] == '\f':
                driver.on_next_page()
            else:
                driver.on_text(token[1], token[0])
    except ImportError:
        raise Error("Pygments not installed, cannot highlight")
    except pygments.util.ClassNotFound, exc:
        raise Error("Pygments error: " + str(exc))
        
def iter_lines(ctx, stream):
    if ctx.opts.encoding != 'utf-8':
        import codecs
        reader_factory = codecs.getreader(ctx.opts.encoding)
        stream = reader_factory(stream)
    driver = TxtDriver(ctx)
    expand_tabs = ctx.opts.tabsize * ' '
    for line in stream.readlines():
        line.replace('\t', expand_tabs)
        spans = [s for s in line.split('\f')]
        while spans:
            span = spans.pop(0)
            if span != '':
                if not enough_space_on_page(ctx, driver.line_height()):
                    driver.on_next_page()
                driver.on_text(span.rstrip())
                driver.on_line_end()
            if spans: # form feed
                driver.on_next_page()

    

class TxtDriver:
    """single text input"""
    def __init__(self, ctx, style=None):
        self.ctx = ctx
        self.line_nr = 0
        self.first_time = True
        self.canvas = None
        self.style = style
        self.style_to_color = {}

    def line_height(self):
        linespacing = 1.0 + self.ctx.opts.linespacing
        return self.ctx.font.height() * linespacing

    def on_line_end(self):
        if self.canvas:
            self.canvas.text_end()
        else:
            self.paint_zebra(self.ctx.y)
        self.line_nr += 1
        self.canvas = None
        self.ctx.y -= self.line_height()
        
    def on_text(self, text, token=None):
        if not self.canvas:
            self.paint_zebra(self.ctx.y)
            baseline = self.ctx.y - self.ctx.font.height() - self.ctx.font.bbox_ymin()
            self.canvas = self.ctx.doc.page().canvas()
            self.canvas.text_start(self.ctx.opts.margins.left(), baseline)
            if self.first_time:
                place_bookmark(self.ctx)
                self.first_time = False
        if token:
            try:
                color = self.style_to_color[token]
            except KeyError:
                color = self.style.style_for_token(token)['color']
                if color:
                    color = parse_color(color)
                else:
                    color = self.ctx.opts.font_color
                self.style_to_color[token] = color
            self.canvas.color("f", *color)
        self.canvas.text(text)
        
    def on_next_page(self):
        if self.canvas:
            self.on_line_end()
        self.ctx.paging.next_page()
        self.line_nr = 0
        
    def paint_zebra(self, y):
        zebra = self.ctx.opts.zebra
        if zebra:
            col = zebra[self.line_nr % len(zebra)]
            if col:
                canvas = self.ctx.doc.page().canvas()
                canvas.state_save()
                height = self.line_height()
                canvas.color("f", *col)
                canvas.rectangle(self.ctx.opts.margins.left(), y - height,
                                 self.ctx.opts.margins.canvas_width(), height)
                canvas.path_paint("f")
                canvas.state_restore()
        

# ----------------------------------------------------------------------
#                   document pagination
       
class Paging:
    def __init__(self, ctx):
        self.ctx = ctx
        self.page_nr = 0 # nr of physical pages
        self.page_start()

    def set_page_topleft_y(self):
        self.ctx.y = self.ctx.opts.page[1] - self.ctx.opts.margins.top()

    def page_start(self):
        self.ctx.doc.page_start(*self.ctx.opts.page)
        self.establish_state()
        self.set_page_topleft_y()
        self.is_page_open = True

    def page_end(self):
        self.ctx.doc.page_end()
        self.is_page_open = False
        self.page_nr += 1

    def next_page(self):
        self.page_end()
        self.page_start()

    def finalize(self):
        if self.is_page_open:
            self.page_end()

    def establish_state(self):
        opts = self.ctx.opts
        canvas = self.ctx.doc.page().canvas()
        canvas.text_font(self.ctx.font)
        canvas.text_character_spacing(opts.charspacing)
        canvas.color_space("fs", jagpdf.CS_DEVICE_RGB)
        canvas.color("f", *opts.font_color)
        if opts.page_color:
            canvas.color("fs", *opts.page_color)
            canvas.rectangle(0, 0, *opts.page)
            canvas.path_paint("fs")
        #self.draw_margin()
            
    def draw_margin(self):
        opts = self.ctx.opts
        canvas = self.ctx.doc.page().canvas()
        canvas.color("fs", *opts.font_color)
        canvas.rectangle(opts.margins.left(), opts.margins.bottom(),
                         opts.margins.canvas_width(), opts.margins.canvas_height())
        canvas.path_paint('s')

        
class NupPaging(Paging):
    def __init__(self, ctx):
        assert ctx.opts.nup
        self.nups = nup_matrices(ctx.opts.nup, *ctx.opts.page)
        self.logical_page_nr = 0
        Paging.__init__(self, ctx)

    def page_start(self):
        i = self.logical_page_nr % len(self.nups)
        if i == 0:
            Paging.page_start(self)
        else:
            self.ctx.doc.page().canvas().state_restore()
            self.set_page_topleft_y()
        canvas = self.ctx.doc.page().canvas()
        canvas.state_save()
        canvas.transform(*self.nups[i])

    def page_end(self):
        canvas = self.ctx.doc.page().canvas()
        canvas.state_restore()
        self.logical_page_nr += 1
        if 0 == (self.logical_page_nr % len(self.nups)):
            Paging.page_end(self)
        else:
            canvas.state_save()


def nup_matrices(power, w, h):
    import math
    dim = 2 ** (power / 2)
    c = 1.0 / math.sqrt(2 ** power)
    if power % 2:
        return [(0.0, c, -c, 0.0, i * h * c, j * w * c) \
                for i in range(dim, 0, -1) for j in range(2 * dim)]
    else:
        return [(c, 0.0, 0.0, c, j * w * c, i * h * c) \
                for i in range(dim) for j in range(dim)]

# ----------------------------------------------------------------------
#                        state management
#
def load_font(ctx):
    opts = ctx.opts
    if os.path.isfile(opts.font):
        name = 'file=' + opts.font
    else:
        name = 'standard; name=' + opts.font
    spec = "%s; size=%d; enc=utf-8" % (name, opts.fontsize)
    ctx.font = ctx.doc.font_load(spec)

def create_doc_profile(opts):
    profile = jagpdf.create_profile()
    viewer_prefs = []
    encrypted = False
    if opts.docname:
        profile.set('info.title', opts.docname)
        viewer_prefs.append('DisplayDocTitle')
    if viewer_prefs:
        profile.set('doc.viewer_preferences', ';'.join(viewer_prefs))
    if opts.initdest:
        profile.set('doc.initial_destination', opts.initdest)
    if opts.fullscreen:
        profile.set('doc.page_mode', 'FullScreen')
    if opts.pagelayout:
        profile.set('doc.page_layout', opts.pagelayout)
    if None != opts.ownerpwd:
        profile.set('stdsh.pwd_owner', opts.ownerpwd)
        encrypted = True
    if None != opts.userpwd:
        profile.set('stdsh.pwd_user', opts.userpwd)
        encrypted = True
    if opts.userpermissions:
        profile.set('stdsh.permissions', opts.userpermissions.replace(',', ';'))
        encrypted = True
    if encrypted:
        profile.set('doc.encryption', 'standard')
    #profile.set("doc.trace_level", "5")
    profile.set("doc.compressed", "0")
    return profile

def create_initial_context(opts):
    """Creates an initial document context from global options."""
    profile = create_doc_profile(opts)
    doc = jagpdf.create_stream(PDFStream(opts), profile)
    ctx = Bunch(doc=doc, img_cache={}, opts=opts)
    load_font(ctx)
    ctx.paging = opts.nup and NupPaging(ctx) or Paging(ctx)
    return ctx

def update_context(ctx):
    """Updates the document context from the current options."""
    load_font(ctx)



# ----------------------------------------------------------------------
#          command line option callbacks & related helpers
#

def parse_color(color):
    if color == '':
        return None
    try:
        return int(color[0:2], 16) / 255.0, \
               int(color[2:4], 16) / 255.0, \
               int(color[4:6], 16) / 255.0
    except ValueError:
        raise OptionValueError("invalid color specification %s" % color)

def hook_paper_format(option, opt, value, parser):
    formats = {'a4': [8.3 * 72, 11.7 * 72],
               'letter': [8.5 * 72, 11.0 * 72]}
    try:
        page = formats[value.lower()]
    except KeyError:
        m = re.compile('^([0-9.]+),([0-9.]+)$').match(value)
        if m:
            page = [float(m.group(1)), float(m.group(2))]
        else:
            raise OptionValueError("unrecognized page format: %s" % value)
    setattr(parser.values, option.dest, page)

def hook_color(option, opt, value, parser):
    setattr(parser.values, option.dest, parse_color(value))

def hook_color_list(option, opt, value, parser):
    colors = [parse_color(c) for c in value.split(',')]
    setattr(parser.values, option.dest, colors)
    
def hook_destination(option, opt, value, parser):
    try:
        dest = "mode=XYZ; zoom=%.2f" % float(value)
    except ValueError:
        optmap = { 'fith': 'FitH', 'fitv': 'FitV', 'fit': 'Fit'}
        if value in optmap:
            dest = "mode=" + optmap[value]
        else:
            raise OptionValueError('unrecognized destination: %s' % value)
    setattr(parser.values, option.dest, dest)


class Margins:
    def __init__(self, parser, margins):
        self.parser = parser
        self.margins = margins
        
    def top(self): return self.margins[0]
    def right(self): return self.margins[1]
    def bottom(self): return self.margins[2]
    def left(self): return self.margins[3]
    def width(self): return self.left() + self.right()
    def height(self): return self.top() + self.bottom()
    def canvas_width(self): return self.parser.values.page[0] - self.width()
    def canvas_height(self): return self.parser.values.page[1] - self.height()


def hook_margins(option, opt, value, parser):
    try:
        margins = [float(m) for m in value.split(',')]
        if len(margins) != 4:
            raise OptionValueError("unrecognized margins: %s" % value)
    except ValueError:
        raise OptionValueError("unrecognized margins: %s" % value)
    setattr(parser.values, option.dest, Margins(parser, margins))

optmap_layout = {'single': 'SinglePage',
                 'cont': 'OneColumn',
                 'cont-facing': 'TwoColumnLeft'}

optmap_perm = {'no_copy': 'no_copy',
               'no_print' : 'no_print',
               'no_modify' : 'no_modify'}

def hook_string_remap(option, opt, values, parser, optmap, is_list=False):
    result = []
    for value in values.split(','):
        if value in optmap:
            result.append(optmap[value])
        else:
            raise OptionValueError("unrecognized value: %s" % values)
    if not is_list and len(result) > 1:
        raise OptionValueError("unrecognized value: %s" % values)
    setattr(parser.values, option.dest, ";".join(result))

class PageBreak: pass
def hook_separator(option, opt, value, parser):
    if value == 'break':
        result = PageBreak
    else:
        try:
            result = float(value)
        except ValueError:
            raise OptionValueError("unrecognized value %s" % value)
    setattr(parser.values, option.dest, result)

def create_opt_parser():
    usage = """usage: %prog [doc-level-options] commands"""
    desc = __doc__
    # A command comprises of input file options and an input file ('-' stands
    # for if token[ stdin). lists are comma separated, units are 1/72 inch,
    # color format is rrggbb
    version="%%prog %s (JagPDF %06x)" % (__version__, jagpdf.version())
    parser = OptionParser(usage=usage,
                          version=version,
                          description=desc)
    parser.set_defaults(page=[8.3 * 72, 11.7 * 72], #a4
                        fontsize=10,
                        encoding='utf-8',
                        charspacing=0.0,
                        linespacing=0.0,
                        font_color=(0, 0, 0),
                        page_color=None,
                        docname=None,
                        initdest=None,
                        fullscreen=False,
                        pagelayout=None,
                        font="Courier",
                        ownerpwd=None,
                        userpwd=None,
                        userpermissions=None,
                        margins=Margins(parser, (72, 68, 72, 68)),
                        zebra=None,
                        nup=None,
                        is_text=True,
                        separator=36.0,  # TBD: false does not work
                        image_align='left',
                        image_fit_wider=True,
                        image_dpi=None,
                        outfile='-',
                        bookmark=None,
                        highlight=False,
                        tabsize=4
                        )
    group = OptionGroup(parser, "Common input options")
    group.add_option("--margins",
                     action='callback', type='string', dest="margins",
                     callback=hook_margins,
                     help="set page margins, MARGINS is a top,right,bottom,left list",
                     metavar="MARGINS")
    group.add_option("-i", "--image",
                     action='store_false', dest='is_text',
                     help="if unsure, insert the input file as an image")
    group.add_option("-t", "--text",
                     action='store_true', dest='is_text',
                     help="if unsure, insert the input file as plain text [default]")
    group.add_option("--page",
                     action='callback', type='string', dest='page',
                     callback=hook_paper_format,
                     help="set page size to PAGE, can be A4, Letter, or custom width,height [A4]")
    group.add_option("--page-color",
                     action='callback', type='string', dest="page_color",
                     callback=hook_color,
                     help="set page background COLOR [white]", metavar="COLOR")
    group.add_option("--bookmark",
                     action='store', type='string', dest='bookmark',
                     help="create a bookmark labelled with STRING", metavar='STRING')
    group.add_option("--separator",
                     action='callback', type='string', dest='separator',
                     callback=hook_separator,
                     help="add vertical SPACE after the input; setting SPACE to 'break' inserts a page break",
                     metavar="SPACE")
    groupt = OptionGroup(parser, "Text input options")
    groupt.add_option("--font",
                     action='store', type='string', dest='font',
                     help="use FONT, can be either a full path or a core font name [Courier]")
    groupt.add_option("--font-size",
                      action='store', type='int', dest="fontsize",
                      help="set font size to SIZE [%default]", metavar="SIZE")
    groupt.add_option("--encoding",
                     action='store', type='string', dest="encoding",
                     help="ENC is input text encoding [%default]",
                     metavar="ENC")
    groupt.add_option("--char-spacing",
                     action='store', type='float', dest="charspacing",
                     help="set character spacing to FACTOR [0.0]",
                     metavar="FACTOR")
    groupt.add_option("--line-spacing",
                     action='store', type='float', dest="linespacing",
                     help="set line spacing to FACTOR [0.0]",
                     metavar="FACTOR")
    groupt.add_option("--text-color",
                     action='callback', type='string', dest="font_color",
                     callback=hook_color,
                     help="show text in COLOR [black]",
                     metavar="COLOR")
    groupt.add_option("--zebra",
                     action='callback', type='string', dest="zebra",
                     callback=hook_color_list,
                     help="paint a zebra with the LIST of colors",
                     metavar="LIST")
    groupt.add_option("--highlight",
                      action="store_true", dest="highlight",
                      help="highlights the input (needs Pygments)")
    groupt.add_option("--no-highlight",
                      action="store_false", dest="highlight",
                      help="do not highlight the input (default)")
    groupi = OptionGroup(parser, "Image input options")
    groupi.add_option("--image-align", type="string", dest="image_align",
                      help="image alignment, IMAGE can be on of: left, center, right [%default]",
                      metavar="ALIGN")
    groupi.add_option("--image-fit-wide", action="store_true",
                      dest="image_fit_wider",
                      help="resize image to fit page if it is wider [default]")
    groupi.add_option("--no-image-fit-wide", action="store_false",
                      dest="image_fit_wider",
                      help="turn off --image-fit-wide")
    groupi.add_option("--image-dpi", type="float", dest="image_dpi",
                      help="use DPI, ignore image intrinsic dpi", metavar="DPI")
    parser.add_option_group(group)
    parser.add_option_group(groupt)
    parser.add_option_group(groupi)
    #
    group = OptionGroup(parser, "Document level options")
    group.add_option("-o", "--output-file",
                      action='store', type='string', dest="outfile",
                      help="output is sent to FILE, defaults to stdout",
                     metavar="FILE")
    group.add_option("--initial-dest",
                     action='callback', type='string', dest="initdest",
                     callback=hook_destination,
                     help="set initial destination, DST can be one of: fitv, fith, fit, or a number specifying the zoom factor",
                     metavar="DST")
    group.add_option("--full-screen",
                     action='store_true', dest="fullscreen",
                     help="document will be displayed in full-screen mode")
    group.add_option("--page-layout",
                     action='callback', type='string', dest='pagelayout',
                     callback=hook_string_remap, callback_args=(optmap_layout,),
                     help="set initial page layout, MODE can be one of: single, cont, and cont-facing", metavar="MODE")
    group.add_option("--owner-pwd",
                     action='store', type='string', dest='ownerpwd',
                     help="set owner password to PWD", metavar="PWD")
    group.add_option("--user-pwd",
                     action='store', type='string', dest='userpwd',
                     help="set user password to PWD", metavar="PWD")
    group.add_option("--user-perm",
                     action='callback', type='string', dest='userpermissions',
                     callback=hook_string_remap,
                     callback_args=(optmap_perm, True),
                     help="set user permissions, LIST, can be a combination of: no_print, no_modify, and no_copy",
                     metavar="LIST")
    group.add_option("--n-up",
                     action='store', type='int', dest='nup',
                     help="2^N-up page imposition, default N is 0", metavar="N")
    group.add_option("--doc-name",
                     action='store', type='string', dest="docname",
                     help="set document name to STRING", metavar="STRING")
    parser.add_option_group(group)
    
    return parser

def expand_args(args):
    """Expands arguments with those defined in an external @file"""
    result = []
    for arg in args:
        if arg.startswith('@'):
            from_file = " ".join(open(arg[1:]).readlines())
            result += from_file.split()
        else:
            result.append(arg)
    return result

# ---------------------------------------------------------------------------
#                           main loop

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    argv = expand_args(argv) # TBD: quoting
    try:
        parser = create_opt_parser()
        parser.disable_interspersed_args()
        ctx, opts = None, None
        while 1:
            opts, argv = parser.parse_args(argv, opts)
            if not len(argv):
                raise Error("no input, run with --help")
            if not ctx:
                ctx = create_initial_context(opts)
            update_context(ctx)
            process_input(ctx, argv.pop(0))
            if not argv:
                ctx.paging.finalize()
                ctx.doc.finalize()
                break
            else:
                insert_input_separator(ctx)
    except Error, err:
        print >>sys.stderr, err.msg
        return 1
    except jagpdf.Exception, err:
        print >>sys.stderr, "JagPDF error:", err
        return 1
    except (URLError, HTTPError), err:
        print >>sys.stderr, 'Cannot read from remote stream:', err.reason[1]

re_is_img = re.compile('^.*\.(?:png|jpg|bmp)$', re.I)
re_is_url = re.compile('^(?:http|ftp)://\S+$', re.I)
def get_stream(ctx, input_name):
    if input_name == '-':
        return sys.stdin, ctx.opts.is_text
    else:
        if re_is_url.match(input_name):
            stream = urlopen(input_name)
        else:
            stream = open(input_name, 'rb')
        return stream, not re_is_img.match(input_name)

re_is_img = re.compile('^.*\.(?:png|jpg|bmp)$', re.I)
def process_input(ctx, input_name):
    """Processes single input."""
    stream, is_text = get_stream(ctx, input_name)
    ctx.input_name = input_name
    if is_text:
        show_text(ctx, stream)
    else:
        paint_image(ctx, stream)
    stream.close()

if __name__ == '__main__':
    sys.exit(main())

# TBD:
# ----
#  - nup
#  - image cache should be keyed by dpi as well
#  - underscore overpaint by a zebra stripe
#  - pygments new_line handling
#  - form-feed - test in both modes (highlight, normal)
#  - formatting of help options in parser.add_option
#  - questionable, if utf-8 is a good default encoding
#  - detect encoding -*- encoding: -*- in N first lines
#  - CppLexer vs. CLexer

# Enhancements
# ------------
# - load profile from a separate file
# - automatic horizontal margins according chars per line
# - input prologue
# - headers/footers
    
    
