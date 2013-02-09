
#include <getopt.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <sys/resource.h>

#include "debug.h"
#include "polllib.h"
#include "buffer.h"
#include "input.h"
#include "output.h"
#include "signals.h"
#include "socket.h"

void usage(int err)
{
	fprintf(err? stderr : stdout,
		"\n"
		"Usage:  soepkiptng_play [-d] [-b bufsize_kb] [-p port] [-D file]\n"
		"\n"
		"        Soepkiptng_play reads 44.1kHz 16-bit signed little-endian audio data\n"
		"        from stdin and plays it on /dev/dsp.\n"
		"\n"
		"        -b bufsize_kb   : set buffer size\n"
		"        -B [16|32]      : set bits per sample (default 16)\n"
		"        -d              : enable debugging output\n"
		"        -p port         : tcp port to listen on\n"
		"        -s freq         : set samplefreq (default 44100)\n"
		"        -D file         : send output to file instead of /dev/dsp\n"
		"\n"
		"Report bugs to eric@lammerts.org.\n");
	exit(err);
}

int playing = 1;

int main(int argc, char **argv)
{
	int c, port = 2222, samplefreq = SAMPLEFREQ, chans = 2;
	int fmt_bits = 16;
	char *dev = "/dev/dsp";
	
	while((c = getopt(argc, argv, "+b:B:c:dhp:s:D:")) != EOF) {
		switch(c) {
			case 'b':
				buffer_size = atoi(optarg) * 1024;
				if(buffer_size < 16) {
					fprintf(stderr, "ERROR: buffer_size < 16\n");
					exit(1);
				}
				break;
			case 'c':
				chans = atoi(optarg);
				break;
			case 'd':
				debug++;
				break;
			case 'B':
				fmt_bits = atoi(optarg);
				if(fmt_bits != 16 && fmt_bits != 32) usage(1);
				break;
			case 'h':
				usage(0);
			case 'p':
				port = atoi(optarg);
				break;
			case 's':
				samplefreq = atoi(optarg);
				break;
			case 'D':
				dev = optarg;
				break;
			default:
				usage(1);
		}
	}

	buffer_init();
	input_start();
	output_init(dev, samplefreq, fmt_bits, chans);
	signals_init();
	socket_init(port);

	/* lock memory (limits for non-root can be raised in /etc/security/limits.conf) */
	if(mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
		struct rlimit rl;
		if(getrlimit(RLIMIT_MEMLOCK, &rl) == 0) {
			rl.rlim_cur = rl.rlim_max;
			if(setrlimit(RLIMIT_MEMLOCK, &rl) == -1) {
				perror("setrlimit RLIMIT_MEMLOCK");
			}
		}
		if(mlockall(MCL_CURRENT | MCL_FUTURE) == -1) {
			perror("warning: mlockall");
		}
	}

	/* realtime priority (limits for non-root can be raised in /etc/security/limits.conf) */
	struct sched_param sp;
	sp.sched_priority = 1;
	if(sched_setscheduler(getpid(), SCHED_FIFO, &sp) < 0)
		perror("sched_setscheduler");

	output_start();
	mainloop();

	return 0;
}
