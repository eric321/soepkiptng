
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <alsa/asoundlib.h>
#include <sys/ioctl.h>
#include <sys/stat.h>

#include "debug.h"
#include "buffer.h"
#include "polllib.h"
#include "output_alsa.h"

#define BLKSIZE 4096

static char *alsa_dev;
static int alsa_samplefreq;
static int alsa_fmt;
static snd_pcm_t *alsa_handle;

int output_alsa_init(char *dev, int samplefreq, int fmt_bits)
{
	DEBUG("output_alsa_init: dev=%s\n", dev);

	alsa_dev = dev;
	alsa_samplefreq = samplefreq;
	switch(fmt_bits) {
		case 16: alsa_fmt = SND_PCM_FORMAT_S16_LE; break;
		case 32: alsa_fmt = SND_PCM_FORMAT_S32_LE; break;
		default: fprintf(stderr, "alsa: %d bits not supported\n", fmt_bits); exit(1);
	}
	return 0;
}

int output_alsa_start()
{
	int err;
	snd_pcm_hw_params_t *alsa_params;
	
	if((err = snd_pcm_open(&alsa_handle, alsa_dev, SND_PCM_STREAM_PLAYBACK, 0)) < 0) {
		fprintf(stderr, "cannot open audio device %s (%s)\n", alsa_dev, snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_nonblock(alsa_handle, 1)) < 0) {
		fprintf(stderr, "cannot set audio device %s to non-blocking (%s)\n", alsa_dev, snd_strerror(err));
		exit(1);
	}
	
	if ((err = snd_pcm_hw_params_malloc(&alsa_params)) < 0) {
		fprintf(stderr, "cannot allocate hardware parameter structure (%s)\n", snd_strerror (err));
		exit(1);
	}
                                                                         
	if((err = snd_pcm_hw_params_any(alsa_handle, alsa_params)) < 0) {
		fprintf(stderr, "cannot initialize hardware parameter structure (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_hw_params_set_access(alsa_handle, alsa_params, SND_PCM_ACCESS_RW_INTERLEAVED)) < 0) {
		fprintf(stderr, "cannot set access type (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_hw_params_set_format(alsa_handle, alsa_params, alsa_fmt)) < 0) {
		fprintf(stderr, "cannot set sample format (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_hw_params_set_rate(alsa_handle, alsa_params, alsa_samplefreq, 0)) < 0) {
		fprintf(stderr, "cannot set sample rate (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_hw_params_set_channels(alsa_handle, alsa_params, 2)) < 0) {
		fprintf(stderr, "cannot set channel count (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	if((err = snd_pcm_hw_params(alsa_handle, alsa_params)) < 0) {
		fprintf(stderr, "cannot set parameters (%s)\n", snd_strerror(err));
		exit(1);
	}
	
	snd_pcm_hw_params_free(alsa_params);
	
	if((err = snd_pcm_prepare(alsa_handle)) < 0) {
		fprintf(stderr, "cannot prepare audio interface for use (%s)\n", snd_strerror(err));
		exit(1);
	}

#if 1
	fprintf(stderr, "sorry, alsa support is incomplete...\n");
	exit(1);
#endif

	return 0;
}

void output_alsa_stop()
{
	DEBUG("output_alsa_stop\n");

//	unregister_fd(alsa_fd);
	snd_pcm_close(alsa_handle);
	alsa_handle = 0;
}

int output_alsa_running()
{
	return alsa_handle != NULL;
}

int output_alsa_bytespersample()
{
	return alsa_samplefreq * ((alsa_fmt == SND_PCM_FORMAT_S32_LE)? 8 : 4);
}

void output_alsa_reset()
{
}

