{
  pkgs
  , lib
  , selfpkgs
  , ...
}:
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
    linuxPackages.perf
    xterm # for `resize`, if vim messes up serial console size
  ] ++
  ( with selfpkgs;
    [
      bm-cpuid
    ]
  );

  # kernel version
  boot.kernelPackages = pkgs.linuxKernel.packages.linux_6_6;

  # boot.extraModulePackages = [
  #   helloModule
  # ];

  # boot.kernelParams = [ "virtio_blk.cvm_io_driver_name=virtio2" ];
  boot.kernelParams = [
                        "virtio_blk.cvm_io_driver_name=virtio2"
                        "virtio_blk.poll_queues=4"
                        "virtio_scsi.virtscsi_poll_queues=4"
                        # "swiotlb=force"
                      ];

#  programs.fio-runner =
#  {
#    enable = true;
#    encrypted-run = true;
#    bounce-buffer = false;
#  };

}
