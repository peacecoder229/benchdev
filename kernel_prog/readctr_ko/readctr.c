#include <linux/module.h>
#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/cdev.h>
#include <linux/fs.h>
#include <linux/mm.h>
#include <linux/uaccess.h>
//start of kthread-related includes:
#include <linux/init.h>
#include <linux/sched.h>
#include <linux/threads.h>
#include <linux/bitmap.h>
#include <linux/cpumask.h>
#include <linux/kthread.h>	//kthreads for "kthread_create_on_cpu" 
#include <linux/types.h>
#include <linux/delay.h>
//end
#include <linux/unistd.h>

#include "readctr.h"

//basic iteration count for all tests:
#define ITER 500
#define INTERVAL 1000

//You have these memorized at this point, right? ;)
#define IA32_PQR_ASSOC 0xC8F
#define IA32_QM_EVTSEL 0xC8D
#define IA32_QM_CTR 0xC8E
#define IA32_TIME_STAMP_COUNTER 0x10

#define IA32_PERF_STATUS 0x198
#define IA32_PERF_CTL 0x199
#define PMC_CTR 0x0
#define PREF_CTL 0x1A4 

//IA32_PQR_ASSOC contents to set RMID=0, CLOS=0:
#define PQRVAL_BOTH 0x0
#define PQRVAL_CLOS 0x1
#define PQRVAL_RMID 0x2
#define PQRVAL_STATIC 0x3
//IA32_QM_EVTSEL contents to retrieve CMT occupancy for RMID 0:
#define EVTSELVAL 0x1

#define USE_KTHREADS 
#define KTHREAD_NODE 0
#define KTHREAD_CPU 0
#define EVESEL 0x01C0
//#define PERF_EV_SEL = ((evsel)|=(1<<22))

static inline unsigned long wrmsr_asm(unsigned long addr, unsigned long val, int iter){
        unsigned long lo=0xFFFFFFFF&val;
        unsigned long hi=0xFFFFFFFF&(val>>32);
        asm volatile("wrmsr\n"
                : //no outputs
                : "c"(addr), "a"(lo), "d"(hi) );
        return 0;
}


// wrmsr spec
// writes teh content of EDX(hi):EAX(lo) into 64 bit msr specified in ECX 
// CPUs supporting 64 bits and hence RDX and RAX ..higher 32 bits are ignored. This is for backward compatiblity



static int __init rdctr_init(void){
	int ret;
	int node;
	unsigned int thread; 
	struct task_struct *ts;
       	ret = 0;
	//long retval = 0;
	printk("rdctr: Initializing kernel module...\n");	
	
	#ifdef USE_KTHREADS
		node = KTHREAD_NODE;
	        thread = KTHREAD_CPU;
		ts = kthread_create_on_node((void *)&run_test,NULL,node,"run_test"); 

		if(!IS_ERR(ts)){
			kthread_bind(ts,thread);
			wake_up_process(ts);
			printk("rdctr: Successfully created thread on node %i, thread %u.\n",node,thread);
		}
		
		pid_t pid;
		pid=ts->pid;
		//cpumask_t mask = ts->cpus_allowed; 
		unsigned int cpu = task_cpu(ts);
		//sched_getaffinity(pid,&mask);	
		printk("rdctr: Kernel says we are allowde to run on CPU: %u.\n",cpu);
	#else
		retval = run_test();
	#endif
	
	printk("rdctr: Kernel module init completed.\n");	
	return ret;
}

static void __exit rdctr_exit(void){
	printk("rdctr: Exiting kernel module\n");
	return;
}


static int program_ctr(void){
    print_sizes();
    //
    unsigned long val_0 = 0x3003C;
    unsigned long evval_0 = ((val_0)|=(1<<22));
    //gen counter programmed to count ctr0 unhalted_cycles.core
    wrmsr_asm(0X186,evval_0,1);
    //rdmsr_ser_bmk(0X186,1);


    unsigned long val_1 = 0x300C0;
    unsigned long evval_1 = ((val_1)|=(1<<22));
    //gen counter programmed to count ctr1 instruction_retired
    wrmsr_asm(0X187,evval_1,1);
    //rdmsr_ser_bmk(0X187,1);


    unsigned long val_2 = 0x3412E;
    unsigned long evval_2 = ((val_2)|=(1<<22));
    //gen counter programmed to count Core-originated cacheable demand requests missed L3
     wrmsr_asm(0X188,evval_2,1);
    //rdmsr_ser_bmk(0X188,1);
    return 0;
}

static int read_ctr(unsigned long interval, int iter){
    unsigned long ctr_0=0, ctr_1=1, ctr_2=2; 
        
    register unsigned long eax1, edx1;
    register unsigned long eax2, edx2;
    register unsigned long lo_0s, lo_1s, lo_2s;
    register unsigned long hi_0s, hi_1s, hi_2s;
    register unsigned long lo_0e, lo_1e, lo_2e;
    register unsigned long hi_0e, hi_1e, hi_2e;
    int i=0;
    for (i=0; i<iter; i++)
    { 
        asm volatile("rdtsc; lfence; \n"
                : "=a"(eax1), "=d"(edx1)
                :
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_0s), "=d"(hi_0s)
                : "c"(ctr_0)
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_1s), "=d"(hi_1s)
                : "c"(ctr_1)
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_2s), "=d"(hi_2s)
                : "c"(ctr_2)
                :
                );
        //ndelay(interval);
        asm volatile("lfence; rdtsc;  \n"
                : "=a"(eax2), "=d"(edx2)
                :
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_0e), "=d"(hi_0e)
                : "c"(ctr_0)
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_1e), "=d"(hi_1e)
                : "c"(ctr_1)
                :
                );
        asm volatile("rdpmc\n"
                : "=a"(lo_2e), "=d"(hi_2e)
                : "c"(ctr_2)
                :
                );

        unsigned long long tsc_diff=0, diff_0=0, diff_1=0, diff_2=0;
        tsc_diff = ((edx2<<32)|eax2) - ((edx1<<32)|eax1);
        diff_0 = ((hi_0e<<32)|lo_0e) - ((hi_0s<<32)|lo_0s);
        diff_1 = ((hi_1e<<32)|lo_1e) - ((hi_1s<<32)|lo_1s);
        diff_2 = ((hi_2e<<32)|lo_2e) - ((hi_2s<<32)|lo_2s);

        printk("iter: %d\n",i);
        printk("ctr: tsc iter %d diff = %lu\n",i,tsc_diff);
        printk("Unhalted Core Cycles: 0x%x iter %d diff = %lu\n",(unsigned int)ctr_0,i,diff_0);
        printk("Instruction Retired: 0x%x iter %d diff = %lu\n",(unsigned int)ctr_1,i,diff_1);
        printk("LLC Misses: 0x%x iter %d diff = %lu\n",(unsigned int)ctr_2,i,diff_2);
        //printk("utilizaion=%0.4f ipc=%0.4f l3_mpki=%0.4f \n ", (double)diff_0/tsc_diff, (double)diff_1/diff_0, 1000.0*(double)diff_2/diff_1);
    }
    return 0;
}



static int run_test(void){
	//Run several types of tests:
	print_sizes();
        unsigned long retval_0, retval_1;
        retval_0 = program_ctr();
        retval_1 = read_ctr(INTERVAL, ITER);

        #ifdef USE_KTHREADS
                do_exit(0);     //from thread
        #else
                return 0;       //just in case
        #endif

}

static void print_sizes(void){
	printk("Printing sizes:\n");
	printk("sizeof int: %lu\n",sizeof(int));
	printk("sizeof long: %lu\n",sizeof(long));
	printk("sizeof long long %lu\n",sizeof(long long));
	printk("sizeof unsigned int: %lu\n",sizeof(unsigned int));
	printk("sizeof unsigned long: %lu\n",sizeof(unsigned long));
	printk("sizeof unsigned long long %lu\n",sizeof(unsigned long long));
	return;
}


module_init(rdctr_init);
module_exit(rdctr_exit);

//MODULE_LICENSE("BSD");
MODULE_LICENSE("GPL");

