
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

#include "debug.h"
#include "polllib.h"
#include "buffer.h"
#include "input.h"
#include "output_oss.h"
#include "signals.h"
#include "socket.h"

void usage(FILE *f)
{
	fprintf(f, "\
Usage:   cdrplay [-dvMR] [-b bufsize_kb] [-k n] [-D file] [command args...]\n\
\n\
         Cdrplay plays the stdout of 'command' (or stdin if command is omitted)\n\
         to /dev/dsp. 'Command' should deliver 44.1kHz 16-bit signed\n\
         little-endian audio data.

         -b bufsize_kb   : set buffer size\n\
         -d              : enable debugging output\n\
         -k n            : skip first n bytes (works only on seekable files)\n\
         -v              : verbose status output\n\
         -w              : wait until audio device isn't busy\n\
         -D file         : send output to file instead of /dev/dsp\n\
         -M              : disable use of mlockall(2)\n\
         -R              : disable use of real-time scheduling\n\
\n\
example: cdrplay -v -b 1000 splay -v -d - mp3files...\n\
         (works only with 44.1kHz mp3s)\n\

example: cdrplay -v -b 1000 mpg123 -r 44100 -s mp3files...\n\
         (use mpg123-0.59o or higher, should work with all mp3s)\n\
\n\
Report bugs to eric@scintilla.utwente.nl.\n");
}

int playing = 1;

int main(int argc, char **argv)
{
	int c, port = 2222;
	char *dev = "/dev/dsp";
	
	while((c = getopt(argc, argv, "+b:dhp:D:")) != EOF) {
		switch(c) {
			case 'b':
				buffer_size = atoi(optarg) * 1024;
				if(buffer_size == < 16) {
					fprintf(stderr, "ERROR: buffer_size < 16\n");
					exit(1);
				}
				break;
			case 'd':
				debug++;
				break;
			case 'h':
				usage(stdout);
				exit(0);
			case 'p':
				port = atoi(optarg);
				break;
			case 'D':
				dev = optarg;
				break;
			default:
				usage(stderr);
				exit(1);
		}
	}

	/* lock memory */
	if(mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
		perror("warning: mlockall");
	}

	buffer_init();
	input_start();
	output_oss_init("/dev/dsp");
	signals_init();
	socket_init(port);

	output_oss_start();
	mainloop();

	return 0;
}
