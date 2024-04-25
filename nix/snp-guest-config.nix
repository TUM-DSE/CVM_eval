{ pkgs, lib, modulesPath, ... }: {
  boot.kernelPatches = [{
    name = "enable-sev-snp";
    patch = null;
    extraConfig = ''
      AMD_MEM_ENCRYPT y
      VIRT_DRIVERS y
      SEV_GUEST m
      X86_CPUID m
    '';
  }];
}
