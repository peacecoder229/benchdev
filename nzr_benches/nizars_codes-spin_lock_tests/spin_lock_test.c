#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <math.h>
#include <unistd.h>
#include <sys/time.h>

#define _GNU_SOURCE
#include <sched.h>  // sched_setaffinity
#include <errno.h>
#define time_usec() ({struct timeval tp; gettimeofday(&tp, 0); tp.tv_sec * 1.e6 + tp. tv_usec;})

int threads=36;

unsigned long long sum = 0;

unsigned long long MAX = 0xFFFFFF;
//unsigned long long MAX = 0xFFFFFF;

void spin_lock(long *);
void spin_unlock(long *);

long spin_val = 0;

struct thread_info {
 
    pthread_t thread_id; // ID returned by pthread_create()
    int core_id; // Core ID we want this pthread to set its affinity to
  };
void *child(void* arg)
{
	// args contains the the core id which I am using to set cpu arguments
	struct thread_info *thread_info = arg; 
  	const pthread_t pid = pthread_self();
  	const int core_id = thread_info->core_id;
    	// cpu_set_t: This data set is a bitset where each bit represents a CPU.
	cpu_set_t cpuset;
	// CPU_ZERO: This macro initializes the CPU set set to be the empty set.
	CPU_ZERO(&cpuset);
	// CPU_SET: This macro adds cpu to the CPU set set.
	CPU_SET(core_id, &cpuset);
	// pthread_setaffinity_np: The pthread_setaffinity_np() function sets the CPU affinity mask of the thread thread to the CPU set pointed to by cpuset. If the call is successful, and the thread is not currently running on one of the CPUs in cpuset, then it is migrated to one of those CPUs.
        const int set_result = pthread_setaffinity_np(pid, sizeof(cpu_set_t), &cpuset);
	while(1) {
       		spin_lock(&spin_val);
       		sum ++;
		if(sum%(MAX/10)==0){
        		time_t t = time(NULL);
       			struct tm tm = *localtime(&t);
       			printf("progress is %f%% at now: %d-%d-%d %d:%d:%d\n",100.0*(float)sum/MAX , tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec);
        	}
       spin_unlock(&spin_val);
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
   /// Initialize thread creation attributes
       pthread_attr_t attr;
       const int attr_init_result = pthread_attr_init(&attr);
    pid = (pthread_t *)malloc(sizeof(pthread_t) * threads);
      struct thread_info *thread_info = calloc(threads, sizeof(struct thread_info));
    st = time_usec();
    for(idx = 0; idx < threads; idx++) {
	
    	int offset =0;
	if (idx <28){
		offset =0;}
	else if(idx <56){
		offset=56;}
	else if(idx < 84){
		offset = 28;}
	else if(idx<112 ){
		offset = 84;
	}
	int thread_id=offset+idx%28;
	
        printf("setting thread %d into core %d\n",idx,thread_id);	
        
        thread_info[idx].core_id = thread_id;
	pthread_create(&pid[idx], &attr, child, &thread_info[idx]);
    }
 
    for(idx = 0; idx < threads; idx++) {
        pthread_join(pid[idx], NULL);
    }
    ed = time_usec();
    
    printf("time elapsed: %.6f(us), sum = %lu\n", ed - st, sum);

    free(pid);
    return 0;
}

