
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
DSTDIR=/usr/local/bin

SRC=buffer.c debug.c input.c output_oss.c polllib.c \
	realtime.c signals.c soepkiptng_play.c
OBJ=$(SRC:%.c=obj/%.o)

obj/%.o: %.c *.h Makefile
	@mkdir -p obj
	$(CC) -c $(CFLAGS) -o $@ $<

all: soepkiptng_play

soepkiptng_play: $(OBJ) *.h Makefile
	$(CC) $(LDFLAGS) -o $@ $(OBJ)

install: soepkiptng_play
	install -o root -m 4755 soepkiptng_play $(DSTDIR)

clean:
	rm -f soepkiptng_play
