#include <fcntl.h>
#include <sys/mman.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

#define COPYINCR (1024*1024*1024) /* 1GB */

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("usage: %s <fromfile> <tofile>", argv[0]);
        exit(1);
    }

    int fdin, fdout;
    if ((fdin = open(argv[1], O_RDONLY)) < 0) {
        printf("can not open %s for reading", argv[1]);
        exit(1);
    }

    if ((fdout = open(argv[2] /* typo fix */, O_RDONLY | O_CREAT | O_TRUNC)) < 0) {
        printf("can not open %s for writing", argv[2]);
        exit(1);
    }

    struct stat sbuf;
    if (fstat(fdin, &sbuf) < 0) { /* need size fo input file */
        printf("fstat error");
        exit(1);
    }


    // always zero, and cause truncate error (parameter error)
    printf("input_file size: %lld\n", (long long)sbuf.st_size); 

    if (ftruncate(fdout, sbuf.st_size) < 0) { /* set output file size */
        printf("ftruncate error");
        exit(1);
    }

    void *src, *dst;
    off_t fsz = 0;
    size_t copysz;
    while (fsz < sbuf.st_size) {
        if (sbuf.st_size - fsz > COPYINCR)
            copysz = COPYINCR;
        else
            copysz = sbuf.st_size - fsz;

        if (MAP_FAILED == (src = mmap(0, copysz, PROT_READ,
                        MAP_SHARED, fdin, fsz))) {
            printf("mmap error for input\n");
            exit(1);
        }

        if (MAP_FAILED == (dst = mmap(0, copysz,
                            PROT_READ | PROT_WRITE,
                            MAP_SHARED, fdout, fsz))) {
            printf("mmap error for output\n");
            exit(1);
        }

        memcpy(dst, src, copysz);
        munmap(src, copysz);
        munmap(dst, copysz);

        fsz += copysz;
    }

    return 0;
}
