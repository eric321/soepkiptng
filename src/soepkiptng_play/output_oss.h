
#ifndef _OUTPUT_H
#define _OUTPUT_H

int output_oss_init(char *dev);

int output_oss_start();
void output_oss_stop();
int output_oss_running();

#endif /*_OUTPUT_H*/
