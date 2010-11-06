
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "output.h"

char *buffer;
int buffer_size;
int buffer_start;
int buffer_length;

int song_counter;
int byte_counter;
int byte_counter_resetcountdown;

void buffer_init()
{
	buffer_size = 500 * 1024;
	if((buffer = malloc(buffer_size)) == NULL) {
		perror("malloc");
		exit(1);
	}
	
	buffer_start = 0;
	buffer_length = SAMPLEFREQ * 4;

	/* preload with 1s of silence */
	memset(buffer, 0, buffer_length);
}
