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
  }
    {
      name = "sev_ghcb";
      patch = ./patches/linux_sev_export_ghcb_func.patch;
    }];
}
