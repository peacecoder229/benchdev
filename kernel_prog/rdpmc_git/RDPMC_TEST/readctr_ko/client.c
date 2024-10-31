
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sched.h>
#include <pthread.h>

#include <time.h>
#include <sys/syscall.h>

#include "client.h"

#define gettid() syscall(__NR_gettid)

#define BUFF_SPACE sizeof(char)* 1024 * 4 //4K
static char output_buff[BUFF_SPACE] ;

void output_metrics(Events e[], int size)
{
    int i;
    memset(output_buff, 0, BUFF_SPACE);

    sprintf(output_buff, "TSC: ");
    // sprintf(output_buff, "TS:%0.4f\nTSC: ", (float)time(NULL));
    for (i = 0; i < size; i++)
        sprintf(output_buff, "%s%llu\t",output_buff, e[i].tsc);

    sprintf(output_buff, "%s\nCTRL0: ", output_buff);
    for (i = 0; i < size; i++)
        sprintf(output_buff, "%s%llu\t",output_buff, e[i].ctrl_0);

    sprintf(output_buff, "%s\nCTRL1: ", output_buff);
    for (i = 0; i < size; i++)
        sprintf(output_buff, "%s%llu\t",output_buff, e[i].ctrl_1);

    sprintf(output_buff, "%s\nCTRL2: ", output_buff);
    for (i = 0; i < size; i++)
        sprintf(output_buff, "%s%llu\t",output_buff, e[i].ctrl_2);

    sprintf(output_buff, "%s\nCTRL3: ", output_buff);
    for (i = 0; i < size; i++)
        sprintf(output_buff, "%s%llu\t",output_buff, e[i].ctrl_3);

    printf("%s\n---\n", output_buff);
}

int main_loop(int interval_us, int iter)
{

    int i = 0, j;
    int cpu_num = sysconf(_SC_NPROCESSORS_CONF);
    // cpu_num = 8;

    cpu_set_t mask;
    int cur_core;
    Events e[cpu_num];

    // initial memory space
    memset(e, 0, sizeof(Events)*cpu_num);

    do
    {

        for (cur_core = 0; cur_core < cpu_num; cur_core++)
        {
            // run rdpmc on each CPU cores
            CPU_ZERO(&mask);
            CPU_SET(cur_core, &mask);

            if (sched_setaffinity(0, sizeof(mask), &mask) == -1)
            {
                printf("set affinity failed\n");
                return 1;
            }

            read_event(&e[cur_core]);

            //usleep(interval);
        }

        output_metrics(e, cpu_num);

        i++;
        usleep(interval_us);

    } while (-1 == iter || i < iter);

    return 0;
}

int main(int argc, char *argv[])
{
    int interval = 1000; // 1st parameter: set smapling interval by ms
    int iter = -1; //2nd parameter: loops

    if (argc >= 3)
    {
        interval = atoi(argv[1]);
        iter = atoi(argv[2]);
    }

    if (argc == 2)
        interval = atoi(argv[1]);

    return main_loop(interval * 1000, iter);

}
