#pragma once

// cf.
// https://www.intel.com/content/dam/www/public/us/en/documents/white-papers/ia-32-ia-64-benchmark-code-execution-paper.pdf
static inline uint64_t __tsc_start(void)
{
    uint32_t cycles_high, cycles_low;
    asm volatile(
        "cpuid\n\t"
        "rdtsc\n\t"
        "mov %%edx, %0\n\t"
        "mov %%eax, %1\n\t"
        : "=r"(cycles_high), "=r"(cycles_low)
        :
        : "%rax", "%rbx", "%rcx", "%rdx");
    return ((uint64_t)(cycles_high) << 32) | (uint64_t)(cycles_low);
}

static inline uint64_t __tsc_end(void)
{
    uint32_t cycles_high, cycles_low;
    asm volatile(
        "rdtscp\n\t"
        "mov %%edx, %0\n\t"
        "mov %%eax, %1\n\t"
        "cpuid\n\t"
        : "=r"(cycles_high), "=r"(cycles_low)
        :
        : "%rax", "%rbx", "%rcx", "%rdx");
    return ((uint64_t)(cycles_high) << 32) | (uint64_t)(cycles_low);
}

