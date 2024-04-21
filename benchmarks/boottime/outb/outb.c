#include <stdio.h>
#include <stdlib.h>
#include <sys/io.h>

/* Access the benchmark port from the guest user space.
 * The host can record this events using a tracer such as bpftrace.
 */

#define BENCHMARK_PORT 0xF4
#define EVENT_USER 240

int main(int argc, char *argv[]) {
    unsigned char value = EVENT_USER;
    if (argc >= 2) {
        value = (char)atoi(argv[1]);
    }

    // Requires sudo
    if (ioperm(BENCHMARK_PORT, 1, 1)) {
        printf("Failed to get access to the benchmark port\n");
        return -1;
    }
    outb(value, BENCHMARK_PORT);
    return 0;
}
