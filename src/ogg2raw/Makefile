
CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
LIBS=-lm -lvorbis -lvorbisfile
DSTDIR=/usr/local/bin

default: ogg2raw

ogg2raw: ogg2raw.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LIBS)

install: ogg2raw
	install ogg2raw $(DSTDIR)

clean:
	-rm -rf ogg2raw *.o
