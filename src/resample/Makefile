
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
DSTDIR=/usr/local/bin

all: resample

resample: resample.c

resample.nodiv: resample.nodiv.c Makefile
	egcc -O6 -Wall -g -o resample.nodiv resample.nodiv.c

install: resample
	install resample $(DSTDIR)

clean:
	rm -f resample{,.nodiv}{,.s} core

