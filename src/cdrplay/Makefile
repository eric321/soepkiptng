
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s

all: cdrplay simpleplay

cdrplay: cdrplay.c

simpleplay: simpleplay.c

install: cdrplay simpleplay
	install -o root -m 4755 cdrplay /usr/local/bin
	install simpleplay /usr/local/bin

clean:
	rm -f cdrplay simpleplay


