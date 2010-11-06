
#include "signals.h"
#include "output.h"
#include "polllib.h"
#include "buffer.h"
#include "input.h"

static void sighup(int s)
{
	if(output_running()) {
		output_stop();
	} else {
		output_start();
	}
}

static void sigusr1(int s)
{
	input_flush();
}

static void sigusr2(int s)
{
	if(output_running()) {
		output_stop();
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
