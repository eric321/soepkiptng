
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
#include "output.h"
#include "output_oss.h"

#define BLKSIZE 4096

#ifndef AFMT_S32_LE
#define AFMT_S32_LE 0x00001000
#endif
#ifndef AFMT_S32_BE
#define AFMT_S32_BE 0x00002000
#endif

static char *oss_dev;
static int oss_fd;
static int oss_do_init;
static int oss_samplefreq;
static int oss_fmt;
static int oss_chans;
static int oss_output_channel_offset;
int oss_intercept_resume;
char *channelbuf;
int channelbufalloc;

static int ischardev(int fd)
{
	struct stat st;
	
	if(fstat(fd, &st) == -1) return 0;
	return S_ISCHR(st.st_mode);
}

static void output_oss_post(int fd, short events, long cookie);

static void output_oss_pre(int fd, long cookie)
{
	DDEBUG("output_oss_pre: length=%d oss_do_init=%d\n", buffer_length, oss_do_init);
	
	if(buffer_length < (oss_do_init? oss_samplefreq * 4 : 1)) {
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
	int bs = BLKSIZE;

	if(oss_chans > 2) bs /= oss_chans / 2;
	l = buffer_length;
	if(l > bs) l = bs;
	if(l + buffer_start > buffer_size) {
		l = buffer_size - buffer_start;
	}

	DDEBUG("output_oss_post: start=%6d lenght=%d, writing %d bytes\n", buffer_start, buffer_length, l);

	if(l > 0) {
		char *b = buffer + buffer_start;
		if(oss_chans > 2) {
			if(channelbufalloc < l * oss_chans / 2) {
				channelbufalloc = l * oss_chans / 2;
				channelbuf = realloc(channelbuf, channelbufalloc);
				memset(channelbuf, 0, channelbufalloc);
			}
			if(oss_output_channel_offset != output_channel_offset) {
				// offset changed
				if(output_channel_offset >= oss_chans) {
					output_channel_offset = 0;
				}
				memset(channelbuf, 0, channelbufalloc);
				oss_output_channel_offset = output_channel_offset;
			}
			int srcstride = (oss_fmt == AFMT_S32_LE)? 8 : 4;
			int dststride = srcstride * oss_chans / 2;
			int i, n = l / srcstride;
			DDEBUG("oss_chans=%d l=%d n=%d channelbufalloc=%d srcstride=%d dststride=%d oss_output_channel_offset=%d\n",
				oss_chans, l, n, channelbufalloc, srcstride, dststride, oss_output_channel_offset);
			for(i = 0; i < n; i++) {
				memcpy(channelbuf + i * dststride + output_channel_offset * srcstride,
					b + i * srcstride, srcstride);
			}
			b = channelbuf;
			l = n * dststride;
		}
		if((l = write(fd, b, l)) == -1) {
			if(errno == EINTR || errno == EAGAIN) return;
			perror("write");
			exit(1);
		}
		if(l % (oss_chans / 2)) {
			fprintf(stderr, "write() returned %d, not a multiple of %d\n", l, oss_chans / 2);
		}
		l /= oss_chans / 2;

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

int output_oss_init(char *dev, int samplefreq, int fmt_bits, int chans)
{
	DEBUG("output_oss_init: dev=%s\n", dev);

	if(strcmp(dev, "-") == 0) {
		oss_dev = NULL;
	} else {
		oss_dev = dev;
	}
	oss_fd = -1;
	oss_samplefreq = samplefreq;
	switch(fmt_bits) {
		case 16: oss_fmt = AFMT_S16_LE; break;
		case 32: oss_fmt = AFMT_S32_LE; break;
		default: fprintf(stderr, "oss: %d bits not supported\n", fmt_bits); exit(1);
	}
	oss_chans = chans;
	return 0;
}

int output_oss_start()
{
	int i, retval;
	audio_buf_info bi;

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
	i = oss_fmt;
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_SETFMT, &i);
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_CHANNELS, &oss_chans);
	i = oss_samplefreq;
	if(retval != -1) retval = ioctl(oss_fd, SNDCTL_DSP_SPEED, &i);

	if(retval == -1 && ischardev(oss_fd)) {
		fprintf(stderr, "warning: sound ioctls failed\n");
	}

	if(i != oss_samplefreq)
		fprintf(stderr, "WARNING: wanted samplefreq %d, got %d\n", oss_samplefreq, i);
	
	if(ioctl(oss_fd, SNDCTL_DSP_GETOSPACE, &bi) == 0) {
		fprintf(stderr, "ospace: frags=%d fragstotal=%d fragsize=%d bytes=%d\n",
			bi.fragments, bi.fragstotal, bi.fragsize, bi.bytes);
	}

	oss_do_init = 1;
	
	return register_fd(oss_fd, output_oss_pre, output_oss_post, 0);
}

void output_oss_stop()
{
	/* max 8 channels * 32 bits/sample */
	static char buf[32];

	DEBUG("output_oss_stop\n");
	
	output_oss_reset();

	/* write 1 or 2 samples to prevent badly designed cards to keep the DC value of the last sample */
	write(oss_fd, buf, sizeof(buf));
	close(oss_fd);

	unregister_fd(oss_fd);
	oss_fd = -1;
}

int output_oss_running()
{
	return oss_fd != -1;
}

int output_oss_bytespersecond()
{
	return oss_samplefreq * ((oss_fmt == AFMT_S32_LE)? 8 : 4);
}

void output_oss_reset()
{
	if(ioctl(oss_fd, SNDCTL_DSP_RESET, NULL) < 0) {
		perror("SNDCTL_DSP_RESET");
	}
}

int output_oss_get_odelay()
{
	int delay;
	return ioctl(oss_fd, SNDCTL_DSP_GETODELAY, &delay) == 0? delay : 0;
}
