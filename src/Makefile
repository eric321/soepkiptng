
DSTDIR:=$(shell pwd)/../bin
PROGRAMS=cdrplay lpac2raw ogg2raw resample

default:
	for i in $(PROGRAMS); do make -C $$i; done
	@echo
	@echo all programs built successfully.

install:
	install -d $(DSTDIR)
	for i in $(PROGRAMS); do make DSTDIR=$(DSTDIR)/ -C $$i install; done

clean:
	for i in $(PROGRAMS); do make -C $$i clean; done

