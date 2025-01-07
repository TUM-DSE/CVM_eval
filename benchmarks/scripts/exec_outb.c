#include <stdio.h>
#include <stdlib.h>
#include <sys/io.h>

#define BENCHMARK_PORT 0xF4

int my_outb(int value) {

  if (ioperm(BENCHMARK_PORT, 1, 1)) {
    printf("Failed to get access to the benchmark port\n");
    return -1;
  }
  outb(value, BENCHMARK_PORT);
  return 0;
}

int main() {
  my_outb(248);
  return 0;
}
