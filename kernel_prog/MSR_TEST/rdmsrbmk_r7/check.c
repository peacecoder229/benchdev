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
//end
#include <linux/unistd.h>

#include "rdmsrbmk.h"

//basic iteration count for all tests:
#define ITER 1000

//You have these memorized at this point, right? ;)
#define IA32_PQR_ASSOC 0xC8F
#define IA32_QM_EVTSEL 0xC8D
#define IA32_QM_CTR 0xC8E
#define IA32_TIME_STAMP_COUNTER 0x10

#define IA32_PERF_STATUS 0x198
#define IA32_PERF_CTL 0x199

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


static inline unsigned long rdtsc_ser_bmk(int iter){
        unsigned long eax1, eax2;
        asm volatile("rdtsc; lfence\n"
                : "=a"(eax1)
                :
		: "edx"
                );
	asm volatile("lfence; rdtsc; \n"
                : "=a"(eax2)
                :
		: "edx"
                );
	printk("rdmsrbmk: Serialized: iter %i diff = %lu\n",iter,(unsigned long)(eax2-eax1));
	//diff=((unsigned long)((edx2<<32)|eax2))-((unsigned long)((edx1<<32)|eax1));
	return 0; //(unsigned long)(eax2-eax1);
}


static unsigned long rdmsr_ser_bmk(unsigned long addr, int iter){
        register unsigned long eax1, edx1; 
        register unsigned long eax2, edx2; 
	//unsigned long ecx; 
        register unsigned long lo=0, hi=0;
	asm volatile("rdtsc; lfence; \n"
                : "=a"(eax1), "=d"(edx1)
                :
		: 
                );
	asm volatile("rdmsr\n"
                : "=a"(lo), "=d"(hi)
                : "c"(addr)
                : 
		);
        asm volatile("lfence; rdtsc;  \n"
                : "=a"(eax2), "=d"(edx2)
                :
		: 
                );
	printk("rdmsrbmk: run_rdmsr_test: 0x%x=0x%16.16lx: iter %d diff = %lu\n",(unsigned int)addr,(unsigned long)((hi<<32)|lo),iter,((unsigned long)(eax2-eax1)));
	return 0;
}


static inline unsigned long wrmsr_ser_bmk(unsigned long addr, unsigned long val, unsigned long val2, int iter){
        unsigned long eax1, edx1;
        unsigned long eax2, edx2;
	unsigned long lo=0xFFFFFFFF&val;
	unsigned long hi=0xFFFFFFFF&(val>>32);

	//printk("rdmsrbmk: About to start run_wrmsr_test: 0x%x=0x%x: iter %d\n",(unsigned int)addr,(unsigned int)val,iter);

	asm volatile("rdtsc; lfence \n"
                : "=a"(eax1), "=d"(edx1)
                :
		: 
                );
        asm volatile("wrmsr\n"
                : //no outputs
                : "c"(addr), "a"(lo), "d"(hi) );
        asm volatile("lfence; rdtsc; lfence \n"
                : "=a"(eax2),"=d"(edx2)
                :
		: 
                );
	//printk("rdmsrbmk: run_wrmsr_test: 0x%x=0x%x: iter %d diff = %lu\n",(unsigned int)addr,(unsigned)((hi<<32)+lo),iter,((unsigned long)(eax2-eax1)));
	printk("rdmsrbmk: run_wrmsr_test(mode %lu): 0x%x=0x%16.16lx: iter %d diff = %lu\n",val2,(unsigned int)addr,(unsigned long)val,iter,((unsigned long)(eax2-eax1)));
	return 0;
}

static int __init rdmsrbmk_init(void){
	int ret;
	int node;
	unsigned int thread; 
	struct task_struct *ts;
       	ret = 0;
	//long retval = 0;
	printk("rdmsrbmk: Initializing kernel module...\n");	
	
	#ifdef USE_KTHREADS
		node = KTHREAD_NODE;
	        thread = KTHREAD_CPU;
		ts = kthread_create_on_node((void *)&run_test,NULL,node,"run_test"); 

		if(!IS_ERR(ts)){
			kthread_bind(ts,thread);
			wake_up_process(ts);
			printk("rdmskbmk: Successfully created thread on node %i, thread %u.\n",node,thread);
		}
		
		pid_t pid;
		pid=ts->pid;
		//cpumask_t mask = ts->cpus_allowed; 
		unsigned int cpu = task_cpu(ts);
		//sched_getaffinity(pid,&mask);	
		printk("rdmskbmk: Kernel says we are allowde to run on CPU: %u.\n",cpu);
	#else
		retval = run_test();
	#endif
	
	printk("rdmsrbmk: Kernel module init completed.\n");	
	return ret;
}

static int run_test(void){
	//Run several types of tests:
	print_sizes();

	//pid_t pid;
	//cpumask_t mask; 
	//sched_getaffinity(pid,&mask);	
	//printk("rdmskbmk: isched_getaffinity says we have CPU mask: 0x%x.\n",mask);
	
	//Basic tests:
	/*
 	run_tsc_test();
	run_rdmsr_test(IA32_TIME_STAMP_COUNTER);	//Timer test as a sanity-check (rdmsr vs rdtsc)
	run_rdmsr_test(IA32_PERF_CTL);
	run_wrmsr_test(IA32_PERF_CTL,0xA1B);
	run_rdmsr_test(IA32_PERF_CTL);
	run_rdmsr_test(IA32_PERF_STATUS);
	*/ 

	//The PQoS tests we actually care about:
	//1. rdtsc as a baseline (serializing version)
	run_tsc_ser_test();
	//2. read FULL IA32_PQR_ASSOC
	run_rdmsr_ser_test(IA32_PQR_ASSOC);

	//3. write FULL IA32_PQR_ASSOC (dynamic field values): 
	run_wrmsr_ser_test(IA32_PQR_ASSOC,PQRVAL_BOTH);
	//4. write ONLY CLOS FIELD of IA32_PQR_ASSOC:
	run_wrmsr_ser_test(IA32_PQR_ASSOC,PQRVAL_CLOS);
	//4. write ONLY RMID FIELD of IA32_PQR_ASSOC:
	run_wrmsr_ser_test(IA32_PQR_ASSOC,PQRVAL_RMID);
	//4. write FULL IA32_PQR_ASSOC (static field values):
	run_wrmsr_ser_test(IA32_PQR_ASSOC,PQRVAL_STATIC);
	
	//5. read IA32_QM_EVTSEL
	//run_rdmsr_ser_test(IA32_QM_EVTSEL);
	//6. write IA32_QM_EVTSEL
	//run_wrmsr_ser_test(IA32_QM_EVTSEL,EVTSELVAL);
	//7. read IA32_QM_CTR:
	//run_rdmsr_ser_test(IA32_QM_CTR);
	
	//8. read FULL IA32_PQR_ASSOC
	//run_rdmsr_ser_test(PREF_CTL);
	//9. write FULL IA32_PQR_ASSOC (dynamic field values): 
	//run_wrmsr_ser_test(PREF_CTL,0x0);
	
	//10. read FULL CAT MASK for CLOS[0]:
	//run_rdmsr_ser_test(0xC90);
	//11. write FULL CAT MASK for CLOS[0]:
	//run_wrmsr_ser_test(0xC90,0x7FF); //SKX
	//run_wrmsr_ser_test(0xC90,0xFFFFF); //BDX
	
	// SKX PRODUCTION: 
	//12. read FULL MBA CLOS[0] throttling val:
	//run_rdmsr_ser_test(0xD50);
	//13. write FULL MBA CLOS[0] throttling val:
	//run_wrmsr_ser_test(0xD50,0x0);
	
	// BDX TEST PATCH: 
	//12. read FULL MBA CLOS[0] throttling val:
	run_rdmsr_ser_test(0xD70);
	//13. write FULL MBA CLOS[0] throttling val:
	run_wrmsr_ser_test(0xD70,0x0);
	
	
	
	#ifdef USE_KTHREADS
		do_exit(0);	//from thread
	#else
		return 0;	//just in case
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

static void run_tsc_ser_test(void){
        //unsigned long res[ITER];	//note: It seems that int=4, long=8, long long = 8. 
        int idx=0;

	printk("rdmsrbmk: Running tsc test...\n");

	for(idx=0; idx<ITER; ++idx){
        	rdtsc_ser_bmk(idx);
        }

	printk("rdmsrbmk: Done.\n");
	return;
}


static void run_wrmsr_ser_test(unsigned long addr, unsigned long val){
        unsigned long idx;
	unsigned long val2;
	val2 =  val;
	idx = 0;
	
	printk("rdmsrbmk: Running run_wrmsr_test for 0x%x = 0x%x...\n",(unsigned int)addr,(unsigned int)val);	
	if(addr == IA32_PQR_ASSOC && val == PQRVAL_BOTH){
		for(idx=0; idx<ITER; ++idx){
			val2 = val;
		        val2 |= (unsigned long)((idx % 8) << 32);  //use bottom 7 CLOS
			val2 |= (unsigned long)(idx % 101);  //use bottom 100 RMIDs
	                wrmsr_ser_bmk(addr,val2,val,idx);
	        }
	}else if(addr == IA32_PQR_ASSOC && val == PQRVAL_CLOS){
		for(idx=0; idx<ITER; ++idx){
			val2 = val | (unsigned long)((idx % 8) << 32);  //use bottom 7 CLOS
	                wrmsr_ser_bmk(addr,val2,val,idx);
	        }
	}else if(addr == IA32_PQR_ASSOC && val == PQRVAL_RMID){
		for(idx=0; idx<ITER; ++idx){
			val2 = val | (idx % 101);  //use bottom 100 RMIDs
	                wrmsr_ser_bmk(addr,val2,val,idx);
	        }
	}else if(addr == IA32_PQR_ASSOC && val == PQRVAL_STATIC){
		for(idx=0; idx<ITER; ++idx){
	                wrmsr_ser_bmk(addr,val,val,idx);
	        }
	}else
		for(idx=0; idx<ITER; ++idx){
	                wrmsr_ser_bmk(addr,val,val,idx);
	        }

	printk("rdmsrbmk: run_wrmsr_test completed.\n");
	return;
}

static void run_rdmsr_ser_test(unsigned long addr){
        int idx = 0;
	printk("rdmsrbmk: Running run_rdmsr_test for 0x%x...\n",(unsigned int)addr);

	for(idx=0; idx<ITER; ++idx){
                rdmsr_ser_bmk(addr,idx);
        }

	printk("rdmsrbmk: run_rdmsr_test completed.\n");
	return;

}


static void __exit rdmsrbmk_exit(void){
	printk("rdmsrbmk: Exiting kernel module\n");
	return;
}

module_init(rdmsrbmk_init);
module_exit(rdmsrbmk_exit);

//MODULE_LICENSE("BSD");
MODULE_LICENSE("GPL");

