
#ifndef _POLLLIB_H
#define _POLLLIB_H

#include <signal.h>
#include <sys/poll.h>

/* all functions return -1 on error, 0 on success */


/* register file descriptor handler */
int register_fd(int fd, short events,
	void (*callback_pre)(int fd, long cookie),
	void (*callback_post)(int fd, short events, long cookie),
	long cookie);

/* unregister file descriptor */
int unregister_fd(int fd);

/* get event mask */
int get_fd_mask(int fd, short *events);

/* set event mask */
int set_fd_mask(int fd, short events);


/* register signal handler */
int register_signal(int sig, void (*callback)(int sig));

/* unregister signal handler */
int unregister_signal(int sig);

/* main loop */
int mainloop();

#endif /**/
