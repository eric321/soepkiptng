
#include <sched.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>

#include "debug.h"

int realtime_on;

void realtime(int on)
{
	struct sched_param sp;

	DEBUG("realtime(%s)\n", on? "on":"off");

	if(realtime_on == on) return;

	/* regain root privileges (from saved uid) */
	if(seteuid(0) < 0) {
		/* no priviledges :-( */
		return;
	}

	if(on) {
#if 0
		sp.sched_priority = 1;
		if(sched_setscheduler(getpid(), SCHED_FIFO, &sp) < 0) {
			perror("sched_setscheduler");
		}
#endif
	} else {
		sp.sched_priority = 0;
		if(sched_setscheduler(getpid(), SCHED_OTHER, &sp) < 0) {
			perror("sched_setscheduler");
		}
	}

	/* surrender root privileges */
	seteuid(getuid());
	
	realtime_on = on;
}

