
static int __init rdmsrbmk_init(void);
static void __exit rdmsrbmk_exit(void);

static int run_test(void);	//calls the other tests below
static void print_sizes(void);
static void run_tsc_ser_test(void);
static void run_wrmsr_ser_test(unsigned long addr, unsigned long val);
static void run_rdmsr_ser_test(unsigned long addr);

