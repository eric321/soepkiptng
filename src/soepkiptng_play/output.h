
#ifndef _OUTPUT_H
#define _OUTPUT_H

#define SAMPLEFREQ 44100

int output_init(char *dev, int samplefreq, int fmt_bits);

extern int (*output_start)();
extern void (*output_stop)();
extern void (*output_reset)();
extern int (*output_running)();
extern int (*output_bytespersecond)();
extern int (*output_get_odelay)();

#endif /*_OUTPUT_H*/

