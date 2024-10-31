
static long long  read_tsc(void){

    register unsigned long eax1, edx1;
    asm volatile("rdtsc; lfence; \n"
            : "=a"(eax1), "=d"(edx1)
            :
            :
            );
    unsigned long long tsc_output = (edx1<<32)|eax1;
    printf("%lld, ", tsc_output);
    //printf("%ld, %ld", edx1, eax1);
    return ((edx1<<32)|eax1);
}
