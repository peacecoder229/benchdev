#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>


static __inline__ unsigned long long __rdtsc(void)
{
   unsigned long lo, hi;

   __asm__ volatile ("rdtsc" : "=a"(lo), "=d"(hi));
   return ((unsigned long long)hi << 32) | lo;
}

int
main(
    int argc,
    char **argv
)
{
    int fd;
    char    *file_map_addr = NULL;
    unsigned long long int map_length;
    int ret;
    struct stat st;
    int i;
    unsigned long long int begin_tsc, diff_tsc;
    unsigned long int num_pages;
    unsigned long int BUFSIZE = 4096;
    unsigned long long int bytes_to_read = 0;

    if (argc < 2){
        printf("usage: %s filename bytes_to_read and blocksize to be read<>\n", argv[0]);
        return -1;
    }

    fd = open(argv[1], O_RDWR);
    if (fd == -1) {
        perror("unable to open input file!\n");
        return -1;
    }
    printf("opened file successfully!\n");

    fstat(fd, &st);
    map_length = (unsigned long long int)st.st_size;
    printf("File length = %llu\n", map_length);

    bytes_to_read = map_length;
    if (argc == 4) {
	BUFSIZE = atol(argv[3]);
        bytes_to_read = atoll(argv[2]);
        if (bytes_to_read > map_length) {
            bytes_to_read = map_length;
        }
    }

    char buf[BUFSIZE];
    file_map_addr = mmap(0, map_length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (file_map_addr == NULL) {
        perror("Unable to mmap()!\n");
        return -1;
    }
    printf("mmap: completed successfully!\n");

    num_pages = bytes_to_read/BUFSIZE;
    begin_tsc = __rdtsc();
    for (i=0; i<num_pages; i++) {
	memcpy(buf, file_map_addr, BUFSIZE);
	file_map_addr += BUFSIZE;
    }
    diff_tsc = __rdtsc() - begin_tsc;
    diff_tsc /= 1000;

    printf("Read %lu pages, elapsed k cycles = %llu\n", num_pages, diff_tsc);
    
    close(fd);
    return 0;
}
