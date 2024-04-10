{ pkgs, lib, modulesPath, ... }: {
  boot.kernelPatches = [{
    name = "enable-sev-snp";
    patch = null;
    extraConfig = ''
      EXPERT y
      AMD_MEM_ENCRYPT y
      AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT n
      KVM_AMD_SEV y
      CRYPTO_DEV_CCP_DD m
      SEV_GUEST m
      X86_CPUID m
    '';
  }];
}
