#
# The html documentation is produced from README.rst There is a special sed
# pre-processing which enables Pygments (see comments in README.rst)
# 
doc/index.htm: README.rst
	< README.rst \
		sed 's/.. sourcecode/.. sourcecode::/g' | \
		sed 's/^::$$//g' | \
		rst2html --cloak-email-addresses \
				 --link-stylesheet \
				 --stylesheet-path=doc/style.css \
				 - doc/index.htm
	sed -i "s/[$$]Date:[$$]/`date -R`/g" doc/index.htm

#
# Manual is built using rst2man from README.rst; sed skips a section belonging
# to the html output (up to '.. manpage-start' placeholder) and the manual
# prologue is added instead.
#
# To format examples correctly, trailing backslash must be replaced by '\\ '
# 
# good rst2man info:
#  http://jimmyg.org/blog/2009/generating-man-pages-from-restructuredtext.html
#
#
# Targets:
#  man      .. builds the manpage
#  mantest  .. builds the manpage and runs it with man
# 
doc/jag-tipdf.1.gz: README.rst man.rst
	env PYTHONPATH=/home/jarda/src/manpage-writer/ \
		sed -n '/.. manpage-start/,$$p' README.rst | \
		sed 's/\\$$/\\\\ /g' | \
		cat man.rst - | \
	    /usr/bin/python \
	    ~/src/manpage-writer/tools/rst2man.py --traceback \
	    > jag-tipdf.1
	gzip jag-tipdf.1
	mv jag-tipdf.1.gz doc/

man: doc/jag-tipdf.1.gz
.PHONY: mantest

mantest: man
	mkdir -p /tmp/man1
	cp doc/jag-tipdf.1.gz /tmp/man1
	man -M /tmp jag-tipdf


#
# all: builds the html documentation and a manpage
#
all: doc/index.htm doc/jag-tipdf.1.gz	


#
# relase: prepares packages for distribution
#
.PHONY: release
release:
	make clean
	make all
	python -u setup.py sdist --format=gztar,zip,bztar



.PHONY: clean
clean:
	rm -f doc/index.htm	doc/jag-tipdf.1.gz output/*

.PHONY: help

help:
	@echo "all     .. html and manpage"
	@echo "release .. creates distribution packages"
	@echo "man     .. builds the manpage"
	@echo "mantest .. builds the manpage and runs it with man"
	@echo "clean   .. deletes all targets"
