
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/poll.h>

#include "polllib.h"
#include "buffer.h"

#define BLKSIZE 4096

static void input_pre(int fd, long cookie)
{
	if(buffer_length < buffer_size) {
   	set_fd_mask(fd, POLLIN);
   } else {
   	set_fd_mask(fd, 0);
   }
}

static void input_post(int fd, short events, long cookie)
{
	int dst, l;

	dst = (buffer_start + buffer_length) % buffer_size;
	l = buffer_size - buffer_length;
	if(l > BLKSIZE) l = BLKSIZE;
	if(l > buffer_size - dst) l = buffer_size - dst;

	if((l = read(fd, buffer + dst, l)) == -1) {
		if(errno == EINTR) return;
		perror("read");
		exit(1);
	}
	
	if(l == 0) {
		//EOF
		unregister_fd(0);
		return;
	}
	
	buffer_length += l;
}

void input_start()
{
	if(register_fd(0, 0, input_pre, input_post, 0) < 0) {
		exit(1);
	}
}
