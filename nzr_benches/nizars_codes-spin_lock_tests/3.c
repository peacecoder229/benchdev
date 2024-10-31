#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <unistd.h>
#include <sys/time.h>
#define time_usec() ({struct timeval tp; gettimeofday(&tp, 0); tp.tv_sec * 1.e6 + tp. tv_usec;})
int threads=36;

unsigned long long sum = 0;

unsigned long long MAX = 0xFFFFFF;
//unsigned long long MAX = 0xFFFFFF;
pthread_mutex_t lock;
void spin_lock(long *);
void spin_unlock(long *);

long spin_val = 0;
void *child(void* dummy)
{
    while(1) {
       pthread_mutex_lock(&lock);
	sum ++;
	if(sum%(MAX/10)==0) {
         time_t t = time(NULL);
       struct tm tm = *localtime(&t);
       printf("progress is %f at now: %d-%d-%d %d:%d:%d\n",100.0*(float)sum/MAX , tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
        }
       pthread_mutex_unlock(&lock); 
	if(sum >= MAX)
           break;
    }
    return NULL;   
}

int main(int argc, char * argv[])
{
    int idx;
    double st, ed;
    pthread_t * pid;
    if (argc == 2) {
        threads=atoi(argv[1]);      
    }
    if (threads <= 0) threads=36;

    pid = (pthread_t *)malloc(sizeof(pthread_t) * threads);

    st = time_usec();
    for(idx = 0; idx < threads; idx++) {
        pthread_create(&pid[idx], NULL, child, NULL);
    }
 
    for(idx = 0; idx < threads; idx++) {
        pthread_join(pid[idx], NULL);
    }
    ed = time_usec();
    
    printf("time elapsed: %.6f(us), sum = %lu\n", ed - st, sum);

    free(pid);
    return 0;
}

