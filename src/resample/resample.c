
static char rcsid[] = "$Id$";

#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>

struct sample {
	short l;
	short r;
};

int mono2stereo = 0;

#define BUFSIZE 1024

/* OK I know it's not efficient to do mono->stereo first
  and then the resampling, but it was easier to code */

int myread(struct sample *buf, int n, FILE *f)
{
	static short monosamples[BUFSIZE];
	int i, r;

	if(!mono2stereo)
		return fread(buf, sizeof(struct sample), n, f);
	
	r = fread(monosamples, sizeof(short), n, f);
	for(i = 0; i < r; i++) buf[i].l = buf[i].r = monosamples[i];
	return r;
}

int main(int argc, char **argv)
{
	int tstep, tperiod, t, i, common, s, d, len;
	struct sample src[BUFSIZE + 1], dst[BUFSIZE];
	int termflag, debug = 0, c;

	while((c = getopt(argc, argv, "ds")) != EOF) {
		switch(c) {
			case 'd':
				debug++;
				break;
			case 's':
				mono2stereo = 1;
				break;
		}
	}
	if(argc != optind + 2) {
		fprintf(stderr,
"Usage: resample [-ds] f_in f_out\n"
"\n"
"       -s      : input is mono (convert to stereo)\n"
"\n"
"       f_in    : input sampling frequency\n"
"       f_out   : output sampling frequency\n"
"\n"
"       stdin   : 16-bit stereo little-endian input\n"
"       stdout  : 16-bit stereo little-endian output\n"
"\n");
		exit(1);
	}

	tstep = atoi(argv[optind]);
	tperiod = atoi(argv[optind + 1]);
	for(i = 2, common = 1; i <= tstep && i <= tperiod; i++) {
		while(tstep % i == 0 && tperiod % i == 0) {
			tstep /= i;
			tperiod /= i;
			common *= i;
		}
	}
	if(debug) fprintf(stderr, "tstep=%d tperiod=%d\n", tstep, tperiod);
	if(tperiod > 65536) {
		i = (tperiod + 65535) / 65536;
		fprintf(stderr, "Warning: conversion rate changed from %d/%d to %d/%d.\n",
			tstep * common, tperiod * common,
			(tstep / i) * i * common, (tperiod / i) * i * common);
		tstep /= i;
		tperiod /= i;
	}

	if((len = myread(src, BUFSIZE, stdin)) < 1) exit(0);
	if(len == 1) {
		src[1].l = src[1].r = 0;
		termflag = 1;
	}
	t = 0;
	s = 1;
	d = 0;
	termflag = 0;
	for(;;) {
		dst[d].l = ((tperiod - t) * src[s - 1].l + t * src[s].l) / tperiod;
		dst[d].r = ((tperiod - t) * src[s - 1].r + t * src[s].r) / tperiod;
		d++;
		if(debug) fprintf(stderr,"d=%d\n",d);

		if(d == BUFSIZE) {
			if(fwrite(dst, sizeof(struct sample), d, stdout) != d) exit(1);
			d = 0;
		}
		if(t == 0 && termflag) {
			if(fwrite(dst, sizeof(struct sample), d, stdout) != d) exit(1);
			exit(0);
		}
		t += tstep;
		while(t >= tperiod) {
			t -= tperiod;
			s++;
			if(debug) fprintf(stderr,"       s=%d/%d\n",s, len);
			if(s == len) {
				if(termflag) {
					if(debug) fprintf(stderr,"_d=%d\n",d);
					if(fwrite(dst, sizeof(struct sample), d, stdout) != d) exit(1);
					exit(0);
				}
				src[0] = src[len - 1];
				s = 1;
				if((len = myread(src + 1, BUFSIZE, stdin)) > 0) {
					len++;
				} else {
					src[1].l = src[1].r = 0;
					len = 2;
					termflag = 1;
				}	
				if(debug) fprintf(stderr,"       s=%d/%d\n",s, len);
			}
		}
	}
}
