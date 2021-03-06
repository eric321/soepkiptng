
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>

#include "buffer.h"
#include "debug.h"              
#include "polllib.h"
#include "socket.h"
#include "output.h"
#include "output_oss.h"


struct socket_t {
	char inbuf[256];
	int inlen;

	char outbuf[256];
	int outoff;
	int outlen;

	int waitbufferempty;
};

static void initsock(struct socket_t *p)
{
	p->inlen = 0;

	p->outoff = 0;
	p->outlen = sprintf(p->outbuf, "+This is soepkiptng_play.\n");

	p->waitbufferempty = 0;
}

static void closesock(int fd, struct socket_t *p)
{
	free(p);
	close(fd);
	unregister_fd(fd);
}

static void sockprintf(struct socket_t *p, char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	p->outlen = vsnprintf(p->outbuf, sizeof(p->outbuf), fmt, ap);
	va_end(ap);
}

static void handle_cmd(int fd, struct socket_t *p, char *s)
{
	char *cmd;
	
	cmd = strtok(s, " \t");
	p->outoff = 0;
	
	if(cmd == NULL) {
		sockprintf(p, "-No command\n");
		return;
	}

	if(strcasecmp(cmd, "quit") == 0) {
		closesock(fd, p);
	}

	if(strcasecmp(cmd, "output") == 0) {
		output_channel_offset = atoi(strtok(NULL, " \t"));
		sockprintf(p, "+OK\n");
	}

	else if(strcasecmp(cmd, "pause") == 0) {
		if(output_running()) {
			sockprintf(p, "+OK\n");
			output_stop();
		} else {
			sockprintf(p, "-Not running\n");
		}
	}

	else if(strcasecmp(cmd, "waitbufferempty") == 0) {
		p->waitbufferempty = 1;
		if(!output_running()) {
			buffer_length = 0;
			oss_intercept_resume = 1;
		}
	}

	else if(strcasecmp(cmd, "resume") == 0) {
		if(output_running()) {
			sockprintf(p, "-Already running\n");
		} else {
			output_start();
			sockprintf(p, "+OK\n");
		}
	}

	else if(strcasecmp(cmd, "pausetoggle") == 0) {
		if(output_running()) {
			output_stop();
		} else {
			output_start();
		}
		sockprintf(p, "+OK\n");
	}

	else if(strcasecmp(cmd, "status") == 0) {
		int b = byte_counter - output_get_odelay();
		if(b < 0) b = 0;
		int s100 = (100LL * b) / output_bytespersecond();
		sockprintf(p, "+running=%d song=%d time=%d.%02d\n",
		   output_running(),
		   song_counter,
		   s100 / 100, s100 % 100);
	}

	else if(strcasecmp(cmd, "dump") == 0) {
		sockprintf(p, "+running=%d start=%d length=%d song_counter=%d byte_counter=%d byte_counter_resetcountdown=%d\n",
		   output_running(), buffer_start, buffer_length, song_counter, byte_counter, byte_counter_resetcountdown);
	}

	else {
		sockprintf(p, "-Unknown command\n");
	}
}

static void socket_pre(int fd, long cookie)
{
	struct socket_t *p = (struct socket_t *)cookie;

	if(p->waitbufferempty) {
		DDEBUG("socket_pre[%d]: waitbufferempty buffer_length=%d\n", fd, buffer_length);
		if(!oss_intercept_resume && buffer_length == 0) {
			sockprintf(p, "+OK\n");
			p->waitbufferempty = 0;
		} else {
			set_fd_mask(fd, 0);
			return;
		}
	}

	if(p->outlen > 0) {
		set_fd_mask(fd, POLLOUT);
		DDEBUG("socket_pre: pollout (outlen=%d)\n", p->outlen);
	} else if(p->inlen < sizeof(p->inbuf)) {
		set_fd_mask(fd, POLLIN);
		DDEBUG("socket_pre: pollin (inlen=%d < %d)\n", p->inlen, sizeof(p->inbuf));
	}
}

static void socket_post(int fd, short events, long cookie)
{
	struct socket_t *p = (struct socket_t *)cookie;

	if(events & (POLLERR | POLLHUP | POLLNVAL)) {
		DEBUG("socket poll: revents=%hd, closing socket.\n", events);
		closesock(fd, p);
		return;
	}

	if(events & POLLIN) {
		char *s;
		int r;

		if((r = read(fd, p->inbuf + p->inlen, sizeof(p->inbuf) - p->inlen)) <= 0) {
			if(r == -1 && (errno == EINTR || errno == EAGAIN)) return;

			DEBUG("socket read: read %d bytes, errno=%d\n", r, r == -1? errno : 0);
			closesock(fd, p);
			return;
		}
		p->inlen += r;
		DEBUG("socket fd %d: read %d bytes inlen=%d\n", fd, r, p->inlen);

		if((s = memchr(p->inbuf, '\n', p->inlen))) {
			int len = s - p->inbuf;
			p->inbuf[len] = 0;
			if(len > 0 && p->inbuf[len - 1] == '\r') {
				p->inbuf[len - 1] = 0;
			}
			handle_cmd(fd, p, p->inbuf);
			p->inlen -= len + 1;
			if(len > 0) memmove(p->inbuf, s + 1, p->inlen);
		}
	}
	
	if(events & POLLOUT) {
		int w;
		
		if((w = write(fd, p->outbuf + p->outoff, p->outlen)) < 0) {
			if(errno == EINTR || errno == EAGAIN) return;
			closesock(fd, p);
			return;
		}

		p->outoff += w;
		p->outlen -= w;
		if(p->outlen == 0) p->outoff = 0;

		DEBUG("socket fd %d: wrote %d bytes outoff=%d outlen=%d\n", fd, w, p->outoff, p->outlen);
	}
}



static void listensocket_post(int fd, short events, long cookie)
{
	int newsock;

	if((newsock = accept(fd, NULL, NULL)) >= 0) {
		struct socket_t *p;
		
		if((p = malloc(sizeof(*p))) != NULL &&
		   register_fd(newsock, socket_pre, socket_post, (long)p) == 0) {

			initsock(p);
		} else {
			close(newsock);
		}
	}
}

void socket_init(int port)
{
	int sock, i;
	struct sockaddr_in addr;
	
	if((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror("socket");
		exit(1);
	}
	
	i = 1;
	setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &i, sizeof(i));

   memset((char *)&addr, 0, sizeof(addr));
   addr.sin_family = AF_INET;
   addr.sin_addr.s_addr = htonl(INADDR_ANY);
   addr.sin_port = htons(port);
	if(bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
		perror("bind");
		exit(1);
	}

	if(listen(sock, 5) < 0) {
		perror("listen");
		exit(1);
	}

	if(register_fd(sock, NULL, listensocket_post, 0) < 0) {
		exit(1);
	}
	set_fd_mask(sock, POLLIN);
}
