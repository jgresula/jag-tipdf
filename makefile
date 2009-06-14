doc/index.htm: README.rst
	rst2html --cloak-email-addresses \
	         README.rst doc/index.htm
	sed -i "s/[$$]Date:[$$]/`date -R`/g" doc/index.htm

#--link-stylesheet \
#--stylesheet-path=doc/voidspace.css \

# http://jimmyg.org/blog/2009/generating-man-pages-from-restructuredtext.html
doc/jag-tipdf.1.gz: README.rst	
	env PYTHONPATH=/home/jarda/src/manpage-writer/ \
	    /usr/bin/python \
	    ~/src/manpage-writer/tools/rst2man.py \
	    README.rst --traceback > jag-tipdf.1
	gzip jag-tipdf.1
	mv jag-tipdf.1.gz doc/

all: doc/index.htm doc/jag-tipdf.1.gz	

.PHONY: release
release:
	make clean
	make all
	python -u setup.py sdist --format=gztar,zip,bztar

.PHONY: clean
clean:
	rm -f doc/index.htm	doc/jag-tipdf.1.gz
