#include <asm/msr.h>

int NTRIALS=10;
int main()
{
    unsigned long ini, end, now, best, tsc;
    int i;
    char buffer[4];
#define measure_time(code) \
    for (i = 0; i < NTRIALS; i++) { \
	rdtscl(ini); \
        code; \
	rdtscl(end); \
	now = end - ini; \
	if (now < best) best = now; \
    }

    /* time rdtsc (i.e. no code) */
    best = ~0;
    measure_time( 0 );
    tsc = best;

    /* time an empty read() */
    best = ~0;
    measure_time( read(STDIN_FILENO, buffer, 0) );

    /* report data */
    printf("rdtsc: %li ticks\nread(): %li ticks\n",
	   tsc, best-tsc);
    return 0;
}
