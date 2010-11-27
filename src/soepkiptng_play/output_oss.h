
#ifndef _OUTPUT_OSS_H
#define _OUTPUT_OSS_H

int output_oss_init(char *dev, int samplefreq, int fmt_bits);

int output_oss_start();
void output_oss_stop();
void output_oss_reset();
int output_oss_running();
int output_oss_bytespersecond();
int output_oss_get_odelay();

int oss_intercept_resume;

#endif /*_OUTPUT_OSS_H*/

