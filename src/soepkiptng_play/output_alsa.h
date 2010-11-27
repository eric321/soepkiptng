
#ifndef _OUTPUT_ALSA_H
#define _OUTPUT_ALSA_H

int output_alsa_init(char *dev, int samplefreq, int fmt_bits);

int output_alsa_start();
void output_alsa_stop();
void output_alsa_reset();
int output_alsa_running();
int output_alsa_bytespersecond();
int output_alsa_get_odelay();

#endif /*_OUTPUT_ALSA_H*/

