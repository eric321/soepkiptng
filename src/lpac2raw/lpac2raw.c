
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>

#define SFREQ 44100

struct wav_file_header {
   char riff[4];
   unsigned len;
   char id[4];
};

struct wav_chunk_header {
   char id[4];
   unsigned len;
};

struct wav_fmt_header {
   unsigned short format;
   unsigned short channels;
   unsigned samples_per_sec;
   unsigned bytes_per_sec;
   unsigned short align;
   unsigned short bits_per_sample;
}; 

void fmterror()
{
	fprintf(stderr, "WAV file format error.\n");
	exit(1);
}

void copybytes(FILE *fin, FILE *fout, int n)
{
	char buf[4096];
	int r, tot;
	
	/* n == 0 is a special case: read until eof */
	tot = 0;
	while(n == 0 || tot < n) {
		r = fread(buf, 1, n < sizeof(buf)? n : sizeof(buf), fin);
		if(r > 0) {
			if(fout) fwrite(buf, 1, r, fout);
			tot += r;
		} else if(n == 0 && r == 0) {
			return;
		} else {
			fmterror();
		}
	}
}
	
int readwavheader(FILE *fin, int *sfreq, int *channels, int *seconds)
{
   struct wav_file_header filehdr;
   struct wav_chunk_header chunkhdr;
   struct wav_fmt_header fmthdr;
   
   
   if(fread(&filehdr, sizeof(filehdr), 1, fin) != 1)
   	fmterror();

   for(;;) {
      if(fread(&chunkhdr, sizeof(chunkhdr), 1, fin) != 1)
      	fmterror();
      if(strncmp(chunkhdr.id, "fmt ", 4) == 0) break;
      copybytes(fin, NULL, chunkhdr.len);
   }

   if(fread(&fmthdr, sizeof(fmthdr), 1, fin) != 1)
   	fmterror();

   if(fmthdr.format != 1)
   	fmterror();

   if(fmthdr.channels > 2)
   	fmterror();

   if(fmthdr.bits_per_sample != 16)
   	fmterror();

   if(fmthdr.align != 2 && fmthdr.align != 4)
   	fmterror();

   for(;;) {
      if(fread(&chunkhdr, sizeof(chunkhdr), 1, fin) != 1)
         fmterror();
      if(strncmp(chunkhdr.id, "data", 4) == 0) break;
      copybytes(fin, NULL, chunkhdr.len);
   }
   *sfreq = fmthdr.samples_per_sec;
   *channels = fmthdr.channels;
   *seconds = (chunkhdr.len / fmthdr.align + fmthdr.samples_per_sec / 2)
  		/ fmthdr.samples_per_sec;
	return chunkhdr.len / fmthdr.align;
}

int main(int argc, char **argv)
{
	int fd[2], freq, chan, bytes, secs;

	if(argc < 2) {
		fprintf(stderr, "usage: lpac2raw file [x]\n");
		exit(1);
	}

	pipe(fd);
	switch(fork()) {
		case 0:
			dup2(fd[1], 1);
			close(fd[0]);
			close(fd[1]);
			execlp("lpac", "lpac", "-x", argv[1], "/dev/fd/1", NULL);
			perror("lpac");
			exit(1);
		case -1:
			perror("fork");
			exit(1);
	}
	dup2(fd[0], 0);
	close(fd[0]);
	close(fd[1]);

	bytes = readwavheader(stdin, &freq, &chan, &secs);
	
	if(argc > 2) {
		printf("%d,%d,%d\n", freq, chan, secs);
		exit(0);
	}
	if(freq != SFREQ || chan != 2) {
		int fd[2];

		pipe(fd);
		switch(fork()) {
			case 0: {
				char freq_in[12], freq_out[12];
				
				sprintf(freq_in, "%d", freq);
				sprintf(freq_out, "%d", SFREQ);
				dup2(fd[0], 0);
				close(fd[0]);
				close(fd[1]);
				if(chan == 1) {
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

	copybytes(stdin, stdout, bytes);
	
	close(0);
	close(1);
	while(wait(NULL) > 0) { }

	return 0;
}

