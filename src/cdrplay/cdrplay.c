
/* cdrplay
 * plays 16-bit 44.1 kHz stereo little-endian raw sound files to /dev/dsp
 * uses mlockall(2) and real-time scheduling to achieve uninterrupted playing
 *
 * copyright (c) 1998, Eric Lammerts <eric@scintilla.utwente.nl>
 */

static char rcsid[] = "$Id$";

#include <fcntl.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/ioctl.h>
#include <linux/soundcard.h>

#define BLKSIZE 4096

int fd1, fd2;
int pid1 = 0;
int pos = 0;
int len = 0;
int mayread = 1;
int maywrite = 0;
int do_realtime = 1;

void perr(char *s)
{
	perror(s);
	exit(1);
}

void sighandler(int s)
{
	if(pid1) kill(pid1, s);
	if(s == SIGINT) {
		short buf[2];

		signal(SIGINT, sighandler);
		ioctl(fd2, SNDCTL_DSP_SYNC, 0);
		buf[0] = buf[1] = 0;
		write(fd2, buf, sizeof(buf));
		pos = len = maywrite = 0;
		mayread = 1;

		if(do_realtime) {
			struct sched_param sp;

			sp.sched_priority = 0;
			if(sched_setscheduler(getpid(), SCHED_OTHER, &sp) < 0)
				perror("sched_setscheduler");

			if(pid1) {
				sp.sched_priority = 0;
				if(sched_setscheduler(pid1, SCHED_OTHER, &sp) < 0)
					perror("sched_setscheduler");
			}
		}

		return;
	}
	fprintf(stderr,"Signal %d received, exiting.\n",s);
	exit(1);
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
Usage:   cdrplay [-dMR] [-b bufsize_kb] [command args...]\n\
\n\
         -d              : enable debugging output\n\
         -b bufsize_kb   : set buffer size\n\
         -M              : disable use of mlockall(2)\n\
         -R              : disable use of real-time scheduling\n\
\n");
}

int main(int argc, char **argv)
{
	char *buf, *p, c;
	int bufsize, l, minlen = 0, status, i;
	int maxfd;
	fd_set rfds, wfds;
	int debug = 0, do_mlockall = 1;

	bufsize = 500 * 1024;
	while((c = getopt(argc, argv, "+b:dhRM")) != EOF) {
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
	if((buf = malloc(bufsize)) == NULL) perr("malloc");
	if(do_mlockall && mlockall(MCL_CURRENT | MCL_FUTURE) == -1) perror("mlockall");

	if(optind == argc)
		fd1 = 0;
	else
		fd1 = pipeopen(argv + optind, &pid1);

	fd2 = open("/dev/dsp", O_WRONLY);
	if(fd2 < 0) { perror("/dev/dsp"); exit(1); }
	ioctl(fd2, SNDCTL_DSP_SYNC, 0);
	i = 44100;
	ioctl(fd2, SNDCTL_DSP_SPEED, &i);
	i = AFMT_S16_LE;
	ioctl(fd2, SNDCTL_DSP_SETFMT, &i);
	i = 1;
	ioctl(fd2, SNDCTL_DSP_STEREO, &i);
	
	maxfd = fd1 > fd2? fd1 : fd2;
	
	signal(SIGTERM, sighandler);
	signal(SIGINT, sighandler);
	signal(SIGPIPE, SIG_IGN);
	
	for(;;) {
		if(debug) {
			printf("Bufsize = %4d/%4d\n", len / 1024, bufsize / 1024);
/*			fflush(stdout);*/
		}		
	
		if(!mayread && len == 0) break;

		if((!mayread || len == bufsize) && !maywrite) {  /* off we go! */
			if(do_realtime) {
				struct sched_param sp;
			
				sp.sched_priority = 3;
				if(sched_setscheduler(getpid(), SCHED_FIFO, &sp) < 0)
					perror("sched_setscheduler");

				if(pid1) {
					sp.sched_priority = 2;
					if(sched_setscheduler(pid1, SCHED_FIFO, &sp) < 0)
						perror("sched_setscheduler");
				}
			}

			maywrite = 1;
			minlen = len;
		}

		FD_ZERO(&rfds);
		if(mayread && len < bufsize) FD_SET(fd1, &rfds);
		FD_ZERO(&wfds);
		if(maywrite && len > 0) FD_SET(fd2, &wfds);
		select(maxfd + 1, &rfds, &wfds, NULL, NULL);	

		/* try writing... */
		if(FD_ISSET(fd2, &wfds)) {
			l = len < BLKSIZE? len : BLKSIZE;
			if(l + pos > bufsize) l = bufsize - pos;
			while((l = write(fd2, buf + pos, l)) == -1 && errno == EINTR) ;
			if(l == -1 && errno != EAGAIN) { perror("write"); break; }
			if(l >= 0) {
				len -= l;
				pos = (pos + l) % bufsize;
				continue;
			}
		}

		/* try reading... */
		if(FD_ISSET(fd1, &rfds)) {
			p = buf + (pos + len) % bufsize;
			l = (bufsize - len) < BLKSIZE? (bufsize - len) : BLKSIZE;
			while((l = read(fd1, p, l)) == -1 && errno == EINTR) ;
			if(l == -1 && errno != EAGAIN) { perror("read"); break; }
			if(l == 0) mayread = 0;
			if(l > 0) len += l;
		}
	}
	close(fd1);
	buf[0] = buf[1] = buf[2] = buf[3] = 0;
	write(fd2, buf, 4);
	close(fd2);
	
	if(pid1) {
		waitpid(pid1, &status, 0);
		if(WIFSIGNALED(status)) {
			fprintf(stderr,"cmd1 killed by signal %d.\n", WTERMSIG(status));
			exit(1);
		}
		if(WIFEXITED(status) && WEXITSTATUS(status) != 0) {
			fprintf(stderr,"cmd1 exited with error code %d.\n", WEXITSTATUS(status));
			exit(1);
		}
	}
	return 0;
}
