
#ifndef _BUFFER_H
#define _BUFFER_H

extern char *buffer;
extern int buffer_size;
extern int buffer_start;
extern int buffer_length;

extern int song_counter;
extern int byte_counter;
extern int byte_counter_resetcountdown;

void buffer_init();

#endif /*_BUFFER_H*/
