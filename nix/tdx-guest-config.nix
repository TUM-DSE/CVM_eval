{ pkgs, lib, modulesPath, ... }: {
  boot.kernelPatches = [{
    name = "enable-tdx";
    patch = null;
    extraConfig = ''
      INTEL_TDX_GUEST y
      TDX_GUEST_DRIVER y
    '';
  }];
}
