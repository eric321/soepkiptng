
#include <string.h>

#include "output.h"
#ifndef NO_ALSA
#include "output_alsa.h"
#endif
#include "output_oss.h"

int (*output_start)();
void (*output_stop)();
void (*output_reset)();
int (*output_running)();
int (*output_bytespersample)();

int output_init(char *dev, int samplefreq, int fmt_bits)
{
#ifndef NO_ALSA
	if(memcmp(dev, "alsa:", 5) == 0) {
		output_start = output_alsa_start;
		output_stop = output_alsa_stop;
		output_reset = output_alsa_reset;
		output_running = output_alsa_running;
		output_bytespersample = output_alsa_bytespersample;
		return output_alsa_init(dev + 5, samplefreq, fmt_bits);
	}
#endif
	output_start = output_oss_start;
	output_stop = output_oss_stop;
	output_reset = output_oss_reset;
	output_running = output_oss_running;
	output_bytespersample = output_oss_bytespersample;
	return output_oss_init(dev, samplefreq, fmt_bits);
}
