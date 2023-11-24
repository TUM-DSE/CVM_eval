## CPUID
- `cpuid.c`
   - Measure CPUID latency
   - `gcc -o cpuid cpuid.c`
- Intel
    - CPUID that causes `#VE`
        - https://intel.github.io/ccc-linux-guest-hardening-docs/security-spec.html#cpuid
        - example
            - `0x2`: Cache info
            - `0x16`: TCS info
    - CPUID that TDX module handles
        - example
            - `0x0`: Vendor info
            - `0x15`: TCS info (trusted)

## MSR
- Note: Only ring0 can access MSRs
- `msr_user.c`
    - Measure MSR latency using `/dev/cpu/*/msr`

## Hypercall
- NOTE
    - Hypercalls result in `#GP` on the host.
    - It seems KVM return `#GP` if the guest executes `vmcall` instruction in ring3.

## TODO
- PIO
- MMIO
- TDCall (TDX)
- ASP MMIO (SEV-SNP)

