
#ifndef _DEBUG_H
#define _DEBUG_H

#include <stdio.h>

extern int debug;

#define DEBUG(fmtargs...) do { \
		if(debug >= 1) printf(fmtargs); \
	} while(0)

#define DDEBUG(fmtargs...) do { \
		if(debug >= 2) printf(fmtargs); \
	} while(0)

#define DDDEBUG(fmtargs...) do { \
		if(debug >= 3) printf(fmtargs); \
	} while(0)

#endif /*_DEBUG_H*/
