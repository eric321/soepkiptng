
CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
DSTDIR=/usr/local/bin

default: lpac2raw

lpac2raw: lpac2raw.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LIBS)

install: lpac2raw
	install lpac2raw $(DSTDIR)

clean:
	-rm -rf lpac2raw *.o
