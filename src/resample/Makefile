
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s

all: resample resample.nodiv

resample: resample.c

resample.nodiv: resample.nodiv.c Makefile
	egcc -O6 -Wall -g -o resample.nodiv resample.nodiv.c

install: resample
	install resample /usr/local/bin

clean:
	rm -f resample{,.nodiv}{,.s} core

