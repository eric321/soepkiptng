
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
	fprintf(f,
		"\n"
		"Usage:  soepkiptng_play [-d] [-b bufsize_kb] [-p port] [-D file]\n"
		"\n"
		"        Soepkiptng_play reads 44.1kHz 16-bit signed little-endian audio data\n"
		"        from stdin and plays it on /dev/dsp.\n"
		"\n"
		"        -b bufsize_kb   : set buffer size\n"
		"        -d              : enable debugging output\n"
		"        -p port         : tcp port to listen on\n"
		"        -D file         : send output to file instead of /dev/dsp\n"
		"\n"
		"Report bugs to eric@lammerts.org.\n");
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
				if(buffer_size < 16) {
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
	output_oss_init(dev);
	signals_init();
	socket_init(port);

	output_oss_start();
	mainloop();

	return 0;
}
