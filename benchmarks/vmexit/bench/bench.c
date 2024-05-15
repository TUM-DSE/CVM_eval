#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/time.h>
#include <linux/types.h>
#include <linux/version.h>

#include "tsc.h"

#define MODULE_NAME "bench"

#ifdef pr_fmt
#undef pr_fmt
#endif
#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#if 1
#define WARMUP_COUNT 1000ULL
#define BENCH_COUNT 100000ULL // 100k
#else
#define _DEBUG
#define WARMUP_COUNT 0
#define BENCH_COUNT 1
#endif

MODULE_LICENSE("GPL");

static int mode = 0;
module_param(mode, int, 0);

// define SNP or TDX for benchmarking
// #define SNP
// #define TDX

#ifdef SNP

#include <asm/sev.h>
#include <asm/svm.h>

#define IOIO_TYPE_IN 1
#define IOIO_DATA_8 BIT(4)

struct ghcb_state {
	struct ghcb *ghcb;
};

struct ghcb *__sev_get_ghcb(struct ghcb_state *state);
void __sev_put_ghcb(struct ghcb_state *state);
enum es_result sev_es_ghcb_hv_call(struct ghcb *ghcb, struct es_em_ctxt *ctxt,
				   u64 exit_code, u64 exit_info_1,
				   u64 exit_info_2);

static __always_inline void vc_ghcb_invalidate(struct ghcb *ghcb)
{
	ghcb->save.sw_exit_code = 0;
	__builtin_memset(ghcb->save.valid_bitmap, 0,
			 sizeof(ghcb->save.valid_bitmap));
}

static inline void snp_cpuid(uint64_t rax, uint64_t rcx)
{
	struct ghcb_state state;
	struct es_em_ctxt ctxt;
	unsigned long flags;
	struct ghcb *ghcb;
	int ret;

	local_irq_save(flags);

	ghcb = __sev_get_ghcb(&state);
	if (!ghcb) {
		pr_info("Failed to get ghcb\n");
		goto e_restore_irq;
	}

	vc_ghcb_invalidate(ghcb);

	// XCR0 is required to be supplied when requesting leaf 0xd
	// assert (rax != 0xd);
	ghcb_set_rax(ghcb, rax);
	ghcb_set_rcx(ghcb, rcx);

	ret = sev_es_ghcb_hv_call(ghcb, &ctxt, SVM_EXIT_CPUID, 0, 0);

	if (ret != ES_OK) {
		WARN_ONCE(1, "Failed to call sev_es_ghcb_hv_call: cpuid %lld\n",
			  rax);
		goto e_put;
	}

	if (!(ghcb_rax_is_valid(ghcb) && ghcb_rbx_is_valid(ghcb) &&
	      ghcb_rcx_is_valid(ghcb) && ghcb_rdx_is_valid(ghcb))) {
		pr_info("Invalid register values!\n");
	}

#ifdef _DEBUG
	pr_info("%s %llx: rax=%llx, rbx=%llx, rcx=%llx, rdx=%llx\n", __func__,
		rax, ghcb->save.rax, ghcb->save.rbx, ghcb->save.rcx,
		ghcb->save.rdx);
#endif

e_put:
	__sev_put_ghcb(&state);
e_restore_irq:
	local_irq_restore(flags);
}

static inline void snp_rdmsr(uint32_t msr, uint64_t *val)
{
	struct ghcb_state state;
	struct es_em_ctxt ctxt;
	unsigned long flags;
	struct ghcb *ghcb;
	int ret;

	local_irq_save(flags);

	ghcb = __sev_get_ghcb(&state);
	if (!ghcb) {
		pr_info("Failed to get ghcb\n");
		goto e_restore_irq;
	}

	vc_ghcb_invalidate(ghcb);

	u64 exit_info_1 = 0; // 0: RDMSR, 1: WRMSR
	ghcb_set_rcx(ghcb, msr);

	ret = sev_es_ghcb_hv_call(ghcb, &ctxt, SVM_EXIT_MSR, exit_info_1, 0);

	if (ret != ES_OK) {
		WARN_ONCE(
			1,
			"Failed to call sev_es_ghcb_hv_call: rdmsr %#x, ret=%d\n",
			msr, ret);
		goto e_put;
	}

	if (!(ghcb_rax_is_valid(ghcb))) {
		WARN_ONCE(1, "Invalid register values!\n");
	}

	*val = ((uint64_t)ghcb->save.rdx << 32) | ghcb->save.rax;

#ifdef _DEBUG
	pr_info("%s %x: val=%llx\n", __func__, msr, *val);
#endif

e_put:
	__sev_put_ghcb(&state);
e_restore_irq:
	local_irq_restore(flags);
}

static inline void snp_vmmcall(unsigned int nr)
{
	struct ghcb_state state;
	struct es_em_ctxt ctxt;
	unsigned long flags;
	struct ghcb *ghcb;
	int ret;

	local_irq_save(flags);

	ghcb = __sev_get_ghcb(&state);
	if (!ghcb) {
		pr_info("Failed to get ghcb\n");
		goto e_restore_irq;
	}

	vc_ghcb_invalidate(ghcb);

	ghcb_set_rax(ghcb, nr);
	ghcb_set_cpl(ghcb, 0);

	ret = sev_es_ghcb_hv_call(ghcb, &ctxt, SVM_EXIT_VMMCALL, 0, 0);

	if (ret != ES_OK) {
		WARN_ONCE(
			1,
			"Failed to call sev_es_ghcb_hv_call: vmmcall %d, ret=%d\n",
			nr, ret);
		goto e_put;
	}

	if (!(ghcb_rax_is_valid(ghcb))) {
		WARN_ONCE(1, "Invalid register values!\n");
	}

#ifdef _DEBUG
	pr_info("%s %d: ret=%d\n", __func__, nr, (int)ghcb->save.rax);
#endif

e_put:
	__sev_put_ghcb(&state);
e_restore_irq:
	local_irq_restore(flags);
}

static inline void snp_inb(uint16_t port, uint8_t *val)
{
	struct ghcb_state state;
	struct es_em_ctxt ctxt;
	unsigned long flags;
	struct ghcb *ghcb;
	int ret;

	local_irq_save(flags);

	ghcb = __sev_get_ghcb(&state);
	if (!ghcb) {
		pr_info("Failed to get ghcb\n");
		goto e_restore_irq;
	}

	vc_ghcb_invalidate(ghcb);

	u64 exit_info_1;
	exit_info_1 = (port << 16) | IOIO_TYPE_IN | IOIO_DATA_8;
	ghcb_set_rax(ghcb, 0);

	ret = sev_es_ghcb_hv_call(ghcb, &ctxt, SVM_EXIT_IOIO, exit_info_1, 0);

	if (ret != ES_OK) {
		WARN_ONCE(
			1,
			"Failed to call sev_es_ghcb_hv_call: inb %d, ret=%d\n",
			port, ret);
		goto e_put;
	}

	if (!(ghcb_rax_is_valid(ghcb))) {
		WARN_ONCE(1, "Invalid register values!\n");
	}

	*val = ghcb->save.rax & 0xff;

#ifdef _DEBUG
	pr_info("%s %d: val=%d\n", __func__, port, *val);
#endif

e_put:
	__sev_put_ghcb(&state);
e_restore_irq:
	local_irq_restore(flags);
}

#endif // SNP

#ifdef TDX

#include <asm/vmx.h>
#include <asm/tdx.h>
#include <asm/shared/tdx.h>

#if LINUX_VERSION_CODE < KERNEL_VERSION(6, 7, 0)
#define tdx_module_args tdx_hypercall_args
#endif

#define PORT_READ 0

// functions that directly call the host without #VE

static inline void tdx_cpuid(uint64_t rax, uint64_t rcx)
{
	struct tdx_module_args args = {
		.r10 = TDX_HYPERCALL_STANDARD,
		.r11 = hcall_func(EXIT_REASON_CPUID),
		.r12 = rax,
		.r12 = rcx,
	};

	__tdx_hypercall(&args);

#ifdef _DEBUG
	pr_info("%s %llx: rax=%llx, rbx=%llx, rcx=%llx, rdx=%llx\n", __func__,
		rax, args->r12, args->r13, args->r14, args->r15);
#endif
}

static inline void tdx_rdmsr(uint32_t msr, uint64_t *val)
{
	struct tdx_module_args args = {
		.r10 = TDX_HYPERCALL_STANDARD,
		.r11 = hcall_func(EXIT_REASON_MSR_READ),
		.r12 = msr,
	};

	__tdx_hypercall(&args);

	*val = args.r11;

#ifdef _DEBUG
	pr_info("%s %d: val=%llx\n", __func__, msr, *val);
#endif
}

static inline void tdx_inb(uint16_t port, uint8_t *val)
{
	int size = 1;
	struct tdx_module_args args = {
		.r10 = TDX_HYPERCALL_STANDARD,
		.r11 = hcall_func(EXIT_REASON_IO_INSTRUCTION),
		.r12 = size,
		.r13 = PORT_READ,
		.r14 = port,
	};

	__tdx_hypercall(&args);

	*val = args.r11;

#ifdef _DEBUG
	pr_info("%s %d: ret=%d\n", __func__, port, *val);
#endif
}

static inline void tdx_vmcall(unsigned int nr)
{
	// assert(nr != zero);

	struct tdx_module_args args = {
		.r10 = nr,
	};

	__tdx_hypercall(&args);

#ifdef _DEBUG
	pr_info("%s %d: ret=%d\n", __func__, nr, (int)args->r10);
#endif
}

#endif // TDX

static inline void _cpuid(uint64_t rax, uint64_t rcx)
{
	uint64_t rbx, rdx;
#ifdef _DEBUG
	uint64_t rax_orig = rax;
#endif
	asm volatile("cpuid\n\t"
		     : "=a"(rax), "=b"(rbx), "=c"(rcx), "=d"(rdx)
		     : "a"(rax), "c"(rcx)
		     :);
#ifdef _DEBUG
	pr_info("%s %llx: rax=%llx, rbx=%llx, rcx=%llx, rdx=%llx\n", __func__,
		rax_orig, rax, rbx, rcx, rdx);
#endif
}

#define DEFINE_BENCH(func)                                                                        \
	static void bench_##func(void)                                                            \
	{                                                                                         \
		uint64_t N = 0;                                                                   \
		uint64_t i = 0;                                                                   \
                                                                                                  \
		N = WARMUP_COUNT;                                                                 \
		for (i = 0; i < N; i++) {                                                         \
			func();                                                                   \
		}                                                                                 \
                                                                                                  \
		N = BENCH_COUNT;                                                                  \
		s64 start_time = ktime_get_ns();                                                  \
		uint64_t start = __tsc_start();                                                   \
		for (i = 0; i < N; i++) {                                                         \
			func();                                                                   \
		}                                                                                 \
		uint64_t end = __tsc_end();                                                       \
		s64 end_time = ktime_get_ns();                                                    \
                                                                                                  \
		uint64_t total_cycles = end - start;                                              \
		uint64_t avg_cycles = total_cycles / N;                                           \
		s64 total_time = end_time - start_time;                                           \
		s64 avg_time = total_time / N;                                                    \
		pr_info("%s, total_cycle %llu, avg_cycle %llu, total_time %lld, avg_time %lld\n", \
			#func, total_cycles, avg_cycles, total_time,                              \
			avg_time);                                                                \
	}

#define DEFINE_CPUID_FUNC(func, rax)          \
	static inline void func##_##rax(void) \
	{                                     \
		func(rax, 0);                 \
	}

DEFINE_CPUID_FUNC(_cpuid, 0)
DEFINE_CPUID_FUNC(_cpuid, 1)
DEFINE_CPUID_FUNC(_cpuid, 0x40000000)
DEFINE_BENCH(_cpuid_0)
DEFINE_BENCH(_cpuid_1)
DEFINE_BENCH(_cpuid_0x40000000)

#ifdef SNP
DEFINE_CPUID_FUNC(snp_cpuid, 0)
DEFINE_CPUID_FUNC(snp_cpuid, 1)
DEFINE_CPUID_FUNC(snp_cpuid, 0x40000000)
DEFINE_BENCH(snp_cpuid_0)
DEFINE_BENCH(snp_cpuid_1)
DEFINE_BENCH(snp_cpuid_0x40000000)
#endif

#ifdef TDX
DEFINE_CPUID_FUNC(tdx_cpuid, 0)
DEFINE_CPUID_FUNC(tdx_cpuid, 1)
DEFINE_CPUID_FUNC(tdx_cpuid, 0x40000000)
DEFINE_BENCH(tdx_cpuid_0)
DEFINE_BENCH(tdx_cpuid_1)
DEFINE_BENCH(tdx_cpuid_0x40000000)
#endif

static void bench_cpuid(void)
{
	pr_info("Benchmarking cpuid\n");

	bench__cpuid_0();
	bench__cpuid_1();
	bench__cpuid_0x40000000();

#ifdef SNP
	bench_snp_cpuid_0();
	bench_snp_cpuid_1();
	bench_snp_cpuid_0x40000000();
#endif

#ifdef TDX
	bench_tdx_cpuid_0();
	bench_tdx_cpuid_1();
	bench_tdx_cpuid_0x40000000();
#endif

	// SNP
	// - #VC handler checks cpuid page first, then call the host if needed
	// - some cpuid calls the host for fixup even if cpuid page is used (e.g., leaf 0x1, leaf 0xb)
	// TDX
	// - TDX module virtualizes many of cpuid. It injects #VE if it does not handle the cpudi
	// - Linux's #VE handler only calls the host for the hypervisor-related request (0x40000000-0x4FFFFFFF)
	// - Otherwise the handler just set zero for cpuid values

	// _cpuid(0x0, 0); // vendor
	// _cpuid(0x1, 0); // feature   (VMGEXIT in SNP for fixup)
	// _cpuid(0xb, 0); // extended topology (#VE in TDx; no tdcall, VMGEXIT in SNP for fixup)
	// _cpuid(0x15, 0); // TSC freq
	// _cpuid(0x16, 0); // TSC freq (#VE in TDX; no tdcall)
	// _cpuid(0x40000000, 0); // hypervisor (#VE in TDX with TDCALL)
}

static inline void _rdmsr(uint32_t msr, uint64_t *val)
{
	uint32_t lo, hi;
	asm volatile("rdmsr\n\t" : "=a"(lo), "=d"(hi) : "c"(msr) :);
	*val = ((uint64_t)hi << 32) | lo;
#ifdef _DEBUG
	pr_info("%s %x: val=%llx\n", __func__, msr, *val);
#endif
}

/*
static inline void _wrmsr(uint32_t msr, uint64_t val) {
    uint32_t lo = val & 0xFFFFFFFF;
    uint32_t hi = val >> 32;
    asm volatile("wrmsr\n\t" : : "c"(msr), "a"(lo), "d"(hi) :);
}
*/

#define DEFINE_RDMSR_FUNC(func, msr)          \
	static inline void func##_##msr(void) \
	{                                     \
		uint64_t val;                 \
		func(msr, &val);              \
	}

DEFINE_RDMSR_FUNC(_rdmsr, 0x1b) // IA32_APIC_BASE
DEFINE_RDMSR_FUNC(_rdmsr, 0xC0000100) // IA32_FS_BASE
DEFINE_BENCH(_rdmsr_0x1b)
DEFINE_BENCH(_rdmsr_0xC0000100)

#ifdef SNP
DEFINE_RDMSR_FUNC(snp_rdmsr, 0x1b)
DEFINE_BENCH(snp_rdmsr_0x1b)
// SEV KVM does not intercept IA32_FS_BASE (ghcb call retruns an error)
//DEFINE_RDMSR_FUNC(snp_rdmsr, 0xC0000100)
//DEFINE_BENCH(snp_rdmsr_0xC0000100)
#endif

#ifdef TDX
DEFINE_RDMSR_FUNC(tdx_rdmsr, 0x1b)
DEFINE_RDMSR_FUNC(tdx_rdmsr, 0xC0000100)
DEFINE_BENCH(tdx_rdmsr_0x1b)
DEFINE_BENCH(tdx_rdmsr_0xC0000100)
#endif

static void bench_msr(void)
{
	pr_info("Benchmarking msr\n");

	bench__rdmsr_0x1b();
	bench__rdmsr_0xC0000100();

#ifdef SNP
	bench_snp_rdmsr_0x1b();
//	bench_snp_rdmsr_0xC0000100();
#endif

#ifdef TDX
	bench_tdx_rdmsr_0x1b();
	bench_tdx_rdmsr_0xC0000100();
#endif
}

// intel: vmcall
// amd: vmmcall
#define HYPERCALL ALTERNATIVE("vmcall", "vmmcall", X86_FEATURE_VMMCALL)

// NOTE: TDX kernel does not handle vmcall in #VE handler
//       we need to patch to handle vmcall in #VE

static inline uint64_t _hypercall(unsigned int nr)
{
	uint64_t ret;
	asm volatile(HYPERCALL : "=a"(ret) : "a"(nr) : "memory");
#ifdef _DEBUG
	pr_info("%s %d: ret=%d\n", __func__, nr, (int)ret);
#endif
	return ret;
}

#define DEFINE_HYPERCALL_FUNC(func, nr)      \
	static inline void func##_##nr(void) \
	{                                    \
		func(nr);                    \
	}

// hypercall 2 (KVM_HC_FEATURES) is deprecated, kvm returns -ENOSYS (-1000)
DEFINE_HYPERCALL_FUNC(_hypercall, 2)
DEFINE_BENCH(_hypercall_2)

#ifdef SNP
DEFINE_HYPERCALL_FUNC(snp_vmmcall, 2)
DEFINE_BENCH(snp_vmmcall_2)
#endif

#ifdef TDX
DEFINE_HYPERCALL_FUNC(tdx_vmcall, 2)
DEFINE_BENCH(tdx_vmcall_2)
#endif

static void bench_hypercall(void)
{
	pr_info("Benchmarking hypercall\n");

	bench__hypercall_2();

#ifdef SNP
	bench_snp_vmmcall_2();
#endif

#ifdef TDX
	bench_tdx_vmcall_2();
#endif
}

static inline void _inb(uint16_t port, uint8_t *val)
{
	asm volatile("inb %1, %0" : "=a"(*val) : "d"(port));
#ifdef _DEBUG
	pr_info("%s %d: val=%d\n", __func__, port, *val);
#endif
}

/*
static inline void _outb(uint16_t port, uint8_t val) {
    asm volatile("outb %0, %1" : : "a"(val), "d"(port));
}
*/

#define DEFINE_INB_FUNC(func, port)            \
	static inline void func##_##port(void) \
	{                                      \
		uint8_t val = 0;               \
		func(port, &val);              \
	}

DEFINE_INB_FUNC(_inb, 0x40) // PIT
DEFINE_INB_FUNC(_inb, 0x70) // CMOS
DEFINE_INB_FUNC(_inb, 0xA0) // PIC 2
DEFINE_BENCH(_inb_0x40)
DEFINE_BENCH(_inb_0x70)
DEFINE_BENCH(_inb_0xA0)

#ifdef SNP
DEFINE_INB_FUNC(snp_inb, 0x40)
DEFINE_INB_FUNC(snp_inb, 0x70)
DEFINE_INB_FUNC(snp_inb, 0xA0)
DEFINE_BENCH(snp_inb_0x40)
DEFINE_BENCH(snp_inb_0x70)
DEFINE_BENCH(snp_inb_0xA0)
#endif

#ifdef TDX
DEFINE_INB_FUNC(tdx_inb, 0x40)
DEFINE_INB_FUNC(tdx_inb, 0x70)
DEFINE_INB_FUNC(tdx_inb, 0xA0)
DEFINE_BENCH(tdx_inb_0x40)
DEFINE_BENCH(tdx_inb_0x70)
DEFINE_BENCH(tdx_inb_0xA0)
#endif

static void bench_pio(void)
{
	pr_info("Benchmarking pio\n");

	bench__inb_0x40();
	bench__inb_0x70();
	bench__inb_0xA0();

#ifdef SNP
	bench_snp_inb_0x40();
	bench_snp_inb_0x70();
	bench_snp_inb_0xA0();
#endif

#ifdef TDX
	bench_tdx_inb_0x40();
	bench_tdx_inb_0x70();
	bench_tdx_inb_0xA0();
#endif
}

static int __init bench_init(void)
{
	pr_info("Initializing: mode=%d\n", mode);

	if (!mode || mode == 1)
		bench_cpuid();
	if (!mode || mode == 2)
		bench_msr();
	if (!mode || mode == 3)
		bench_hypercall();
	if (!mode || mode == 4)
		bench_pio();

	return 0;
}

static void __exit bench_exit(void)
{
	pr_info("Exit\n");
}

module_init(bench_init);
module_exit(bench_exit);
