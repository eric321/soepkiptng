
CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s

default: lpac2raw

lpac2raw: lpac2raw.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LIBS)

install: lpac2raw
	install lpac2raw /usr/local/bin

clean:
	-rm -rf lpac2raw *.o
