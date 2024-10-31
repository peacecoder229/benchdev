
#include <linux/module.h>
#include <linux/kernel.h>

//Below are the perfeventsel bit settings for thej respective events
//which are written into the eventsel CTR defined by MSR 0x186 for general CTR0..and so on

#define EVENT_UNHALTED_CYCELE 0x47013C
#define EVENT_INSTRUCTION 0x4700C0
#define EVENT_LLC_MISSES 0x47412E
#define EVENT_LLC_REF 0x474F2E

#define MONCTR_0 0x186
#define MONCTR_1 0x187
#define MONCTR_2 0x188
#define MONCTR_3 0x189

// #define GLOBAL_CTRL 0x38F
// #define GLOBAL_OVF_CTRL 0x390
// #define GLOBAL_CHECK_STATUE 0x38E

//assembly lang code for setting CR4 bit 8 to 1

void CR4_enablePMC(void)
{
        asm volatile(
            "push %rax\n\t"
            "mov %cr4,%rax\n\t"
            "or $(1<<8),%rax\n\t"
            "mov %rax,%cr4\n\t"
            "pop %rax\n\t");
}

void init_module_smp(void *param)
{
        CR4_enablePMC();      
}

void cleanup_module_smp(void *param)
{
}

static inline void wrmsr_asm(unsigned long addr, unsigned long val)
{
        unsigned long lo = 0xFFFFFFFF & val;
        unsigned long hi = 0xFFFFFFFF & (val >> 32);
        asm volatile("wrmsr\n"
                     : //no outputs
                     : "c"(addr), "a"(lo), "d"(hi));
        printk("Counter perevfsel MSR %lx is set with %lx", addr, val);
}

void program_ctr(void *p)
{
        // 0 fill all ctrllers 
        // wrmsr_asm(GLOBAL_OVF_CTRL, 0x00070000000F);
        // wrmsr_asm(GLOBAL_CTRL, 0x0000E00F);

        // Declair 3 reguestors
        wrmsr_asm(MONCTR_0, EVENT_UNHALTED_CYCELE);
        wrmsr_asm(MONCTR_1, EVENT_INSTRUCTION);
        wrmsr_asm(MONCTR_2, EVENT_LLC_MISSES);
        wrmsr_asm(MONCTR_3, EVENT_LLC_REF);
}

int init_module(void)
{
        printk("==Initial light monitor module==\n");
        printk("run command: 'echo1 > /sys/devices/cpu/rdpmc' to keep rdpmc working\n ");

        // set CR4 to enable RDPMC for user space
        on_each_cpu(init_module_smp, NULL, 1);
        // set controllers for RDPMC
        on_each_cpu(program_ctr, NULL, 1);

        return 0;
}

void cleanup_module(void)
{
        on_each_cpu(cleanup_module_smp, NULL, 1);
        printk("==Cleanup module light monitor module==");
}
