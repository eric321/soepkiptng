
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
DSTDIR=/usr/local/bin

all: cdrplay

cdrplay: cdrplay.c

install: cdrplay
	install -o root -m 4755 cdrplay $(DSTDIR)

clean:
	rm -f cdrplay
