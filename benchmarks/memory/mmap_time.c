#include <stdio.h>
#include <sys/mman.h>
#include <time.h>

// measure the time taken to allocate 32GB of memory using mmap

int main() {
  struct timespec a, b;
  clock_gettime(CLOCK_REALTIME, &a);
  char *p = mmap(NULL, 32ULL * 1024 * 1024 * 1024, PROT_READ | PROT_WRITE,
                 MAP_POPULATE | MAP_SHARED | MAP_ANONYMOUS, -1, 0);
  clock_gettime(CLOCK_REALTIME, &b);
  printf("%.6lf\n",
         (b.tv_sec + b.tv_nsec * 1e-9) - (a.tv_sec + a.tv_nsec * 1e-9));
  return 0;
}
