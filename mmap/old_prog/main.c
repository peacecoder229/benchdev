#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>


int
main(
    int argc,
    char **argv
)
{
    int fd;
    char    *file_map_addr = NULL;
    int map_length;
    char buf[4096];
    int total_read = 0;
    int ret;
    struct stat st;
    int i;

    if (argc != 2){
        printf("usage: %s filename <>\n", argv[0]);
        return -1;
    }

    fd = open(argv[1], O_RDWR);
    if (fd == -1) {
        perror("unable to open input file!\n");
        return -1;
    }
    printf("opened file successfully!\n");

    fstat(fd, &st);
    map_length = st.st_size;
    printf("File length = %d\n", map_length);

    file_map_addr = mmap(0, map_length, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (file_map_addr == NULL) {
        perror("Unable to mmap()!\n");
        return -1;
    }
    printf("mmap: completed successfully!\n");

    // Read till EOF
    while ((ret = read(fd, buf, sizeof(buf))) != 0) {
	    for (i=0; i<ret; i++) {
            if (file_map_addr[total_read+i] != buf[i]) {
                printf("compare error at offset %d, %x != %x\n", file_map_addr[total_read+i], buf[i]);
                return -1;
            }
	    }
        total_read += ret;
        printf("read %d bytes \r", total_read);
    }

    close(fd);
    return 0;
}
