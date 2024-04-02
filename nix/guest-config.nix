{
  pkgs
  , lib
  , selfpkgs
  , ...
}:
let
  kernelPackages = pkgs.linuxPackages_6_6;
in
{
  imports =
  [
    # ({ config, ...}: {})
    # ./modules/encrypt.nix
    # ./modules/fio-runner.nix
  ];

  services.sshd.enable = true;
  programs.direnv.enable = true;

  networking.hostName = "native-guest";
  networking.firewall.enable = false;
  # networking.firewall.allowedTCPPorts = [22];

  users.users.root.password = "password";
  services.openssh.settings.PermitRootLogin = lib.mkDefault "yes";
  users.users.root.openssh.authorizedKeys.keys =
  [
    (builtins.readFile ./ssh_key.pub)
  ];
  services.getty.autologinUser = lib.mkDefault "root";
  time.timeZone = "Europe/Berlin";
  i18n.defaultLocale = "en_US.UTF-8";
  console = {
    font = "Lat2-Terminus16";
    keyMap = "us";
  };
  system.stateVersion = "23.11";

  nix.extraOptions =
  ''
    experimental-features = nix-command flakes
  '';
  nix.package = pkgs.nixFlakes;
  environment.systemPackages = with pkgs;
  [
    git
    fio
    cryptsetup
    trace-cmd
    bpftrace
    blktrace
    vim
    tmux
    fzf
    kernelPackages.perf
    xterm # for `resize`, if vim messes up serial console size
  ] ++
  ( with selfpkgs;
    [
      bm-cpuid
    ]
  );

  boot.kernelPackages = kernelPackages;
  boot.kernelPatches = [
    {
      name = "enable-sev-snp";
      patch = null;
      # based on a build script (commonsh) in the AMDESE/AMDSEV repo
      extraConfig = ''
          EXPERT y
          AMD_MEM_ENCRYPT y
          AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT n
          KVM_AMD_SEV y
          CRYPTO_DEV_CCP_DD m
          SEV_GUEST m
          X86_CPUID m
      '';
    }
  ];

  # XXX: for some reason, the AMD GPU driver failed to link with the following configuratios
  # boot.kernelPatches = [
  #   {
  #     name = "enable-sev-snp";
  #     patch = null;
  #     # based on a build script (commonsh) in the AMDESE/AMDSEV repo
  #     extraConfig = ''
  #       EXPERT y
  #       DEBUG_INFO y
  #       DEBUG_INFO_REDUCED y
  #       AMD_MEM_ENCRYPT y
  #       AMD_MEM_ENCRYPT_ACTIVE_BY_DEFAULT n
  #       KVM_AMD_SEV y
  #       SYSTEM_TRUSTED_KEYS n
  #       IOMMU_DEFAULT_PASSTHROUGH n
  #       PREEMPT_DYNAMIC n
  #       CGROUP_MISC y
  #       UBSAN n
  #
  #       ## MLX4_EN n # disoption conflicts "MLX4_EN m"
  #       #MLX4_DEBUG y
  #       #MLX4_CORE_GEN2 y
  #       #MLX5_FPGA y
  #       #MLX5_CORE_EN y
  #       #MLX5_EN_ARFS y
  #       #MLX5_EN_RXNFC y
  #       #MLX5_MPFS y
  #       #MLX5_ESWITCH y
  #       #MLX5_BRIDGE y
  #       #MLX5_CORE_IPOIB y
  #       #MLX5_SW_STEERING y
  #       #MLXSW_CORE_HWMON y
  #       #MLXSW_CORE_THERMAL y
  #
  #       # modules
  #       CRYPTO_DEV_CCP_DD m
  #       SEV_GUEST m
  #       X86_CPUID m
  #
  #       #MLX4_EN m
  #       #MLX4_CORE m
  #       #MLX5_CORE m
  #       #MLXSW_CORE m
  #       #MLXSW_PCI m
  #       #MLXSW_I2C m
  #       #MLXSW_SPECTRUM m
  #       #MLXSW_MINIMAL m
  #       #MLXFW m
  #
  #       # XXX: these are defined in the build script
  #       #      but result in "error: unsed option"
  #       # DEBUG_PREEMPT n
  #       # MLX4_EN_DCB y
  #       # MLX5_CLS_ACT y
  #       # MLX5_CORE_EN_DCB y
  #       # MLX5_TC_CT y
  #       # MLX5_TC_SAMPLE y
  #       # MLXSW_SPECTRUM_DCB y
  #       # MODULE_SIG_KEY n
  #       # SYSTEM_REVOCATION_KEYS n
  #       # PREEMPT_COUNT n
  #       # PREEMPTION n
  #     '';
  #   }
  # ];

  boot.kernelParams = [
                        "virtio_blk.cvm_io_driver_name=virtio2"
                        "virtio_blk.poll_queues=4"
                        "virtio_scsi.virtscsi_poll_queues=4"
                        # "swiotlb=force"
                      ];

}
