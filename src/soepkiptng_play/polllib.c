
#include <assert.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/poll.h>

#include "debug.h"
#include "polllib.h"

struct fd_info {
	void (*callback_pre)(int fd, long cookie);
	void (*callback_post)(int fd, short events, long cookie);
	long cookie;
};

int fd_num;
int fd_alloc;
struct pollfd *pollfds;
struct fd_info *fd_infos;

int register_fd(int fd,
	void (*callback_pre)(int fd, long cookie),
	void (*callback_post)(int fd, short events, long cookie),
	long cookie)
{
	int i;
	
	for(i = 0; i < fd_num; i++) {
		if(pollfds[i].fd == fd) {
			// already have this fd
			return -1;
		}
	}

	// get more entries allocated
	if(fd_num == fd_alloc) {
		if(fd_alloc == 0) fd_alloc = 16;
		else fd_alloc *= 2;

		pollfds = realloc(pollfds, sizeof(*pollfds) * fd_alloc);
		fd_infos = realloc(fd_infos, sizeof(*fd_infos) * fd_alloc);
	}

	pollfds[fd_num].fd = fd;
	pollfds[fd_num].events = 0;
	pollfds[fd_num].revents = 0;
	fd_infos[fd_num].callback_pre = callback_pre;
	fd_infos[fd_num].callback_post = callback_post;
	fd_infos[fd_num].cookie = cookie;
	fd_num++;	
	
	return 0;
}

int unregister_fd(int fd)
{
	int i;

	for(i = 0; i < fd_num; i++) {
		if(pollfds[i].fd == fd) {
			if(i != fd_num - 1) {
				// not the last entry; move last entry to this one
				pollfds[i] = pollfds[fd_num - 1];
				fd_infos[i] = fd_infos[fd_num - 1];
			}
			fd_num--;

			// just in case we're in a pre/post for loop
			pollfds[fd_num].events = 0;
			pollfds[fd_num].revents = 0;

			return 0;
		}
	}
	return -1;
}

int get_fd_mask(int fd, short *events)
{
	int i;

	for(i = 0; i < fd_num; i++) {
		if(pollfds[i].fd == fd) {
			*events = pollfds[i].events;
			return 0;
		}
	}
	return -1;
}

int set_fd_mask(int fd, short events)
{
	int i;

	for(i = 0; i < fd_num; i++) {
		if(pollfds[i].fd == fd) {
			pollfds[i].events = events;
			return 0;
		}
	}
	return -1;
}

int register_signal(int sig, void (*callback)(int sig))
{
	return signal(sig, callback) == SIG_ERR? -1 : 0;
}

int unregister_signal(int sig)
{
	signal(sig, SIG_DFL);
	return 0;
}

int mainloop()
{
	int i, num;

	signal(SIGPIPE, SIG_IGN);

	for(;;) {
		for(i = 0; i < fd_num; i++) {
			if(fd_infos[i].callback_pre) {
				fd_infos[i].callback_pre(pollfds[i].fd, fd_infos[i].cookie);
			}
		}
		
		num = poll(pollfds, fd_num, 1000);
		if(num == 0) DEBUG("poll: 0\n");

		for(i = 0; i < fd_num; i++) {
			if(pollfds[i].revents && fd_infos[i].callback_post) {
				fd_infos[i].callback_post(pollfds[i].fd, pollfds[i].revents, fd_infos[i].cookie);
			}
		}
	}
}
