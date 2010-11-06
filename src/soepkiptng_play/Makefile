
# $Id$

CC=gcc
CFLAGS=-O2 -Wall
LDFLAGS=-s
DSTDIR=../../bin

SRC=buffer.c debug.c input.c output.c output_alsa.c output_oss.c polllib.c \
	signals.c socket.c soepkiptng_play.c
OBJ=$(SRC:%.c=obj/%.o)

obj/%.o: %.c *.h Makefile
	@mkdir -p obj
	$(CC) -c $(CFLAGS) -o $@ $<

all: soepkiptng_play

soepkiptng_play: $(OBJ) *.h Makefile
	$(CC) $(LDFLAGS) -o $@ $(OBJ) -lasound

install: soepkiptng_play
	install -o root -m 4755 soepkiptng_play $(DSTDIR)

clean:
	rm -f *.o soepkiptng_play
