{ pkgs, lib, modulesPath, ... }: {
  boot.kernelPatches = [
    {
      name = "enable-tdx";
      patch = null;
      extraConfig = ''
        INTEL_TDX_GUEST y
        TDX_GUEST_DRIVER y
      '';
    }
    {
      name = "tdx-allow-user-io";
      patch = ./patches/linux_tdx_allow_user_io.patch;
    }
    {
      name = "tdx-handle-vmcall-ve";
      patch = ./patches/linux_tdx_handle_vmcall_ve.patch;
    }
  ];
}
