
/* cdrplay
 * plays 16-bit 44.1 kHz stereo little-endian raw sound files to /dev/dsp
 * uses mlockall(2) and real-time scheduling to achieve uninterrupted playing
 *
 * copyright (c) 1998, Eric Lammerts <eric@scintilla.utwente.nl>
 * may be copied under the terms of the GNU General Public License
 */

static char rcsid[] = "$Id$";

#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <linux/soundcard.h>

#define BLKSIZE 4096

int fd1, fd2;
int pid1 = 0;
int pos = 0;
int len = 0;
int readeof = 0;
int maywrite = 0;
int do_realtime = 1;
int debug = 0;
int stop_on_buffer_empty = 0;

void perr(char *s)
{
	perror(s);
	exit(1);
}

int ischardev(int fd)
{
	struct stat st;
	
	if(fstat(fd, &st) == -1) return 0;
	return S_ISCHR(st.st_mode);
}

void realtime(int on)
{
	struct sched_param sp;

	if(debug) fprintf(stderr,"realtime(%s)\n", on? "on":"off");
	if(on) {
		sp.sched_priority = 3;
		if(sched_setscheduler(getpid(), SCHED_FIFO, &sp) < 0)
			perror("sched_setscheduler");
	
		if(pid1) {
			sp.sched_priority = 2;
			if(sched_setscheduler(pid1, SCHED_FIFO, &sp) < 0)
				perror("sched_setscheduler");
		}
	} else {
		sp.sched_priority = 0;
		if(sched_setscheduler(getpid(), SCHED_OTHER, &sp) < 0)
			perror("sched_setscheduler");

		if(pid1) {
			sp.sched_priority = 0;
			if(sched_setscheduler(pid1, SCHED_OTHER, &sp) < 0)
				perror("sched_setscheduler");
		}
	}
}

void sighandler(int s)
{
	if(pid1) kill(pid1, s);
	fprintf(stderr,"\nSignal %d received, exiting.\n",s);
	exit(1);
}

void sigusr1(int s)
{
	short buf[2];

	signal(s, sigusr1);
/*	ioctl(fd2, SNDCTL_DSP_RESET, 0); */
	buf[0] = buf[1] = 0;
	write(fd2, buf, sizeof(buf));
	ioctl(fd2, SNDCTL_DSP_SYNC, 0);  /* SNDCTL_DSP_POST doesn't seem to work ... */
	pos = len = maywrite = 0;
	readeof = 0;

	if(do_realtime) realtime(0);
}

void sigusr2(int s)
{
	stop_on_buffer_empty = 1;
	signal(s, sigusr2);
}

/* flags should be O_RDONLY or O_WRONLY. If pid != NULL, the pid of the
   child process will be put there */

int pipeopen(char **cmd, int *pid)
{
	int fd[2];
	int p;

	if(pipe(fd) < 0) perr("pipe");
	switch((p = fork())) {
		case -1:	perr("fork");
		case 0:		dup2(fd[1],1);
					close(fd[0]);
					close(fd[1]);
					setuid(getuid()); 	/* surrender root privileges */
					setpgrp();			/* give program its own program group so signals from the shell don't reach it */
					execvp(*cmd, cmd);
					perr("execvp");
		default:	if(pid) *pid = p;
					close(fd[1]);
					return fd[0];
	}
}

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

int main(int argc, char **argv)
{
	char *buf, c;
	int bufsize, l, minlen = 0, status, i, r, w, iseek = 0, retval;
	int write_total = 0;
	int maxfd;
	fd_set rfds, wfds;
	int do_mlockall = 1, verbose = 0, busywait = 0;
	char *snddev = "/dev/dsp";
	int s_minflt = 0, s_majflt = 0, s_nswap = 0, s_nivcsw = 0;
	char waitstr[] = "|/-\\";

	bufsize = 500 * 1024;
	while((c = getopt(argc, argv, "+b:dhk:vwD:RM")) != EOF) {
		switch(c) {
			case 'b':
				bufsize = atoi(optarg) * 1024;
				if(bufsize < 16384) {
					fprintf(stderr,"bufsize too small (<16kb)\n");
					exit(1);
				}
				break;
			case 'd':
				debug++;
				break;
			case 'h':
				usage(stdout);
				exit(0);
			case 'k':
				iseek = atoi(optarg);
				break;
			case 'v':
				verbose++;
				break;
			case 'w':
				busywait = 1;
				break;
			case 'D':
				snddev = optarg;
				break;
			case 'R':
				do_realtime = 0;
				break;
			case 'M':
				do_mlockall = 0;
				break;
			default:
				usage(stderr);
				exit(1);
		}
	}
	if(optind == argc)
		fd1 = 0;
	else
		fd1 = pipeopen(argv + optind, &pid1);
	if(iseek) lseek(fd1, iseek, SEEK_SET);

	if(strcmp(snddev,"-") == 0) fd2 = 1;
	else for(i = 0;;) {
		fd2 = open(snddev, O_WRONLY | O_CREAT | O_TRUNC, 0666);
		if(!busywait || fd2 >= 0 || errno != EBUSY) break;
		if(verbose) {
			fprintf(stderr,"%c\b", waitstr[i++ % 4]);
			fflush(stderr);
		}
		usleep(200000);
	}
	if(fd2 < 0) { perror(snddev); exit(1); }

	retval = ioctl(fd2, SNDCTL_DSP_SYNC, 0);
	i = 44100;
	if(retval != -1) retval = ioctl(fd2, SNDCTL_DSP_SPEED, &i);
	i = AFMT_S16_LE;
	if(retval != -1) retval = ioctl(fd2, SNDCTL_DSP_SETFMT, &i);
	i = 1;
	if(retval != -1) retval = ioctl(fd2, SNDCTL_DSP_STEREO, &i);

	if(retval == -1 && ischardev(fd2)) fprintf(stderr, "warning: sound ioctls failed\n");
	
	if((buf = malloc(bufsize)) == NULL) perr("malloc");
	if(do_mlockall && mlockall(MCL_CURRENT | MCL_FUTURE) == -1) perror("mlockall");

	maxfd = fd1 > fd2? fd1 : fd2;
	
	signal(SIGTERM, sighandler);
	signal(SIGINT, sighandler);
	signal(SIGUSR1, sigusr1);
	signal(SIGUSR2, sigusr2);
	signal(SIGPIPE, SIG_IGN);
	
	for(;;) {
/*		if(debug)
			fprintf(stderr,"Bufsize = %8d/%8d\n", len, bufsize); */

		if(verbose) {
			unsigned t;
			int perc;
			static unsigned displayed_t = -1;
			static int displayed_perc = -1;
			
			t = write_total / 176400;
			perc = 100 * len / bufsize;
			if(perc > 90) perc = -1;
			
			if(t != displayed_t || perc != displayed_perc) {
				if(maywrite) {
					fprintf(stderr," [%02u:%02u", t / 60, t % 60);
					displayed_t = t;
					if(verbose > 1) {
						struct stat st;
						unsigned t;
	
						fstat(fd1, &st);
						if(st.st_size) {
							t = st.st_size / 176400;
							fprintf(stderr," / %02u:%02u", t / 60, t % 60);
						}
					}
					fprintf(stderr,"]");
				}
				if(perc != -1) fprintf(stderr," fill %d%%", perc);
				if(readeof) fprintf(stderr," EOF");
				fprintf(stderr,"            \r");
				fflush(stderr);
				displayed_perc = perc;
			}
		}

		if(stop_on_buffer_empty && len == 0) break;
		if(readeof && len == 0) break;

		if((readeof || len == bufsize) && !maywrite) {  /* off we go! */
			if(do_realtime) realtime(1);

			/* don't let verbose/debug output block the audio output */
			fcntl(1, F_SETFL, O_NONBLOCK);

			maywrite = 1;
			minlen = len;

			if(debug) {			
				struct rusage ru;
			
				getrusage(RUSAGE_SELF, &ru);
				s_minflt = ru.ru_minflt;
				s_majflt = ru.ru_majflt;
				s_nswap = ru.ru_nswap;
				s_nivcsw = ru.ru_nivcsw;
			}
		}

		FD_ZERO(&rfds);
		if(!readeof && len < bufsize) FD_SET(fd1, &rfds);
		FD_ZERO(&wfds);
		if(maywrite && len > 0) FD_SET(fd2, &wfds);
		select(maxfd + 1, &rfds, &wfds, NULL, NULL);

		/* try writing... */
		if(FD_ISSET(fd2, &wfds)) {
			l = len;
			if(l > BLKSIZE) l = BLKSIZE;
			if(l + pos > bufsize) l = bufsize - pos;

			if((w = write(fd2, buf + pos, l)) == -1) {
				if(errno == EINTR) continue;
				perror("write");
				break;
			}
			len -= w;
			if(debug > 1) {
				fprintf(stderr, "wrote %8d bytes at %8d. len now %8d\n",
					w, pos, len);
			}
			pos = (pos + w) % bufsize;
			write_total += w;

			/* flush data in soundcard driver if we are out of data */
			if(len == 0) ioctl(fd2, SNDCTL_DSP_POST, 0);

			/* if readeof == 1, we don't select() on fd1. Therefore, select
			   always waits until fd2 is ready. If we'd continue here we'd
			   never try reading */
			if(!readeof) continue;
		}

		/* try reading... */
		if(readeof || FD_ISSET(fd1, &rfds)) {
			int dst;

			dst = (pos + len) % bufsize;
			l = bufsize - len;
			if(l > BLKSIZE) l = BLKSIZE;
			if(l > bufsize - dst) l = bufsize - dst;
			
			if((r = read(fd1, buf + dst, l)) == -1) {
				if(errno == EINTR) continue;
				perror("read");
				break;
			}
			len += r;
			if(debug > 1) {
				fprintf(stderr, "read  %8d bytes at %8d. len now %8d\n",
					r, dst, len);
			}
			readeof = (r == 0); /* end-of-file */
			if(debug && readeof) fprintf(stderr,"readeof ");
		}
	}
	if(verbose) fprintf(stderr,"\n");
	close(fd1);
	buf[0] = buf[1] = buf[2] = buf[3] = 0;
	write(fd2, buf, 4);
	close(fd2);

	if(debug) {			
		struct rusage ru;
			
		getrusage(RUSAGE_SELF, &ru);
		fprintf(stderr,"minflt=%ld, majflt=%ld, nswap=%ld, nivcsw=%ld\n",
			ru.ru_minflt - s_minflt,
			ru.ru_majflt - s_majflt,
			ru.ru_nswap - s_nswap,
			ru.ru_nivcsw - s_nivcsw);
	}
	
	if(pid1) {
		waitpid(pid1, &status, 0);
		if(WIFSIGNALED(status)) {
			fprintf(stderr,"command killed by signal %d.\n", WTERMSIG(status));
			exit(1);
		}
		if(WIFEXITED(status) && WEXITSTATUS(status) != 0) {
			fprintf(stderr,"command exited with error code %d.\n", WEXITSTATUS(status));
			exit(1);
		}
	}
	return 0;
}
