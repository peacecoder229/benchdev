#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <unistd.h>
#include <sys/time.h>
#include <atomic>
#include <iostream>
#define time_usec() ({struct timeval tp; gettimeofday(&tp, 0); tp.tv_sec * 1.e6 + tp.tv_usec;})
int threads=36;

std::atomic<long> sum(0);
long int non_atomic_sum =0;
unsigned long long MAX = 0xFFFFFF;
//unsigned long long MAX = 0xFFFFFF;

void spin_lock(long *);
void spin_unlock(long *);

long spin_val = 0;
void *child(void* dummy)
{
      while(1){
       sum++;
       non_atomic_sum++;
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
    
    printf("time elapsed: %.6f(us) non atomic sum =%lu\n", ed - st , non_atomic_sum);
    std::cout << "sum is equal to :" << sum << std::endl;
    free(pid);
    return 0;
}

