
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <unistd.h>
#include "vorbis/codec.h"
#include "vorbis/vorbisfile.h"

#define SFREQ 44100

int main(int argc, char **argv)
{
	OggVorbis_File vf;
	char c;
	int info_only = 0;
	int len;
	int current_section;
	char pcmout[4096];
	FILE *input;
	vorbis_info *vi;

	while((c = getopt(argc, argv, "i")) != EOF) {
		switch(c) {
			case 'i':
				info_only = 1;
				break;
		}
	}
	if(optind != argc - 1) {
		fprintf(stderr, "usage: ogg2raw [-i] file\n");
		exit(1);
	}
	input = fopen(argv[optind], "r");
	if(input == NULL) {
		perror(argv[1]);
		exit(1);
	}

	if(ov_open(input, &vf, NULL, 0) < 0) {
		fprintf(stderr, "Input does not appear to be an Ogg bitstream.\n");
		exit(1);
	}

	vi = ov_info(&vf, -1);
	if(info_only) {
		int br = ov_bitrate(&vf, -1);
		len = 0;
		if(ov_seekable(&vf)) len = ov_time_total(&vf, -1);
		printf("%ld,%d,%d,%d\n", vi->rate, vi->channels, len, br);
		exit(0);
	}
	
	if(vi->channels == 1 || vi->rate != SFREQ) {
		int fd[2];

		pipe(fd);
		switch(fork()) {
			case 0: {
				char freq_in[12], freq_out[12];
				
				sprintf(freq_in, "%ld", vi->rate);
				sprintf(freq_out, "%d", SFREQ);
				dup2(fd[0], 0);
				close(fd[0]);
				close(fd[1]);
				if(vi->channels == 1) {
					execlp("resample", "resample", "-s", freq_in, freq_out, NULL);
				} else {
					execlp("resample", "resample", freq_in, freq_out, NULL);
				}
				exit(1);
			}
			case -1:
				perror("fork");
				exit(1);
		}
		dup2(fd[1], 1);
		close(fd[0]);
		close(fd[1]);
	}

	for(;;) {
		len = ov_read(&vf, pcmout, sizeof(pcmout), 0, 2, 1, &current_section);
		if(len == 0) break;
		if(len == -1) continue;
		fwrite(pcmout, 1, len, stdout);
	}

	/* cleanup */
	ov_clear(&vf);

	return 0;
}
