#include <stdio.h>
#include <sys/time.h>
int main(int argc, char *argv[]) {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  printf("[Dd] the time now: %lu ms\n", tv.tv_sec * 1000 + tv.tv_usec / 1000);
}
