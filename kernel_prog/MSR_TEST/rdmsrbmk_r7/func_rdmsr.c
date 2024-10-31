#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <linux/types.h>

int fd_msr;


msr_t rdmsr(int addr)
{
	uint32_t buf[2];
	msr_t msr = { 0xffffffff, 0xffffffff };

	if (lseek(fd_msr, (off_t) addr, SEEK_SET) == -1) {
		perror("Could not lseek() to MSR");
		close(fd_msr);
		exit(1);
	}

	if (read(fd_msr, buf, 8) == 8) {
		msr.lo = buf[0];
		msr.hi = buf[1];
		return msr;
	}

	if (errno == 5) {
		printf(" (*)"); // Not all bits of the MSR could be read
		msr_readerror = 1;
	} else {
		// A severe error.
		perror("Could not read() MSR");
		close(fd_msr);
		exit(1);
	}

	return msr;
}
