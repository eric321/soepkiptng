
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/soundcard.h>
#include <sys/stat.h>

#include "debug.h"
#include "buffer.h"
#include "polllib.h"
#include "output_oss.h"

#define SAMPLEFREQ 44100
#define BLKSIZE 4096
#define BUFFER_MIN (SAMPLEFREQ * 4)

static char *oss_dev;
static int oss_fd;
static int oss_do_init;
int oss_intercept_resume;

static int ischardev(int fd)
{
	struct stat st;
	
	if(fstat(fd, &st) == -1) return 0;
	return S_ISCHR(st.st_mode);
}

static void output_oss_pre(int fd, long cookie)
{
	DDEBUG("output_oss_pre: length=%d oss_do_init=%d\n", buffer_length, oss_do_init);
	
	if(buffer_length < (oss_do_init? BUFFER_MIN : 1)) {
		set_fd_mask(fd, 0);
		return;
	}

	if(oss_do_init) {
		char buf[4096];

		DEBUG("oss_do_init\n");
		
		memset(buf, 0, sizeof(buf));
		write(fd, buf, sizeof(buf));

		oss_do_init = 0;
	}

	set_fd_mask(fd, POLLOUT);
}

static void output_oss_post(int fd, short events, long cookie)
{
	int l;

	l = buffer_length;
	if(l > BLKSIZE) l = BLKSIZE;
	if(l + buffer_start > buffer_size) {
		l = buffer_size - buffer_start;
	}

	DDEBUG("output_oss_post: start=%6d lenght=%d, writing %d bytes\n", buffer_start, buffer_length, l);

	if(l > 0) {
		if((l = write(fd, buffer + buffer_start, l)) == -1) {
			if(errno == EINTR || errno == EAGAIN) return;
			perror("write");
			exit(1);
		}

		buffer_length -= l;
		buffer_start += l;
		if(buffer_start >= buffer_size) {
			buffer_start -= buffer_size;
		}
	   byte_counter += l;
		if(byte_counter_resetcountdown) {
		   byte_counter_resetcountdown -= l;
		   if(byte_counter_resetcountdown <= 0) {
		      byte_counter = -byte_counter_resetcountdown;
		      byte_counter_resetcountdown = 0;
		      song_counter++;
		   }
		}
	}

	DDEBUG("output_oss_post: start=%6d length=%d\n", buffer_start, buffer_length);

	/* flush data in soundcard driver if we are out of data */
	if(buffer_length == 0) {
		DEBUG("output_oss_post: DSP_POST\n");
		ioctl(fd, SNDCTL_DSP_POST, 0);
	}
}

int output_oss_init(char *dev)
{
	DEBUG("output_oss_init: dev=%s\n", dev);

	if(strcmp(dev, "-") == 0) {
		oss_dev = NULL;
	} else {
		oss_dev = dev;
	}
	oss_fd = -1;
	return 0;
}

int output_oss_start()
{
	int i, retval;

	DEBUG("output_oss_start: oss_dev=%s\n", oss_dev);
	
	if(oss_fd != -1) {
		/* already started */
		return 0;
	}
	
	if(oss_intercept_resume) {
		oss_intercept_resume = 0;
		return 0;
	}

	if(oss_dev) {
		oss_fd = open(oss_dev, O_WRONLY | O_CREAT | O_TRUNC, 0666);
		if(oss_fd < 0) {
			perror(oss_dev);
			return -1;
		}
	} else {
		oss_fd = 1;
	}

	retval = ioctl(oss_fd, SNDCTL_DSP_SYNC, 0);
	i = AFMT_S16_LE;
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_SETFMT, &i);
	i = 1;
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_STEREO, &i);
	i = 44100;
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_SPEED, &i);

	if(retval == -1 && ischardev(oss_fd)) {
		fprintf(stderr, "warning: sound ioctls failed\n");
	}
	
	fcntl(oss_fd, F_SETFL, O_NONBLOCK);
	
	oss_do_init = 1;
	
	return register_fd(oss_fd, output_oss_pre, output_oss_post, 0);
}

void output_oss_stop()
{
	char buf[4] = { 0, 0, 0, 0 };

	DEBUG("output_oss_stop\n");

	/* write 1 sample to prevent badly designed cards to keep the DC value of the last sample */
	write(oss_fd, buf, 4);
	close(oss_fd);

	unregister_fd(oss_fd);
	oss_fd = -1;
}

int output_oss_running()
{
	return oss_fd != -1;
}
