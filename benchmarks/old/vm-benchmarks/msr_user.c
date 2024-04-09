#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <time.h>

#include "tsc.h"

#define N 10000
uint64_t cycles[N];

int main(int argc, char *argv[])
{
    if (argc < 2) {
        printf("Usage: %s <msr index> \n", argv[0]);
        return 0;
    }

    uint32_t msr_index = atoi(argv[1]);
    uint64_t msr_value;
    int i, r, fd;
    char msr_file_path[32];
    struct timespec start, end;

    sprintf(msr_file_path, "/dev/cpu/0/msr");
    fd = open(msr_file_path, O_RDONLY);
    if (fd < 0) {
    	fprintf(stderr, "Error opening %s: %s\n", msr_file_path, strerror(errno));
       	return 1;
    }


    memset(cycles, 0, N);
    for (i = 0; i < 10; i++) {
         r = pread(fd, &msr_value, sizeof(msr_value), msr_index); 
#if 1
        if (r != sizeof(msr_value)) {
            fprintf(stderr, "Error reading MSR 0x%X: %s\n", msr_index, strerror(errno));
            close(fd);
            return 1;
        }
	//if(i == 0)
        //    printf("MSR 0x%X: 0x%016lX\n", msr_index, msr_value);
#endif
    }

    for (i = 0; i < N; i++) {
        uint64_t start = __tsc_start();
        pread(fd, &msr_value, sizeof(msr_value), msr_index); 
        uint64_t end = __tsc_end();
        cycles[i] = end - start;
    }

    for (i = 0; i < N; i++) {
        printf("%lu\n", cycles[i]);
    }

    clock_gettime(CLOCK_BOOTTIME, &start);
    for (i = 0; i < N; i++) {
        pread(fd, &msr_value, sizeof(msr_value), msr_index); 
    }
    clock_gettime(CLOCK_BOOTTIME, &end);

    unsigned long long diff = 1000000000L * (end.tv_sec - start.tv_sec) + end.tv_nsec - start.tv_nsec;
    printf("%u, %llu, %llu\n", N, diff, diff/N);



    close(fd);
    return 0;
 }

