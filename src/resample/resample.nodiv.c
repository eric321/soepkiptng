
static char rcsid[] = "$Id$";

#include <stdio.h>
#include <stdlib.h>

struct sample {
	short l;
	short r;
};

#define MULT_BITS 32
#define MULT (1LL << MULT_BITS)
#define BUFSIZE 1024

int main(int argc, char **argv)
{
	unsigned long long tstep, t;
	int s, d, len;
	static struct sample src[BUFSIZE + 1], dst[BUFSIZE];
	int termflag, debug = 0;

	while(argc > 1 && strcmp(argv[1], "-d") == 0) {
		argc--;
		argv++;
		debug++;
	}
	if(argc != 3) {
		fprintf(stderr,"\
Usage: resample f_in f_out\n\
\n\
       f_in    : input sampling frequency\n\
       f_out   : output sampling frequency\n\
\n\
       stdin   : 16-bit stereo little-endian input\n\
       stdout  : 16-bit stereo little-endian output\n\
\n");
		exit(1);
	}

	tstep = (long long)(MULT * atof(argv[1]) / atof(argv[2]) + 0.5);
	if(debug)
		fprintf(stderr, "tstep=%Ld = 2^32 * %f, err=%e\n",
			tstep, (double)tstep/MULT, (double)tstep/MULT - atof(argv[1]) / atof(argv[2]));

	if((len = fread(src, sizeof(struct sample), BUFSIZE, stdin)) < 1) exit(0);
	if(len == 1) {
		src[1].l = src[1].r = 0;
		termflag = 1;
	}
	t = 0;
	s = 1;
	d = 0;
	termflag = 0;
	for(;;) {
#if 1
		dst[d].l = (t * (src[s].l - src[s - 1].l) >> MULT_BITS) + src[s - 1].l;
		dst[d].r = (t * (src[s].r - src[s - 1].r) >> MULT_BITS) + src[s - 1].r;
#else
		fprintf(stderr,"s=%d d=%d t=%Lu\n", s, d, t);
		asm ("movw %2, %%ebx;
		      movw %3, %%eax;
		      subl %%ebx, %%eax;
		      mull %1;
		      addl %%ebx, %%edx;
		      movw %%edx, %0"

			: "=m" (dst[d].l)
			: "m" (t), "m" (src[s - 1].l) , "m" (src[s].l)
			: "edx", "ebx", "eax", "cc");
		asm ("movw %2, %%ebx;
		      movw %3, %%eax;
		      subl %%ebx, %%eax;
		      mull %1;
		      addl %%ebx, %%edx;
		      movw %%edx, %0"

			: "=m" (dst[d].r)
			: "m" (t), "m" (src[s - 1].r) , "m" (src[s].r)
			: "edx", "ebx", "eax", "cc");
#endif
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
		while(t >= MULT) {
			t -= MULT;
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
				if((len = fread(src + 1, sizeof(struct sample), BUFSIZE, stdin)) > 0) {
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
