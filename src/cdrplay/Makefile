
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s

all: cdrplay

cdrplay: cdrplay.c

install: cdrplay
	install -o root -m 4755 cdrplay /usr/local/bin

clean:
	rm -f cdrplay
