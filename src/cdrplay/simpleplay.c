
#include<stdio.h>
#include<stdlib.h>
#include<fcntl.h>
#include<unistd.h>
#include<sys/ioctl.h>
#include<linux/soundcard.h>

void play(int sndfd, int fd)
{
	int r;
	char buf[16384];

	for(;;) {
		r = read(fd, buf, 16384);
		if(r < 0) {
			if(errno == EINTR) continue;
			perror("stdin");
			exit(1);
		}
		if(r == 0) break;
		write(sndfd, buf, r);
	}
}

int main(int argc, char **argv)
{
	int sndfd, fd, arg;
	
	sndfd = open("/dev/dsp", O_WRONLY);
	if(sndfd < 0) { perror("/dev/dsp"); exit(1); }
	ioctl(sndfd, SNDCTL_DSP_SYNC, 0);
	arg = 44100;
	ioctl(sndfd, SNDCTL_DSP_SPEED, &arg);
	arg = AFMT_S16_LE;
	ioctl(sndfd, SNDCTL_DSP_SETFMT, &arg);
	arg = 1;
	ioctl(sndfd, SNDCTL_DSP_STEREO, &arg);

	if(argc == 1) play(sndfd, 0);
	else for(arg = 1; arg < argc; arg++) {
		if(strcmp(argv[arg], "-") == 0) fd = 0;
		else {
			fd = open(argv[arg], O_RDONLY);
			if(fd < 0) {
				perror(argv[arg]);
				continue;
			}
		}
		play(sndfd, fd);
		close(fd);
	}
	return 0;
}
