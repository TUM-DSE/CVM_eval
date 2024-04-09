#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>

#include "tsc.h"

static inline void cpuid(uint64_t rax, uint64_t rcx){
    uint64_t rbx, rdx;
    asm volatile( "cpuid\n\t"
        : "=a"(rax), "=b"(rbx), "=c"(rcx), "=d"(rdx)
        : "a"(rax), "c"(rcx)
        : );
}

#define N 10000
uint64_t cycles[N];
int main(int argc, char* argv[]) {

    if (argc < 3) {
        printf("Usage: %s <rax> <rcx>\n", argv[0]);
        return 0;
    }

    uint64_t rax = atoi(argv[1]);
    uint64_t rcx = atoi(argv[2]);
    
    struct timespec start, end;
    int i;

    // warmup
    for (i = 0; i < N; i++) {
        cpuid(rax, rcx);
        cycles[i] = 0;
    }

    // measure cycles
    for (i = 0; i < N; i++) {
        uint64_t start = __tsc_start();
        cpuid(rax, rcx);
        uint64_t end = __tsc_end();
        cycles[i] = end - start;
    }

    for (i=0; i<N; i++) {
        printf("%lu\n", cycles[i]);
    }

    // measure total time
    clock_gettime(CLOCK_BOOTTIME, &start);
    for (i = 0; i < N; i++) {
        cpuid(rax, rcx);
    }
    clock_gettime(CLOCK_BOOTTIME, &end);

    unsigned long long diff = 1000000000L * (end.tv_sec - start.tv_sec) + end.tv_nsec - start.tv_nsec;
    printf("%u, %llu, %llu\n", N, diff, diff/N);

    return 0;
}
