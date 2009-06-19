#
# The html documentation is combined from README.rst and MANUAL.rst. There is a
# special sed pre-processing which cuts out the man header needed by rst2man
# 
doc/index.htm: README.rst MANUAL.rst
	cat README.rst MANUAL.rst | \
		sed '/.. manpage-start/,/.. manpage-header-end/d' | \
		rst2html --cloak-email-addresses \
				 --link-stylesheet \
				 --stylesheet-path=doc/style.css \
				 - doc/index.htm
	sed -i "s/[$$]Date:[$$]/`date -R`/g" doc/index.htm


#
# Manual is built using rst2man from MANUAL.rst, sed skips a section belonging
# to the html output.
#
# good rst2man info:
#  http://jimmyg.org/blog/2009/generating-man-pages-from-restructuredtext.html
#
# Targets:
#  man      .. builds the manpage
#  mantest  .. builds the manpage and runs it with man
# 
doc/jag-tipdf.1.gz: MANUAL.rst	
	env PYTHONPATH=/home/jarda/src/manpage-writer/ \
		sed -n '/.. manpage-start/,$$p' MANUAL.rst | \
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
#
#
all: doc/index.htm doc/jag-tipdf.1.gz	

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
