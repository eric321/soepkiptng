
#include "signals.h"
#include "output_oss.h"
#include "polllib.h"
#include "buffer.h"

static void sighup(int s)
{
	if(output_oss_running()) {
		output_oss_stop();
	} else {
		output_oss_start();
	}
}

static void sigusr1(int s)
{
	buffer_start = 0;
	buffer_length = 0;
}

static void sigusr2(int s)
{
	if(output_oss_running()) {
		output_oss_stop();
	}
}

static void sigalarm(int s)
{
   if((byte_counter_resetcountdown = buffer_length) == 0) {
       song_counter++;
       byte_counter = 0;
   }
}


void signals_init()
{
	register_signal(SIGUSR1, sigusr1);
	register_signal(SIGUSR2, sigusr2);
	register_signal(SIGALRM, sigalarm);
	register_signal(SIGHUP, sighup);
}
