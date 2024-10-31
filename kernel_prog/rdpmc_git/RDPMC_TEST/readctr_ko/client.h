#define MONITOR_CLIENT 
#define REGUESTORS 3

typedef struct event_list{

    unsigned long long tsc;

    // 3 controllers ctrl_0~e2 for SKX cpus
    unsigned long long ctrl_0;
    unsigned long long ctrl_1;
    unsigned long long ctrl_2;
    unsigned long long ctrl_3;

} Events;


static unsigned long long rdtsc(void)
{
    // read cpu cycles
    register unsigned long eax, edx;
    asm volatile("rdtsc; lfence; \n"
                 : "=a"(eax), "=d"(edx)
                 :
                 :);
    unsigned long long tsc = 0;
    tsc = (edx << 32) | eax;

    return tsc;
}

static unsigned long long rdpmc(unsigned ctr_id)
{
    // read pmc counters by cotroller id
    unsigned int low, high;
    asm volatile("rdpmc\n"
                 : "=a"(low), "=d"(high)
                 : "c"(ctr_id)
                 :);

    unsigned long long count = 0;

    count = (low << 32) | high;

    return count;
}

unsigned long long _diff(unsigned long long before, unsigned long long after)
{
    if (before <= after)
    {

        return after - before;
    }
    else
    {
        //        printf("!!overflow: %llu, %llu\n", before, after);
        return (~(unsigned long long)0) - before + after;
    }
}

Events diff(Events *b, Events *a)
{
    Events r;

    r.tsc = _diff(b->tsc, a->tsc);
    r.ctrl_0 = _diff(b->ctrl_0, a->ctrl_0);
    r.ctrl_1 = _diff(b->ctrl_1, a->ctrl_1);
    r.ctrl_2 = _diff(b->ctrl_2, a->ctrl_2);

    return r;
}

void read_event(Events *e)
{
    e->tsc = rdtsc();

    e->ctrl_0 = rdpmc(0u);
    e->ctrl_1 = rdpmc(1u);
    e->ctrl_2 = rdpmc(2u);
    e->ctrl_3 = rdpmc(3u);
}
