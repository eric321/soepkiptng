
CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
LIBS=/usr/lib/vorbisfile.a -lm -lvorbis

default: ogg2raw

ogg2raw: ogg2raw.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LIBS)

install: ogg2raw
	install ogg2raw /usr/local/bin

clean:
	-rm -rf ogg2raw *.o
